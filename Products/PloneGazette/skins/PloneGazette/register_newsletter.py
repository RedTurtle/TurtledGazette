## Script (Python) "register_newsletter"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=nlpath, email, format=None, REQUEST=None
##title=Newsletter subscription hub
##
# ******************************************************************
# ** Transmit the subscribe request to selected NewsletterTheme **
# ******************************************************************
#
# Handles the subscription form from newsletter_slot
#
# $Id: register_newsletter.py 20500 2004-08-18 08:17:06Z zope $
#
from Products.PythonScripts.standard import url_quote

if REQUEST is None:
    REQUEST = context.REQUEST
    
nlcentral = context.restrictedTraverse(nlpath)

if format is None:
    format = nlcentral.default_format
    
actions = context.portal_actions.listFilteredActionsFor(object=nlcentral)
url = [action['url'] for action in actions['object']
       if action['id'] == 'subscribe'][0]
query = '?email=%s&format=%s' % (url_quote(email), format)

REQUEST.RESPONSE.redirect(url + query)
return
