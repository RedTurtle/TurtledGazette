from zope.interface import implements

from Products.Archetypes.atapi import BaseBTreeFolder, BaseBTreeFolderSchema
from Products.Archetypes.atapi import registerType
from AccessControl import ClassSecurityInfo
from PNLPermissions import *
from PNLBase import PNLContentBase
from Products.CMFCore.permissions import ListFolderContents
from Products.PloneGazette.interfaces import INewsletterBTree
from Products.PloneGazette import config

class NewsletterBTree(BaseBTreeFolder, PNLContentBase):
    implements(INewsletterBTree)
    
    portal_type = meta_type = 'NewsletterBTree' 
    archetype_name = 'Newsletter Large Folder'   #this name appears in the 'add' box
    # 
    default_view = 'newsletterbtree_view'
    
    security = ClassSecurityInfo()
    schema = BaseBTreeFolderSchema.copy()

    # Make sure we get title-to-id generation when an object is created
    _at_rename_after_creation = True

    security.declarePublic('displayContentsTab')
    def displayContentsTab(self):
        """ do not display 'contents' tab """
        return False

    #Methods
    security.declareProtected(ChangeNewsletterTheme, 'listFolderContents')
    def listFolderContents(self, spec=None, contentFilter=None, suppressHiddenFiles=0):
        """
        """
        return BaseFolder.listFolderContents(self, contentFilter=contentFilter, suppressHiddenFiles=suppressHiddenFiles)
        
    security.declareProtected(ChangeNewsletterTheme, 'folderlistingFolderContents')
    def folderlistingFolderContents(self, spec=None, contentFilter=None, suppressHiddenFiles=0):
        """
        """
        return self.listFolderContents(spec, contentFilter, suppressHiddenFiles)

    security.declareProtected(ListFolderContents, 'folder_contents')
    def folder_contents(self, REQUEST=None, RESPONSE=None):
        """ redirect """
        if REQUEST is None:
            REQUEST = self.REQUEST
        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE
        return RESPONSE.redirect(self.absolute_url()+'/view')
        

registerType(NewsletterBTree, config.PROJECTNAME)


