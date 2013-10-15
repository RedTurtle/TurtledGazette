# -*- coding: utf-8 -*-

from zope.interface import Interface

class INewsletterBTree(Interface):
    """ BTree folder - holds subscribers """
    
class INewsletterTheme(Interface):
    """ Base content object for newsletters and subscribers """

class INewsletter(Interface):
    """Base newsletter content"""
    
class ISubscriber(Interface):
    """The newsletter subscriber"""
