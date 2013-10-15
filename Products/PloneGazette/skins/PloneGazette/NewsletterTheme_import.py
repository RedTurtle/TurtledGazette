## Script (Python) "NewsletterTheme_import"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=file_upload
##title=
##
request = context.REQUEST
redirect = request.RESPONSE.redirect

plone_utils = context.plone_utils

result = context.createSubscribersFromCSV(file_upload)
plone_utils.addPortalMessage(msg, type="error")

return redirect(context.absolute_url() + '/NewsletterTheme_importForm?import=1')



