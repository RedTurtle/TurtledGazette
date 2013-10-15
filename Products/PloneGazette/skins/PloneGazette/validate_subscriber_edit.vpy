## Controller Python Script "validate_subscriber_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=email=None
##title=Validates a Subscriber edit_form contents
#
#
_ = context.translate

if not email:
    state.setError('email', _('input_required',
                              default=u'Input is required but no input given',
                              domain='plonegazette'))
else:
    if not context.checkMailAddress(email.strip()):
        state.setError('email', _('invalid_email_address',
                                  default=u'This is not a valid mail address',
                                  domain='plonegazette'))
    else:
        theme = context.getTheme()
        if context.email != email and  theme.alreadySubscriber(email):
            state.setError('email', _('already_subscribed',
                                      default=u'There is already a subscriber with this address',
                                      domain='plonegazette'))

if state.getErrors():
    context.plone_utils(_('please_fix_errors',
                          domain=u'Please correct the indicated errors.', domain='plonegazette'))
    return state.set(status='failure')
else:
    return state
