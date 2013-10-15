## Script (Python) "NewsletterCentral_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id='', title=None, description=None, default_format='', body='', testEmail='', authorEmail='', replyto='', activationMailSubject='', activationMailTemplate='', newsletterFooter='', notify=0, renderTemplate='', extraRecipients='', subscriber_folder_id='', alternative_portal_url=None, text='', text_format=''
##title=Edit content and metadata
##

if not id:
    id = context.getId()

_ = context.translate

new_context = context.portal_factory.doCreate(context, id)
new_context.edit(title=title,
                 default_format=default_format,
                 testEmail=testEmail,
                 authorEmail=authorEmail,
                 replyto=replyto,
                 activationMailSubject=activationMailSubject,
                 activationMailTemplate=activationMailTemplate,
                 newsletterFooter=newsletterFooter,
                 notify=notify,
                 renderTemplate=renderTemplate,
                 extraRecipients=extraRecipients,
                 subscriber_folder_id=subscriber_folder_id,
                 alternative_portal_url=alternative_portal_url,
                 text=text,
                 text_format=text_format)

new_context.plone_utils.contentEdit(new_context, 
                                    description=description)

# contentEdit don't work for description as expected
# Also we have UnicodeError if with collective.indexing
#new_context.setDescription(description)
new_context.setDescription(description.decode('utf-8'))

statusMsg = _('newsletter_theme_save',
              default=u'Newsletter Theme changes saved.', domain="plonegazette")
context.plone_utils.addPortalMessage(statusMsg, 'info')

return state.set(context=new_context)
