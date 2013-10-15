# -*- coding: utf-8 -*-

## Archetypes import
from Products.Archetypes.public import *
from Products.Archetypes import listTypes

## CMF imports

from Products.CMFCore.utils import ContentInit
from Products.CMFCore import permissions, DirectoryView
from Products.CMFCore.utils import registerIcon

from zope.i18nmessageid import MessageFactory
PloneGazetteFactory = MessageFactory('plonegazette')

## App imports
from config import PROJECTNAME
from config import product_globals

DirectoryView.registerDirectory('skins', product_globals)
DirectoryView.registerDirectory('skins/PloneGazette', product_globals)

def initialize(context):

    import NewsletterTheme, Newsletter, Subscriber, NewsletterBTree

    contentConstructors = (Newsletter.addNewsletter, Subscriber.addSubscriber)
    contentClasses = (Newsletter.Newsletter, Subscriber.Subscriber)
    factoryTypes = (Newsletter.Newsletter.factory_type_information,
                    Subscriber.Subscriber.factory_type_information)

    ContentInit(
        'Plone Gazette Newsletter Theme',
        content_types = (NewsletterTheme.NewsletterTheme,),
        permission = PNLPermissions.AddNewsletterTheme,
        extra_constructors = (NewsletterTheme.addNewsletterTheme,),
        fti = NewsletterTheme.NewsletterTheme.factory_type_information).initialize(context)

    ContentInit(
        'Plone Gazette resources',
        content_types = contentClasses,
        permission = permissions.AddPortalContent,
        extra_constructors = contentConstructors,
        fti = factoryTypes).initialize(context)

    registerIcon(NewsletterTheme.NewsletterTheme, 'skins/PloneGazette/NewsletterTheme.gif', globals())
    registerIcon(Newsletter.Newsletter, 'skins/PloneGazette/Newsletter.gif', globals())
    registerIcon(Subscriber.Subscriber, 'skins/PloneGazette/Subscriber.gif', globals())

    # Archetypes init
    content_types, constructors, ftis = process_types(listTypes(PROJECTNAME), PROJECTNAME)

    ContentInit(
        PROJECTNAME + ' Content',
        content_types = content_types,
        permission = permissions.AddPortalContent,
        extra_constructors = constructors,
        fti = ftis,).initialize(context)
