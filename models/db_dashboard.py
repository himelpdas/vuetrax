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

db.define_table("survey",
    Field("practice", db.practice),
    Field("tc01_comment"),
    Field("tc01_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc02_comment"),
    Field("tc02_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc03_comment"),
    Field("tc03_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc04_comment"),
    Field("tc04_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc05_comment"),
    Field("tc05_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc06_comment"),
    Field("tc06_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc07_comment"),
    Field("tc07_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc08_comment"),
    Field("tc08_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("tc09_comment"),
    Field("tc09_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km01_comment"),
    Field("km01_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km02_comment"),
    Field("km02_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km03_comment"),
    Field("km03_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km04_comment"),
    Field("km04_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km05_comment"),
    Field("km05_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km06_comment"),
    Field("km06_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km07_comment"),
    Field("km07_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km08_comment"),
    Field("km08_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km09_comment"),
    Field("km09_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km10_comment"),
    Field("km10_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km11_comment"),
    Field("km11_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km12_comment"),
    Field("km12_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km13_comment"),
    Field("km13_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km14_comment"),
    Field("km14_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km15_comment"),
    Field("km15_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km16_comment"),
    Field("km16_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km17_comment"),
    Field("km17_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km18_comment"),
    Field("km18_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km19_comment"),
    Field("km19_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km20_comment"),
    Field("km20_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km21_comment"),
    Field("km21_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km22_comment"),
    Field("km22_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km23_comment"),
    Field("km23_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km24_comment"),
    Field("km24_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km25_comment"),
    Field("km25_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km26_comment"),
    Field("km26_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km27_comment"),
    Field("km27_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("km28_comment"),
    Field("km28_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac01_comment"),
    Field("ac01_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac02_comment"),
    Field("ac02_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac03_comment"),
    Field("ac03_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac04_comment"),
    Field("ac04_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac05_comment"),
    Field("ac05_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac06_comment"),
    Field("ac06_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac07_comment"),
    Field("ac07_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac08_comment"),
    Field("ac08_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac09_comment"),
    Field("ac09_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac10_comment"),
    Field("ac10_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac11_comment"),
    Field("ac11_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac12_comment"),
    Field("ac12_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac13_comment"),
    Field("ac13_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("ac14_comment"),
    Field("ac14_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm01_comment"),
    Field("cm01_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm02_comment"),
    Field("cm02_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm03_comment"),
    Field("cm03_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm04_comment"),
    Field("cm04_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm05_comment"),
    Field("cm05_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm06_comment"),
    Field("cm06_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm07_comment"),
    Field("cm07_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm08_comment"),
    Field("cm08_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cm09_comment"),
    Field("cm09_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc01_comment"),
    Field("cc01_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc02_comment"),
    Field("cc02_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc03_comment"),
    Field("cc03_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc04_comment"),
    Field("cc04_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc05_comment"),
    Field("cc05_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc06_comment"),
    Field("cc06_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc07_comment"),
    Field("cc07_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc08_comment"),
    Field("cc08_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc09_comment"),
    Field("cc09_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc10_comment"),
    Field("cc10_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc11_comment"),
    Field("cc11_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc12_comment"),
    Field("cc12_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc13_comment"),
    Field("cc13_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc14_comment"),
    Field("cc14_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc15_comment"),
    Field("cc15_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc16_comment"),
    Field("cc16_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc17_comment"),
    Field("cc17_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc18_comment"),
    Field("cc18_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc19_comment"),
    Field("cc19_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc20_comment"),
    Field("cc20_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("cc21_comment"),
    Field("cc21_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi01_comment"),
    Field("qi01_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi02_comment"),
    Field("qi02_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi03_comment"),
    Field("qi03_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi04_comment"),
    Field("qi04_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi05_comment"),
    Field("qi05_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi06_comment"),
    Field("qi06_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi07_comment"),
    Field("qi07_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi08_comment"),
    Field("qi08_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi09_comment"),
    Field("qi09_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi10_comment"),
    Field("qi10_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi11_comment"),
    Field("qi11_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi12_comment"),
    Field("qi12_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi13_comment"),
    Field("qi13_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi14_comment"),
    Field("qi14_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi15_comment"),
    Field("qi15_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi16_comment"),
    Field("qi16_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi17_comment"),
    Field("qi17_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi18_comment"),
    Field("qi18_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"]))),
    Field("qi19_comment"),
    Field("qi19_response", requires=IS_EMPTY_OR(IS_IN_SET(["Yes", "No", "N/A"])))

                )