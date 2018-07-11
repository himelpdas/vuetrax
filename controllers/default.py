# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------
# import code for encoding urls and generating md5 hashes


def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    email, password = request.vars['register_email'], request.post_vars['register_password']
    verify = request.post_vars['register_password_verify']
    if (password and verify) and (password == verify) and not auth.login_bare(email, password):
        db.auth_user.insert(
            first_name=None,
            last_name=None,
            email=email,
            password=db.auth_user.password.requires[0](password)[0]
        )
        auth.login_bare(email, password)
        redirect('home')
    # redirect
    return dict()


from collections import OrderedDict

@auth.requires_login()
def profiles():
    usrs = db(db.auth_user.id > 0).select()

    forms = OrderedDict()

    db.role.id.readable=False

    db.role.owner_id.writable=False

    _usrs = []

    for usr in usrs:

        role = db(db.role.id == usr.id).select().last()

        role_form = SQLFORM(db.role, role)

        usr_role = getattr(role, "role", None)

        def onvalidation(form, usr_id=usr.id):
            form.vars.owner_id = usr_id

        if role_form.process(formname="role_form_%s"%usr.id, onvalidation=onvalidation).accepted:
            session.flash = "Role updated!"
            _redirect_after_submit()

        user_form = [usr, None, role_form]

        if my_role == "admin":
            forms[usr.id] = user_form
            _usrs.append(usr.id)

        elif my_role == "trainer" and not usr_role == "admin" and not usr_role == "trainer":
            forms[usr.id] = user_form
            _usrs.append(usr.id)

    query = db(db.auth_user.id.belongs(_usrs))

    db.auth_user.id.represent = lambda id, row: A("Role", _href="#", **dict(
                {"_data-toggle": "modal", "_data-target": "#modal_%s" % id}))

    profiles_grid = SQLFORM.grid(query)

    return dict(usrs=usrs, my_role=my_role, profiles_grid=profiles_grid, forms=forms)


def training():
    practice_id = request.vars["practice"]
    practice = db(db.practice.id == practice_id).select().last()
    return dict(practice_id=practice_id, practice=practice)


def tracking():
    return dict()


@auth.requires_login()
def router():
    if my_role in ["admin", "trainer"]:
        redirect(URL("home"))
    else:
        practice = db(db.practice.trainer.contains(auth.user.id)).select().first()
        if practice:
            redirect(URL("dashboard", vars=dict(practice=practice.id, section="gap")))
    session.flash = "Please request an admin to give privelages to your account."
    redirect(URL('default', 'user', args=['profile']))


def practice_tracking():
    practice_id = request.vars["practice"]
    practice = db(db.practice.id == practice_id).select().last()

    return dict(**locals())


def summary():
    practice_id = request.vars["practice"]
    practice = db(db.practice.id == practice_id).select().last()
    return dict(practice_id=practice_id, practice=practice)


def dashboard_print():
    return dashboard()


def _get_tracking_table():

    return dict()

