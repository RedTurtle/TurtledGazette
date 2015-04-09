## Script (Python) "Newsletter_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id='', title=None, description=None, text=None, dateEmitted=None, text_format='text', attachment=None
##title=Edit content and metadata
##
# 

from Products.CMFPlone import PloneMessageFactory as _

if not id:
    id = context.getId()

new_context = context.portal_factory.doCreate(context, id)
new_context.edit(text_format=text_format,
                 text=text,
                 title=title,
                 dateEmitted=dateEmitted,
                 attachment=attachment)

new_context.plone_utils.contentEdit(new_context)

# contentEdit don't work for description as expected
new_context.setDescription(description)

statusMsg = _(u'Newsletter changes saved.')
context.plone_utils.addPortalMessage(statusMsg, 'info')
return state.set(context=new_context)
