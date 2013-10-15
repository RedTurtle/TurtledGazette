from zope.interface import Interface

class INewsletterBTreeView(Interface):
    """ """
    
    def listSubscribers():
        """ return list of subscribers in the folder """
    
    def parent_url():
        """ returns parent url """