@auth.requires_login()
def dashboard():
    if search:
        redirect(URL('home', vars=dict(search=search)))

    progress = 0.0

    form = None

    question_order = []

    slides = {}

    if is_gap:
        slides = json.loads(_get_private_file('slides_gap.json'), object_pairs_hook=collections.OrderedDict)
    if is_front:
        slides = json.loads(_get_private_file('slides_front.json'), object_pairs_hook=collections.OrderedDict)
    if is_provider:
        slides = json.loads(_get_private_file('slides_provider.json'), object_pairs_hook=collections.OrderedDict)
    if is_staff_training:
        slides = json.loads(_get_private_file('slides_staff.json'), object_pairs_hook=collections.OrderedDict)
    if is_emr_training:
        slides = json.loads(_get_private_file('slides_emr.json'), object_pairs_hook=collections.OrderedDict)


    practice = db(db.practice.id == practice_id).select().last()  #TODO practice id is list
    if is_training:
        _recurse_questions(slides, question_order)

        navigation = {}

        progress = _get_question_progress(question_order, practice_id)

        first_question = question_order[0]

    elif is_survey:
        def onvalidation(form):
            form.vars.practice =practice_id

        survey_tc_form_row = db(db.survey_tc.practice == practice_id).select().last()
        survey_tc_form = SQLFORM(db.survey_tc, survey_tc_form_row, keepvalues=True)
        db.survey_tc.practice.default = practice_id
        db.survey_tc.practice.readable = False
        db.survey_tc.practice.writable = False
        if survey_tc_form.process(onvalidation = onvalidation).accepted:
            session.flash = "TC Form updated!"
            _redirect_after_submit()

        survey_km_form_row = db(db.survey_km.practice == practice_id).select().last()
        survey_km_form = SQLFORM(db.survey_km, survey_km_form_row, keepvalues=True)
        db.survey_km.practice.default = practice_id
        db.survey_km.practice.readable = False
        db.survey_km.practice.writable = False
        if survey_km_form.process(onvalidation = onvalidation).accepted:
            session.flash = "KM Form updated!"
            _redirect_after_submit()

        survey_ac_form_row = db(db.survey_ac.practice == practice_id).select().last()
        survey_ac_form = SQLFORM(db.survey_ac, survey_ac_form_row, keepvalues=True)
        db.survey_ac.practice.default = practice_id
        db.survey_ac.practice.readable = False
        db.survey_ac.practice.writable = False
        if survey_ac_form.process(onvalidation = onvalidation).accepted:
            session.flash = "AC Form updated!"
            _redirect_after_submit()

        survey_cm_form_row = db(db.survey_cm.practice == practice_id).select().last()
        survey_cm_form = SQLFORM(db.survey_cm, survey_cm_form_row, keepvalues=True)
        db.survey_cm.practice.default = practice_id
        db.survey_cm.practice.readable = False
        db.survey_cm.practice.writable = False
        if survey_cm_form.process(onvalidation = onvalidation).accepted:
            session.flash = "CM Form updated!"
            _redirect_after_submit()

        survey_cc_form_row = db(db.survey_cc.practice == practice_id).select().last()
        survey_cc_form = SQLFORM(db.survey_cc, survey_cc_form_row, keepvalues=True)
        db.survey_cc.practice.default = practice_id
        db.survey_cc.practice.readable = False
        db.survey_cc.practice.writable = False
        if survey_cc_form.process(onvalidation = onvalidation).accepted:
            session.flash = "CC Form updated!"
            _redirect_after_submit()

        survey_qi_form_row = db(db.survey_qi.practice == practice_id).select().last()
        survey_qi_form = SQLFORM(db.survey_qi, survey_qi_form_row, keepvalues=True)
        db.survey_qi.practice.default = practice_id
        db.survey_qi.practice.readable = False
        db.survey_qi.practice.writable = False
        if survey_qi_form.process(onvalidation = onvalidation).accepted:
            session.flash = "QI Form updated!"
            _redirect_after_submit()

    else:
        db[section].practice.default=practice_id
        form = SQLFORM.grid(db[section].practice == practice_id, maxtextlength=40, details=False, deletable=False if IS_GRID else True)

    return dict(**locals())


def delete_practice():
    practice_id = request.args(0)
    record = db(db.practice.id==practice_id).select().last()
    record.delete_record()
    redirect(URL("home"))


import os
def _get_private_file(filename):
    x = open(os.path.join(request.folder, 'private', filename), "r")
    y = x.read()
    x.close()
    return y


def _recurse_questions(d, l, p=None, pt=None):
    l[:] = [] # clear in place
    def recurse(d, l, p, pt):
        for i in d:
            c = db(db.answer.identifier==i).select().last()
            ct = d[i]["type"]
            if p:
                if pt == "yesNo":
                    if p.yes_no == d[i]["showIfParentEquals"]:
                        print d[i]["showIfParentEquals"]
                        l.append(i)
                    #else:
                        #return
            else:
                l.append(i)

            if 'branches' in d[i] and c is not None:
                recurse(d[i]['branches'], l, p=c, pt=ct)
    recurse(d, l, p, pt)


