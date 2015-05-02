# -*- coding: utf-8 -*-

from zope.interface import Interface


class IPNLBase(Interface):
    """ Interface for all PNL content types """

class INewsletterBTree(IPNLBase):
    """ BTree folder - holds subscribers """
    
class INewsletterTheme(IPNLBase):
    """ Base content object for newsletters and subscribers """

class INewsletter(IPNLBase):
    """Base newsletter content"""
    
class ISubscriber(IPNLBase):
    """The newsletter subscriber"""
