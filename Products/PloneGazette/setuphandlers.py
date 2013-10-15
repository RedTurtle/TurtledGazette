from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.PloneGazette.config import PG_CATALOG
import logging
logger = logging.getLogger('PloneGazette')

def importVarious(context):
    """
    """
    site = context.getSite()
    migrateAttributes(site)
    
    wtool = getToolByName(site, 'portal_workflow')
    ctool = getToolByName(site, 'portal_catalog')
    newsletterthemes = [s.getObject() for s in ctool(portal_type='NewsletterTheme')]
    for nl in newsletterthemes:
        if not base_hasattr(nl, PG_CATALOG):
            logger.info('Migrating Subscriber objects to catalog for NewsletterTheme %s' % nl.getId())
            nl._initCatalog()
            # find subscribers in newsletter theme and 'subscribers' folder
            subscribers = [s for s in nl.objectValues('Subscriber')]
            folder = nl.getSubscriberFolder()
            if folder is not None:
                subscribers.extend([s for s in folder.objectValues('Subscriber')])
            for s in subscribers:
                # migrate attributes
                if s._internalVersion == 1:
                    s.email    = s.title
                    s.fullname = ''
                    del s.title
                    s._internalVersion = 2
                # index all subscribers
                s.indexObject()
            logger.info('Migration of Subscriber objects done.')

    chain = wtool.getChainFor('Subscriber')
    if 'one_state_workflow' not in chain:
        logger.info('Setting one_state_workflow for Subscriber objects')
        wtool.setChainForPortalTypes(('Subscriber',), ('one_state_workflow',))
        logger.info('Setting one_state_workflow for Subscriber objects done.')
        # we don't need allowedRolesAndUsers index, because subscribers are not listed
        # in default templates nor indexed in portal_catalog
        
    return ''

def migrateAttributes(self):
    """ Migrate Newsletter instances to have all required attributes
    """
    ctool = getToolByName(self, 'portal_catalog')
    nls = ctool(portal_type='Newsletter')
    for nl in nls:
        obj = nl.getObject()
        if obj is not None:
            if not base_hasattr(obj, '_dynamic_content'):
                setattr(obj, '_dynamic_content', None)
                obj._p_changed = 1
            
    