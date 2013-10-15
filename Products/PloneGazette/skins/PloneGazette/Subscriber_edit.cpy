## Script (Python) "Subscriber_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=id='', email=None, format=None, active=None
##title=Edit a Subscriber
##

# if there is no id specified, keep the current one
if not id:
    id = context.getId()

_ = context.translate

new_context = context.portal_factory.doCreate(context, id)

# Custom editing method (called only for specific attributes)
new_context.edit(format=format, active=active, email=email)

statusMsg = _('subscriber_saved',
              default=u'Subscriber changes saved.', domain="plonegazette")
context.plone_utils.addPortalMessage(statusMsg, 'info')

return state.set(context=new_context)
