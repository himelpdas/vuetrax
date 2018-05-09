practice_id = request.args[0]

def process_practice_info_form():

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