def _get_question_progress(identifiers, pid):
    #@cache("question_progress_%s"%pid, time_expire=300, cache_model=cache.disk)

    denominator = len(identifiers)
    answered = []
    for identifier in identifiers:
        answer = db((db.answer.practice==pid) & (db.answer.identifier == identifier)).select().last()
        answered.append(bool(answer))
    numerator = answered.count(True)

    answered_by_id = OrderedDict(zip(identifiers, answered))

    return dict(percent = float(numerator) / float(denominator), answered_by_id = answered_by_id)



def _set_question_navigation(d, identifiers, current_id, practice_id, section):
    ##print identifiers
    current_id = current_id
    current_index = identifiers.index(current_id)
    current_url = URL(vars=dict(practice=practice_id, section=section), args=[current_id])
    if current_index == 0:
        previous_id = None
        previous_url = None
    else:
        previous_id = identifiers[current_index - 1]
        previous_url = URL(vars=dict(practice=practice_id, section=section), args=[previous_id])
    if identifiers[-1] == current_id:
        next_id = None
        next_url = None
    else:
        next_id = identifiers[current_index + 1]
        next_url = URL(vars=dict(practice=practice_id, section=section), args=[next_id])

    d.clear()
    d.update(**locals())


def _search_cards(search):
    keywords = _split_and_lower(search)
    query = (db.practice.keywords.contains(keywords))
    #print "FJFJDJDFJDJF"
    return query


def questions():
    if search:
        redirect(URL('home', vars=dict(search=search)))

    is_upload = is_yes_no = is_response = is_download = None

    progress = 0.0

    form = None

    question_order = []

    current_id = request.args[0]

    slides = None

    if is_gap:
        slides = json.loads(_get_private_file('slides_gap.json'), object_pairs_hook=collections.OrderedDict)
    if is_front:
        slides = json.loads(_get_private_file('slides_front.json'), object_pairs_hook=collections.OrderedDict)
    if is_provider:
        slides = json.loads(_get_private_file('slides_provider.json'), object_pairs_hook=collections.OrderedDict)
    if is_staff_training:
        slides = json.loads(_get_private_file('slides_staff.json'), object_pairs_hook=collections.OrderedDict)
    if is_emr_training:
        slides = json.loads(_get_private_file('slides_emr.json'), object_pairs_hook=collections.OrderedDict)

    ##print "is provider %s"%is_provider
    ##print "is gap %s"%is_gap
    ##print "is front %s"%is_front

    ##print practice_id

    practice = db(db.practice.id == practice_id).select().last()

    ##print len(_recurse_find_by_key(slides, current_id))

    (current_slide, current_depth) = _recurse_find_by_key(slides, current_id)

    current_type = current_slide["type"]

    current_template = current_slide.get("template", None)

    current_inquiry = current_slide["inquire"]

    _recurse_questions(slides, question_order)

    navigation = {}
    _set_question_navigation(navigation, question_order, current_id, practice_id, section)

    progress = _get_question_progress(question_order, practice_id)

    meta_data = dict(type=current_type, depth=current_depth, inquire=current_inquiry)

    if current_type == "download":
        is_download = True
        downloads = current_slide["assets"]
        meta_data["assets"] = downloads
        db.answer.insert(identifier=current_id, practice=practice_id, meta_data=json.dumps(meta_data))

    default_answer_row = db((db.answer.identifier==current_id) & (db.answer.practice==practice_id)).select().last()

    if current_type == "response":
        default_answer = getattr(default_answer_row, "response", None)
        answer_field = Field("response", "text", default=default_answer or current_template, requires=IS_NOT_EMPTY())
        form = SQLFORM.factory(
            answer_field,
        )
        is_response = True

    if current_type == "yesNo":
        default_answer = getattr(default_answer_row, "yes_no", None)
        if default_answer is not None:
            default_answer = "Yes" if default_answer is True else "No"
        answer_field = Field("yes_no", default=default_answer, requires=IS_IN_SET(["Yes", "No"]))
        form = SQLFORM.factory(
            answer_field,
        )
        is_yes_no = True

    if current_type.lower() == "upload":
        form = SQLFORM.factory(
            Field('file_name', requires=IS_NOT_EMPTY()),
            Field('file_upload', 'upload'),
        )
        uploads = db((db.answer.identifier==current_id) & (db.answer.practice==practice_id)).select()
        is_upload = True


    if form and form.process().accepted:

        if form.vars.yes_no == "Yes":
            yes_no = True
        elif form.vars.yes_no == "No":
            yes_no = False
        else:
            yes_no = None

        db.answer.insert(identifier=current_id, response=form.vars.response, file_name=form.vars.file_name,
                         file_upload=form.vars.file_upload, yes_no=yes_no, practice=practice_id,
                         meta_data=json.dumps(meta_data))
        session.flash = 'Submission accepted!'
        practice.update_record(dashboard_modified_on=datetime.datetime.now())
        _recurse_questions(slides, question_order)
        _set_question_navigation(navigation, question_order, current_id, practice_id, section)
        redirect(navigation["next_url"] if navigation["next_url"] else navigation["current_url"])

    session.question = current_id
    session.section = section

    return dict(**locals())





