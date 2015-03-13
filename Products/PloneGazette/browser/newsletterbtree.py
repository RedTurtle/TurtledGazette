from Acquisition import aq_inner, aq_parent
from AccessControl import Unauthorized
from zope.interface import implements
from Products.Five import BrowserView
from Products.PloneGazette.browser.interfaces import INewsletterBTreeView
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName

class NewsletterBTreeView(BrowserView):
    implements(INewsletterBTreeView)
    
    def listSubscribers(self):
        context = aq_inner(self.context)
        # blah, acquired from NewsletterTheme
        subscribers = context.getSubscribers(path='/'.join(context.getPhysicalPath()))
        result = []
        for s in subscribers:
            # process catalog brains
            result.append({'url':s.getURL(), 
                           'email':s.email,
                           'format':s.format,
                           'id':s.id,
                           'active':s.active,
                           })
        return result
        
    def parent_url(self):
        """
        This method is copied from plone.app.content.browser.foldercontents view
        """
        portal_membership = getToolByName(self.context, 'portal_membership')

        obj = self.context

        checkPermission = portal_membership.checkPermission

        # Abort if we are at the root of the portal
        if IPloneSiteRoot.providedBy(self.context):
            return None
        

        # Get the parent. If we can't get it (unauthorized), use the portal
        parent = aq_parent(aq_inner(obj))
        
        # # We may get an unauthorized exception if we're not allowed to access#
        # the parent. In this case, return None
        try:
            if getattr(parent, 'getId', None) is None or \
                   parent.getId() == 'talkback':
                # Skip any Z3 views that may be in the acq tree;
                # Skip past the talkback container if that's where we are
                parent = aq_parent(aq_inner(parent))

            if not checkPermission('List folder contents', parent):
                return None
    
            return parent.absolute_url()

        except Unauthorized:
            return None   