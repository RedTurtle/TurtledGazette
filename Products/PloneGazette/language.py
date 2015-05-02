# -*- coding: utf8 -*-

from zope.component.hooks import getSite
from zope.interface import implements
from plone.app.multilingual.interfaces import LANGUAGE_INDEPENDENT
from Products.CMFPlone.interfaces import ILanguage


class PNLLanguage(object):
    """ PNL doens't support language
    Still, we need this for Plone 5 compatibility
    """
    implements(ILanguage)

    def __init__(self, context):
        self.context = context

    def get_language(self):
        return LANGUAGE_INDEPENDENT

    def set_language(self, language):
        """Can't set language"""
        raise NotImplementedError("PNBBase doens't support setting language")