@auth.requires_login()
def overview():
    practice_id = request.vars["practice"]
    practice = db(db.practice.id == practice_id).select().last()
    return dict(practice_id=practice_id, practice=practice)


def nt_download():
    if not str(request.args(0)).startswith('no_table.'):
        raise HTTP(404)
    return response.stream(open(os.path.join(request.folder, 'uploads', request.args(0))), attachment=True)


def template_library():
    return dict()
    


    

def _process_emr_form(practice, emr_forms, emr_forms_green):
    emr_form = SQLFORM.factory(
        Field("emr_directions", "text", default=practice.emr_directions),
        Field("emr_email", default=practice.emr_email),
        Field("emr_password", default=practice.emr_password),
        Field("emr_problem", "boolean", default=practice.emr_problem),
        Field("emr_teamviewer", "boolean", default=practice.emr_teamviewer),
        Field("emr", default=practice.emr),
    )

    if emr_form.process(formname="emr_form_%s" % practice.id).accepted:
        db(db.practice.id == practice.id).update(**db.practice._filter_fields(emr_form.vars))
        session.flash = "EMR Info Updated!"
        _redirect_after_submit()

    emr_forms[practice.id] = emr_form
    emr_forms_green[practice.id] = all([
        #practice.emr_directions,
        practice.emr_email,
        practice.emr_password,
        not practice.emr_problem,
        practice.emr_teamviewer,
        practice.emr
    ])


def _process_cc_form(practice, cc_forms, cc_forms_meta):
    cc_form = SQLFORM.factory(
        Field("payment_is_check", 'boolean', default=practice.payment_is_check),
        Field("credit_card_first_name", default=practice.credit_card_first_name),
        Field("credit_card_last_name", default=practice.credit_card_last_name),
        Field("credit_card_type", default=practice.credit_card_type, requires=IS_EMPTY_OR(IS_IN_SET([
            "Visa", "Mastercard", "American Express"
        ]))),
        Field("credit_card_number", default=practice.credit_card_number),
        Field("credit_card_expiration_year", default=practice.credit_card_expiration_year),
        Field("credit_card_expiration_month", default=practice.credit_card_expiration_month,
              requires=IS_EMPTY_OR(IS_IN_SET(range(1, 13)))),
        Field("credit_card_cvv", default=practice.credit_card_cvv),
        Field("credit_card_street", default=practice.credit_card_street),
        Field("credit_card_state", default=practice.credit_card_state),
        Field("credit_card_zip", default=practice.credit_card_zip),
    )

    if cc_form.process(formname="cc_form_%s" % practice.id).accepted:
        db(db.practice.id == practice.id).update(**db.practice._filter_fields(cc_form.vars))
        session.flash = "Credit Card Info Updated!"
        _redirect_after_submit()

    cc_forms[practice.id] = cc_form

    cc_forms_meta[practice.id] = {}

    cc_forms_meta[practice.id]["practice"] = practice

    if practice.payment_is_check:
        cc_forms_meta[practice.id]["green"] = True
    else:
        cc_forms_meta[practice.id]["green"] = all([
            practice.credit_card_first_name, practice.credit_card_last_name,
            practice.credit_card_type, practice.credit_card_number, practice.credit_card_expiration_year,
            practice.credit_card_expiration_month, practice.credit_card_cvv, practice.credit_card_street,
            practice.credit_card_state, practice.credit_card_zip
        ])

