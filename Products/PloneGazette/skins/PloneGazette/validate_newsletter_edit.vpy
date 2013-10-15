## Controller Python Script "validate_newsletter_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=title='', dateEmitted=None
##title=Validates a Newsletter edit_form contents
##

_ = context.translate
plone_utils = context.plone_utils

if not title:
    state.setError('title', _('mail_required',
                              default=u'Input is required but no input given',
                              domain='plonegazette'))

if dateEmitted is not None:
    dateEmitted = dateEmitted.strip()
    try:
        if dateEmitted != '':
            dateEmitted = DateTime(dateEmitted)
    except:
        dateEmitted = None
        state.setError('dateEmitted',
                       _('valid_date_required',
                         default=u'Please provide a valid date', domain='plonegazette'))

if state.getErrors():
    plone_utils.addPortalMessage(_('please_fix_errors',
                                   default=u'Please correct the indicated errors.',
                                   domain='plonegazette'), type="error")
    return state.set(status='failure')
else:
    return state
