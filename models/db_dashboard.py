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