def _process_baa_form(practice, baa_forms, baa_links):
    baa_form = SQLFORM.factory(
        Field('file_name', requires=IS_NOT_EMPTY()),
        Field('file_upload', 'upload'),
    )

    if baa_form.process(formname="baa_form_%s" % practice.id).accepted:
        print baa_form.vars
        db.uploads.insert(practice=practice.id, **db.uploads._filter_fields(baa_form.vars))
        session.flash = "Document uploaded!"
        _redirect_after_submit()

    baa_forms[practice.id] = baa_form

    baa_links[practice.id] = []

    uploads = db(db.uploads.practice == practice.id).select()

    for u in uploads:
        baa_links[practice.id].append(dict(file_name=u.file_name, file_upload=u.file_upload))


def _process_message_form(practice, message_forms, message_links):
    message_form = SQLFORM.factory(
        Field("subject"),
        Field("message_", 'text'),
    )

    if message_form.process(formname="message_form_%s" % practice.id).accepted:
        db.messaging.insert(practice=practice.id, **db.messaging._filter_fields(message_form.vars))
        session.flash = "Message Added!"
        _redirect_after_submit()

    message_forms[practice.id] = message_form

    message_links[practice.id] = db(db.messaging.practice == practice.id).select()


def _redirect_after_submit():
    cache.ram.clear()
    redirect(URL(args=request.args, vars=request.get_vars))


def _get_admin_ids():
    pass


import math
import datetime
@auth.requires(my_role in ["admin", "trainer"] or IS_MASTER)
def home():
    if len(request.args):
        page=int(request.args[0])
    else:
        page=0
    items_per_page=12-1
    limitby=(page*items_per_page,(page+1)*items_per_page+1)

    filter = request.vars["filter"]

    tagout = db((db.auth_user.id == request.vars["tagout"])).select().last() or auth.user

    search = request.vars["search"]

    practice_form = SQLFORM.factory(*practice_form_fields)

    if not IS_MASTER:
        query = (db.practice.id > 0) & (db.practice.trainer.contains(tagout.id))
    else:
        query = (db.practice.id > 0)
    if search:
        query &= _search_cards(search)
    if filter:
        query &= db.practice.is_renewal == (True if filter == "renewal" else False)

    count = db(query).count()
    practices = db(query).select(limitby=limitby, orderby=~db.practice.id)
    pages = math.ceil(count / (items_per_page))

    #print count, pages

    if practice_form.process(formname="practice_form").accepted:
        practice_form.vars["trainer"] = [auth.user.id]
        id = db.practice.insert(**db.practice._filter_fields(practice_form.vars))
        redirect(URL(vars=request.get_vars))

    emr_forms = {}
    emr_forms_green = {}
    admin_forms = {}
    cc_forms = {}
    cc_forms_meta = {}
    baa_forms = {}
    message_forms = {}
    message_links = {}
    baa_links = {}
    red_bells = {}

    for practice in practices:
        _process_emr_form(practice, emr_forms, emr_forms_green)
        _process_cc_form(practice, cc_forms, cc_forms_meta)
        _process_baa_form(practice, baa_forms, baa_links)
        _process_message_form(practice, message_forms, message_links)
        answers = db(db.answer.practice == practice_id).select()
        red_bells[practice.id] = []

    ###print request.post_vars

    return dict(practices=practices, practice_form=practice_form,
                emr_forms=emr_forms, tagout=tagout, _get_progress_by_practice=_get_progress_by_practice,
                emr_forms_green=emr_forms_green, cc_forms=cc_forms,
                cc_forms_meta=cc_forms_meta, baa_forms=baa_forms, baa_links=baa_links, page=page,
                items_per_page=items_per_page, pages=pages, red_bells=red_bells, message_forms=message_forms,
                message_links=message_links)


def _get_progress_by_practice(practice_id, section):
    @cache("progress_by_practice_%s_%s" % (practice_id, section), time_expire=600, cache_model=cache.disk)
    def inner():
        slides = json.loads(_get_private_file('slides_%s.json' % section), object_pairs_hook=collections.OrderedDict)
        question_order = []
        _recurse_questions(slides, question_order)
        progress = _get_question_progress(question_order, practice_id)
        return progress
    return inner()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


