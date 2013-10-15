## Controller Python Script "validate_newslettertheme_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=title='', testEmail='',authorEmail='', replyto='', activationMailSubject='', activationMailTemplate='', subscriber_folder_id=''
##title=Validates a Newsletter Theme edit_form contents
##

_ = context.translate
required = _('mail_required',
             default=u'Input is required but no input given',
             domain='plonegazette')
not_valid_email = _('invalid_email_address',
                    default=u'This is not a valid mail address', domain='plonegazette')

if not title:
    state.setError('title', required)

if not testEmail:
    state.setError('testEmail', required)
else:
    if not context.checkMailAddress(testEmail.strip()):
        state.setError('testEmail', not_valid_email)

if not authorEmail:
    state.setError('authorEmail', required)
else:
    if not context.checkMailAddress(authorEmail.strip()):
        state.setError('authorEmail', not_valid_email)

if replyto and not context.checkMailAddress(replyto.strip()):
    state.setError('replyto', not_valid_email)

if not activationMailSubject:
    state.setError('activationMailSubject', required)

if not activationMailTemplate:
    state.setError('activationMailTemplate', required)
else:
    errMsg = _('template_format_error',
               default="This template must contain <b>%(url)s</b> and <b>%(email)s</b><br />"
                        " These key are needed to be replaced by the subscriber's preferences URL"
                        " and his e-mail address in the activation mail",
               domain='plonegazette')
    template = activationMailTemplate
    if template.find('%(url)s') == -1 or template.find('%(email)') == -1:
        state.setError('activationMailTemplate', errMsg)

talExpressions = [(name, context.REQUEST[name].strip()) for name in ('renderTemplate', 'extraRecipients')]

context.checkTalExpressions(talExpressions, state=state)

if subscriber_folder_id and subscriber_folder_id not in context.objectIds('NewsletterBTree'):
    state.setError('subscriber_folder_id', _('must_create_nlf',
                                             default=u'You must first create a large plone folder',
                                             domain='plonegazette'))

if state.getErrors():
    context.plone_utils.addPortalMessage(_('please_fix_errors',
                                           default=u'Please correct the indicated errors.', domain='plonegazette'),
                                         type="error")
    return state.set(status='failure')
else:
    return state
