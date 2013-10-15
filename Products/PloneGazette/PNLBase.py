# -*- coding: utf-8 -*-

# Zope core import
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

# CMF/Plone imports
from Products.CMFCore.utils import getToolByName

class PNLContentBase(object):
    """Shared by all that's in a NewsletterCentral
    """
    security = ClassSecurityInfo()

    security.declarePublic('getTheme')
    def getTheme(self):
        """Returns the NewsletterTheme parent object or None"""

        obj = self
        while 1:
            obj = obj.aq_parent
            if obj.meta_type == 'NewsletterTheme':
                return obj
            if not obj:
                return None
        return

    security.declarePublic('getNewsletter')
    def getNewsletter(self):
        """Returns the NewsletterTheme parent object or None"""

        obj = self
        while obj:
            if obj.meta_type == 'Newsletter':
                return obj
            obj = obj.aq_parent
        return None

    security.declarePublic('ploneCharset')
    def ploneCharset(self):
        """The default charset of this Plone instance"""

        portal_properties = getToolByName(self, 'portal_properties')
        charset = portal_properties.site_properties.getProperty('default_charset').strip()
        return charset
        
InitializeClass(PNLContentBase)