def process_practice_info_form():
    practice_id = request.args[0]

    practice = db(db.practice.id == practice_id).select().last()

    practice_info_form = SQLFORM.factory(
        Field('practice_specialty',
              requires=IS_IN_SET(['Internal Medicine', 'Pediatrics', 'Family']),
              default=practice.practice_specialty
              ),
        Field('address', default=practice.address),
        Field('practice_name', default=practice.practice_name),
        Field('phone', default=practice.phone),
        Field('fax', default=practice.fax),
        Field('days', "list:string", default=practice.days),
        Field("hours_from", "list:string", requires=IS_TIME(), default=practice.hours_from),
        Field("hours_to", "list:string", requires=IS_TIME(), default=practice.hours_to),
        Field('credentials', default=practice.credentials),
        Field("practice_email", default=practice.practice_email, requires=IS_EMAIL()),
        Field('dea_number', default=practice.dea_number),
        Field('providers', "list:string", default=practice.providers),
        Field('provider_license', "list:string", default=practice.provider_license),
        Field('provider_npi', "list:string", default=practice.provider_npi),
        Field('provider_dob', "list:string", default=practice.provider_dob),
        Field('provider_board', "list:string", default=practice.provider_board),
        Field('provider_credential', "list:string", default=practice.provider_credential),
        Field('practice_npi', default=practice.practice_npi),
        Field('practice_tax_id', default=practice.practice_tax_id),

    )


    if practice_info_form.process(formname="practice_info_form_%s" % practice.id).accepted:
        db(db.practice.id == practice.id).update(**db.practice._filter_fields(practice_info_form.vars))
        session.flash = "Practice Updated!"
        redirect(URL(args=request.args))
        #_redirect_after_submit()

    return dict(form=practice_info_form)

def staff_management():
    practice_id = request.args[0]

    practice = db(db.practice.id == practice_id).select().last()

    practice_info_form = SQLFORM.factory(
        Field('practice_specialty',
              requires=IS_IN_SET(['Internal Medicine', 'Pediatrics', 'Family']),
              default=practice.practice_specialty
              ),
        Field('address', default=practice.address),
        Field('practice_name', default=practice.practice_name),
        Field('phone', default=practice.phone),
        Field('fax', default=practice.fax),
        Field('days', "list:string", default=practice.days),
        Field("hours_from", "list:string", requires=IS_TIME(), default=practice.hours_from),
        Field("hours_to", "list:string", requires=IS_TIME(), default=practice.hours_to),
        Field('credentials', default=practice.credentials),
        Field("practice_email", default=practice.practice_email, requires=IS_EMAIL()),
        Field('dea_number', default=practice.dea_number),
        Field('providers', "list:string", default=practice.providers),
        Field('provider_license', "list:string", default=practice.provider_license),
        Field('provider_npi', "list:string", default=practice.provider_npi),
        Field('provider_dob', "list:string", default=practice.provider_dob),
        Field('provider_board', "list:string", default=practice.provider_board),
        Field('provider_credential', "list:string", default=practice.provider_credential),
        Field('practice_npi', default=practice.practice_npi),
        Field('practice_tax_id', default=practice.practice_tax_id),

    )




    return dict(form=practice_info_form)
def process_admin_form():

    practice_id = request.args[0]

    practice = db(db.practice.id == practice_id).select().last()

    admin_form = SQLFORM.factory(
        Field('trainer', 'list:reference auth_user', default=practice.trainer,
              requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s (%(id)s)', multiple=True)),
        Field("pps", default = practice.pps),
        Field("app_tool_username", default = practice.app_tool_username),
        Field("app_tool_password", default = practice.app_tool_password),
        Field("survey_tool_username", default = practice.survey_tool_username),
        Field("survey_tool_password", default = practice.survey_tool_password),
    )

    if admin_form.process(formname="admin_form_%s" % practice.id).accepted:
        print admin_form.vars
        db(db.practice.id == practice.id).update(**db.practice._filter_fields(admin_form.vars))
        session.flash = "Admin Info Updated!"
        redirect(URL(args=request.args))

    return dict(form=admin_form)