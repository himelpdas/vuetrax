import urllib, hashlib
# Set your variables here

NOT_GRID = "edit" in request.args or "view" in request.args
IS_GRID = not NOT_GRID
IS_EDIT_VIEW = any(map(lambda arg: arg in ["edit", "view"], request.args))
IS_NEW = "new" in request.args

db._common_fields += [f for f in auth.signature]

def get_gravatar(email):
    size = 100
    # construct the url
    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'s':str(size)})
    return gravatar_url

gravatar_url = None
if auth.is_logged_in():
    gravatar_url = get_gravatar(auth.user.email)

practice_form_fields = [Field('practice_name', requires=IS_NOT_EMPTY()),
        Field('providers', "list:string"),
        Field('trainer', 'list:reference auth_user',
              requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s (%(id)s)', multiple=True)),
        Field("app_tool_username"),
        Field("app_tool_password"),
        Field("survey_tool_username"),
        Field("survey_tool_password"),
        Field("is_renewal", "boolean"),
]


def _split_and_lower(s):
    l = (s or "").split()
    o = []
    for e in l:
        o.append(e.lower())
    return o


def _keywords(_set):
    print _set
    rows = _set.select()
    for record in rows:
        k = []
        for trainer in record['trainer']:

            trainer_row = db(db.auth_user.id == trainer).select().last()
            if trainer_row:
                k = k + _split_and_lower(trainer.first_name)
                k = k + _split_and_lower(trainer.last_name)

        for provider in record['providers']:
            k = k + _split_and_lower(provider)

        k = k + _split_and_lower(record['practice_name'])

        k = k + _split_and_lower(record['address'])

        db(db.practice.id == record.id).update_naive(keywords=filter(lambda e: bool(e), k))  # ignore ""  # will be recursive update


db.define_table(
    "role",
    Field("owner_id", 'reference auth_user'),
    Field("role", requires=IS_EMPTY_OR(IS_IN_SET(["admin", "trainer"]))),
)

db.define_table(
    "practice",
    # Field("physician", 'list:string'),

    Field('providers', "list:string"),

    Field("practice_specialty"),
    Field("address", default=""),
    Field("phone"),
    Field('trainer', 'list:reference auth_user', default=[],
          requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s (%(id)s)', multiple=True)),


    Field("fax"),
    Field("days", "list:string"),
    Field("hours_from", "list:string"),
    Field("hours_to", "list:string"),
    Field("credentials"),
    Field("dea_number"),
    Field("provider_license", "list:string"),
    Field("practice_email", requires=IS_EMAIL()),
    Field("practice_npi"),
    Field("provider_npi", "list:string"),
    Field("provider_dob", "list:string"),
    Field("provider_board", "list:string"),
    Field("provider_credential", "list:string"),
    Field("practice_tax_id"),
    Field("pps"),
    Field("emr"),
    Field("emr_email"),
    Field("emr_problem", "boolean"),
    Field("emr_password"),
    Field("emr_directions", "text"),
    Field("emr_teamviewer", "boolean"),
    Field("payment_is_check", "boolean"),
    Field("credit_card_first_name"),
    Field("credit_card_last_name"),
    Field("credit_card_type"),
    Field("credit_card_number"),
    Field("credit_card_expiration_year"),
    Field("credit_card_expiration_month"),
    Field("credit_card_cvv"),
    Field("credit_card_street"),
    Field("credit_card_state"),
    Field("credit_card_zip"),
    Field("comment_email"),
    Field("write_access", "list:reference auth_user"),
    Field("read_access", "list:reference auth_user"),
    Field('keywords', 'list:string', default=[]),
    Field('baa_file_name'),
    Field('baa_file_upload', 'upload'),
    #Field('dashboard_modified_on', 'datetime')
    #auth.signature,
    *practice_form_fields
)


db.define_table("uploads",
    Field("practice", db.practice),
    Field('file_name'),
    Field('file_upload', 'upload'),
)


db.practice._after_insert.append(lambda f, i: _keywords(db(db.practice.id==i)))
db.practice._after_update.append(lambda s, f: _keywords(s))

db.define_table(
    "answer",
    Field("practice", db.practice),
    Field("identifier"),
    Field("response", 'text'),
    Field("yes_no", 'boolean'),
    Field('file_name', requires=IS_NOT_EMPTY()),
    Field('file_upload', 'upload'),
    Field('meta_data', 'json'),
    auth.signature
)


db.define_table(
    "messaging",
    Field("practice", db.practice),
    Field("subject"),
    Field("message_", 'text'),
    auth.signature
)


# simple search https://groups.google.com/forum/#!topic/web2py/3aqVqRxSEt8

def _recurse_find_by_key(d, k, depth=0):
    v = []

    def recurse(d, k, v, depth=depth):
        #print d.keys(), k in d
        if k in d:
            v.append((d[k], depth))
        else:
            for i in d:
                if 'branches' in d[i]:
                    recurse(d[i]['branches'], k, v, depth+1)
    recurse(d, k, v)
    return v[0]

BUCKETS = ["imaging", "lab", "referral"]
for each in BUCKETS:
    db.define_table(
        each,
    Field("practice", db.practice),
    Field('patient',),
    Field('notes', "text"),
    Field('ordering_provider',),
    Field('appointment_date', 'date', default=request.now, requires=IS_DATE()),
    Field('destination'),
    Field('urgent', 'boolean'),
    Field('status',
          requires=IS_IN_SET(["Awaiting Response", "Order Overdue", "Results Received", "Appointment Missed By Patient",
                              "Appointment Canceled By Patient", "Appointment Canceled By Destination"],
                             sort = True),
          widget=SQLFORM.widgets.radio.widget),
    )
    db[each].is_active.readable = False
    db[each].is_active.writable = False
    db[each].id.readable = False
    db[each].practice.readable = False
    db[each].created_by.readable = True
    db[each].created_on.readable = True
    if IS_NEW:
        db[each].status.writable = False
        db[each].status.readable = False
    db[each]._enable_record_versioning()


db.define_table("hospital",
    Field("practice", db.practice),
    Field("patient"),
    Field("date_of_notification", "date"),
    Field("reason"),
    Field("appointment_date", "date"),
    Field("notes", "text"),
    Field("received_discharge_summary", "boolean"),
    Field("uploaded_to_emr", "boolean", label="Uploaded To Patient's Chart?"),
)

db["hospital"].id.readable = False
db["hospital"].practice.readable = False

db.define_table("telephone",
    Field("practice", db.practice),
    Field('urgent', 'boolean'),
    Field('after_hours', 'boolean'),
    Field("patient"),
    Field("date_of_birth", "date"),
    Field("time_of_request", "date"),
    Field("time_when_addressed", "date"),
    Field("transcript", "text"),
)

db["telephone"].id.readable = False
db["telephone"].practice.readable = False


db.define_table("secure_messaging",
    Field("practice", db.practice),
    Field('urgent', 'boolean'),
    Field('after_hours', 'boolean'),
    Field("patient"),
    Field("date_of_birth", "date"),
    Field("time_of_request", "date"),
    Field("time_when_addressed", "date"),
    Field("transcript", "text"),
)

db["secure_messaging"].id.readable = False
db["secure_messaging"].practice.readable = False

db.define_table("survey_tc",
    Field("practice", db.practice),
    Field("tc01_comment", "text",),
    Field("tc01_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc02_comment", "text", ),
    Field("tc02_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc03_comment", "text", ),
    Field("tc03_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc04_comment", "text", ),
    Field("tc04_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc05_comment", "text", ),
    Field("tc05_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc06_comment", "text", ),
    Field("tc06_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc07_comment", "text", ),
    Field("tc07_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc08_comment", "text", ),
    Field("tc08_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc09_comment", "text", ),
    Field("tc09_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
                )
db.define_table("survey_km",
    Field("practice", db.practice),
    Field("km01_comment", "text",),
    Field("km01_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km02_comment", "text", ),
    Field("km02_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km03_comment", "text", ),
    Field("km03_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km04_comment", "text", ),
    Field("km04_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km05_comment", "text", ),
    Field("km05_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km06_comment", "text", ),
    Field("km06_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km07_comment", "text", ),
    Field("km07_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km08_comment", "text", ),
    Field("km08_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km09_comment", "text", ),
    Field("km09_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km10_comment", "text", ),
    Field("km10_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km11_comment", "text", ),
    Field("km11_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km12_comment", "text", ),
    Field("km12_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km13_comment", "text", ),
    Field("km13_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km14_comment", "text", ),
    Field("km14_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km15_comment", "text", ),
    Field("km15_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km16_comment", "text", ),
    Field("km16_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km17_comment", "text", ),
    Field("km17_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km18_comment", "text", ),
    Field("km18_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km19_comment", "text", ),
    Field("km19_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km20_comment", "text", ),
    Field("km20_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km21_comment", "text", ),
    Field("km21_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km22_comment", "text", ),
    Field("km22_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km23_comment", "text", ),
    Field("km23_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km24_comment", "text", ),
    Field("km24_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km25_comment", "text", ),
    Field("km25_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km26_comment", "text", ),
    Field("km26_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km27_comment", "text", ),
    Field("km27_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km28_comment", "text", ),
    Field("km28_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    )

db.define_table("survey_ac",
    Field("practice", db.practice),
    Field("ac01_comment", "text",),
    Field("ac01_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac02_comment", "text", ),
    Field("ac02_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac03_comment", "text", ),
    Field("ac03_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac04_comment", "text", ),
    Field("ac04_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac05_comment", "text", ),
    Field("ac05_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac06_comment", "text", ),
    Field("ac06_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac07_comment", "text", ),
    Field("ac07_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac08_comment", "text", ),
    Field("ac08_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac09_comment", "text", ),
    Field("ac09_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac10_comment", "text", ),
    Field("ac10_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac11_comment", "text", ),
    Field("ac11_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac12_comment", "text", ),
    Field("ac12_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac13_comment", "text", ),
    Field("ac13_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac14_comment", "text", ),
    Field("ac14_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    )

db.define_table("survey_cm",
    Field("practice", db.practice),
    Field("cm01_comment", "text",),
    Field("cm01_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm02_comment", "text", ),
    Field("cm02_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm03_comment", "text", ),
    Field("cm03_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm04_comment", "text", ),
    Field("cm04_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm05_comment", "text", ),
    Field("cm05_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm06_comment", "text", ),
    Field("cm06_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm07_comment", "text", ),
    Field("cm07_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm08_comment", "text", ),
    Field("cm08_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm09_comment", "text", ),
    Field("cm09_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    )

db.define_table("survey_cc",
    Field("practice", db.practice),
    Field("cc01_comment", "text",),
    Field("cc01_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc02_comment", "text", ),
    Field("cc02_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc03_comment", "text", ),
    Field("cc03_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc04_comment", "text", ),
    Field("cc04_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc05_comment", "text", ),
    Field("cc05_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc06_comment", "text", ),
    Field("cc06_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc07_comment", "text", ),
    Field("cc07_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc08_comment", "text", ),
    Field("cc08_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc09_comment", "text", ),
    Field("cc09_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc10_comment", "text", ),
    Field("cc10_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc11_comment", "text", ),
    Field("cc11_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc12_comment", "text", ),
    Field("cc12_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc13_comment", "text", ),
    Field("cc13_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc14_comment", "text", ),
    Field("cc14_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc15_comment", "text", ),
    Field("cc15_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc16_comment", "text", ),
    Field("cc16_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc17_comment", "text", ),
    Field("cc17_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc18_comment", "text", ),
    Field("cc18_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc19_comment", "text", ),
    Field("cc19_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc20_comment", "text", ),
    Field("cc20_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc21_comment", "text", ),
    Field("cc21_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
                )         
db.define_table("survey_qi",
    Field("practice", db.practice),
    Field("qi01_comment", "text",),
    Field("qi01_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi02_comment", "text", ),
    Field("qi02_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi03_comment", "text", ),
    Field("qi03_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi04_comment", "text", ),
    Field("qi04_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi05_comment", "text", ),
    Field("qi05_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi06_comment", "text", ),
    Field("qi06_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi07_comment", "text", ),
    Field("qi07_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi08_comment", "text", ),
    Field("qi08_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi09_comment", "text", ),
    Field("qi09_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi10_comment", "text", ),
    Field("qi10_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi11_comment", "text", ),
    Field("qi11_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi12_comment", "text", ),
    Field("qi12_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi13_comment", "text", ),
    Field("qi13_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi14_comment", "text", ),
    Field("qi14_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi15_comment", "text", ),
    Field("qi15_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi16_comment", "text", ),
    Field("qi16_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi17_comment", "text", ),
    Field("qi17_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi18_comment", "text", ),
    Field("qi18_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi19_comment", "text", ),
    Field("qi19_response", "text", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"])))
                )
