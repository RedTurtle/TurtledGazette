# -*- coding: utf-8 -*-

# Zope imports
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

# Archetypes imports
from Products.Archetypes.public import *
from Products.CMFCore.CatalogTool import CatalogTool
# Products imports
from Products.PloneGazette.config import PG_CATALOG

class args:
    def __init__(self, **kw):
        self.__dict__.update(kw)

class SubscribersCatalog(CatalogTool):
    """Subscribers catalog for PloneGazette"""

    id = PG_CATALOG
    title = "Subscribers Catalog"
    
    security = ClassSecurityInfo()
    
    def __init__(self):
        CatalogTool.__init__(self)
    
    security.declarePublic('enumerateIndexes')
    def enumerateIndexes(self):
        """Returns indexes used by catalog"""
        return (
                ('path', 'PathIndex'),
                ('id', 'FieldIndex'),
                ('email', 'FieldIndex'),
                ('SearchableText', 'ZCTextIndex'),
                ('fullname', 'ZCTextIndex'),
                ('format', 'FieldIndex'),
                ('active', 'FieldIndex'),
                )
    
    def __url(self, object):
        """Returns url of object"""
        return '/'.join(object.getPhysicalPath())
    
    security.declarePrivate('indexObject')
    def indexObject(self, object):
        '''Add to catalog.
        '''
        url = self.__url(object)
        self.catalog_object(object, url)

    security.declarePrivate('unindexObject')
    def unindexObject(self, object):
        '''Remove from catalog.
        '''
        url = self.__url(object)
        self.uncatalog_object(url)

    security.declarePrivate('reindexObject')
    def reindexObject(self, object, idxs=[],  update_metadata=1, uid=None):
        """Update catalog after object data has changed.
        The optional idxs argument is a list of specific indexes
        to update (all of them by default).
        """
        
        url = self.__url(object)
        if idxs != []:
            # Filter out invalid indexes.
            valid_indexes = self._catalog.indexes.keys()
            idxs = [i for i in idxs if i in valid_indexes]
        self.catalog_object(object, url, idxs=idxs, update_metadata=update_metadata)

InitializeClass(SubscribersCatalog)


def manage_addSubscribersCatalog(self, REQUEST=None):
    """Add the subscribers catalog
    """

    c = SubscribersCatalog()
    self._setObject(c.getId(), c)

    cat = getattr(self, c.getId())
    
    # Add Lexicon
    cat.manage_addProduct['ZCTextIndex'].manage_addLexicon(
        'pg_lexicon',
        elements=[
            args(group='Case Normalizer', name='Case Normalizer'),
            args(group='Stop Words', name=" Don't remove stop words"),
            args(group='Word Splitter', name="Unicode Whitespace splitter"),
        ]
        )


    # Add indexes and metadatas    
    for index_name, index_type in cat.enumerateIndexes():
        try:
            if index_name not in cat.indexes():
                if index_type == 'ZCTextIndex':
                    extra = args(doc_attr=index_name,
                                 lexicon_id='pg_lexicon',
                                 index_type='Okapi BM25 Rank')
                    cat.addIndex(index_name, index_type, extra=extra)
                else:
                    cat.addIndex(index_name, index_type)
                    
            if not index_name in cat.schema():
                cat.addColumn(index_name)
        except:
            pass
                    
    if REQUEST is not None:
        return self.manage_main(self, REQUEST,update_menu=1)
    
