# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# ----------------------------------------------------------------------------------------------------------------------
# Customize your APP title, subtitle and menus here
# ----------------------------------------------------------------------------------------------------------------------

response.logo = A(B('web', SPAN(2), 'py'), XML('&trade;&nbsp;'),
                  _class="navbar-brand", _href="http://www.web2py.com/",
                  _id="web2py-logo")
response.title = request.application.replace('_', ' ').title()
response.subtitle = ''

# ----------------------------------------------------------------------------------------------------------------------
# read more at http://dev.w3.org/html5/markup/meta.name.html
# ----------------------------------------------------------------------------------------------------------------------
response.meta.author = myconf.get('app.author')
response.meta.description = myconf.get('app.description')
response.meta.keywords = myconf.get('app.keywords')
response.meta.generator = myconf.get('app.generator')

# ----------------------------------------------------------------------------------------------------------------------
# your http://google.com/analytics id
# ----------------------------------------------------------------------------------------------------------------------
response.google_analytics_id = None

practice_id = request.vars["practice"]

section = request.vars["section"]

is_referral = section == "referral"

is_lab = section == "lab"

is_imaging = section == "imaging"

is_telephone = section == "telephone"

is_secure_messaging = section == "secure_messaging"

is_hospital = section == "hospital"

is_tracking = any([is_referral, is_lab, is_imaging, is_telephone, is_hospital, is_secure_messaging])

is_gap = section == "gap"

is_front = section == "front"

is_provider = section == "provider"

if auth.is_logged_in():
    if auth.user.email.lower() in ["gdewey@insightmanagement.org", "himel@insightmanagement.org"]:
        my_role = "admin"
    else:
        my_role = getattr(db(db.role.owner_id == auth.user.id).select().last(), "role", None) or "usr"
else:
    my_role = "guest"