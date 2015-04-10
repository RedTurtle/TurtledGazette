#
# $Id: NewsletterTheme.py 252613 2013-10-02 15:34:06Z keul $
#

"""NewsletterCentral class"""

# Standard Python imports
import string
import random
import csv
import os

import email.Message
import email.Utils
from email.Header import Header

# Zope core imports
from zope.interface import implements
from zope.i18n import translate
import transaction
from Globals import InitializeClass
from AccessControl import getSecurityManager, ClassSecurityInfo
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from OFS import Folder
from Products.PageTemplates import Expressions
try:
    from zope.tales.tales import CompilerError
except ImportError:
    from Products.PageTemplates.TALES import CompilerError

# CMF/Plone imports
from Products.CMFCore import permissions
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault import SkinnedFolder
from Products.CMFPlone.utils import base_hasattr, safe_unicode

# Product specific imports
from PNLPermissions import *
from PNLUtils import ownerOfObject
from PNLUtils import checkMailAddress
from PNLBase import PNLContentBase
from Products.PloneGazette.catalog import manage_addSubscribersCatalog
from Products.PloneGazette.config import PG_CATALOG
from Products.PloneGazette.interfaces import INewsletterTheme

try:
    from zope.structuredtext.html import HTML
except:
    from Products.CMFCore.utils import format_stx
    HTML = False

from Products.PloneGazette import PloneGazetteFactory as _
from zope.component import getMultiAdapter
import logging
logger = logging.getLogger('PloneGazette')

#################
## The factory ##
#################
def addNewsletterTheme(self, id, title = '', REQUEST = {}):
    """
    Factory method for a NewsletterTheme object
    """
    obj = NewsletterTheme(id, title)
    self._setObject(id, obj)
    getattr(self, id)._post_init()
    if REQUEST.has_key('RESPONSE'):
        return REQUEST.RESPONSE.redirect('manage_main')
    return

########################################
## The NewsletterCentral content type ##
########################################

class NewsletterTheme(SkinnedFolder.SkinnedFolder, DefaultDublinCoreImpl, PNLContentBase):
    """NewsletterTheme class
    """
    ########################################
    ## Registration info for portal_types ##
    ########################################
    implements(INewsletterTheme)

    factory_type_information = {
        'id': 'NewsletterTheme',
        'portal_type': 'NewsletterTheme',
        'meta_type': 'NewsletterTheme',
        'description': 'Manage your newsletters with this',
        'content_icon': 'NewsletterTheme.gif',
        'product': 'PloneGazette',
        'factory': 'addNewsletterTheme',
        'immediate_view': 'NewsletterTheme_view',
        'filter_content_types': 1,
        'allowed_content_types': ('Newsletter', 'Subscriber', 'NewsletterBTree'),
        'actions': (
            {'id': 'view',
             'name': 'View',
             'action': 'string:${object_url}',
             'permissions': (permissions.View,)},

            {'id' : 'infos',
             'name' : 'Informations',
             'action' : 'string:${object_url}/subscribers_infos',
             'permissions' : (ChangeNewsletterTheme,)},

            {'id': 'edit',
             'name': 'Edit',
             'action': 'string:${object_url}/edit',
             'permissions': (ChangeNewsletterTheme,)},

            {'id' : 'NewsletterTheme_importForm',
             'name' : 'Import',
             'action' : 'string:${object_url}/NewsletterTheme_importForm',
             'permissions' : (ChangeNewsletterTheme,)},
            ),
        'aliases' : {
                '(Default)'  : 'NewsletterTheme_view',
                'view'       : 'NewsletterTheme_view',
                'index.html' : '',
                'edit'       : 'NewsletterTheme_editForm',
                'properties' : 'base_metadata',
                'sharing'    : 'folder_localrole_form',
        },
        }

    ###########################
    ## Basic class behaviour ##
    ###########################

    meta_type = portal_type = 'NewsletterTheme'

    manage_options = Folder.Folder.manage_options + CMFCatalogAware.manage_options

    # Standard security settings
    security = ClassSecurityInfo()
    security.declareObjectProtected(permissions.View)

    _csv_import_log = ''
    _new_object = False
    alternative_portal_url = None
    _stx_level = 1
    
    cooked_text = text = text_format = ''
    
    _format_list = [{'id': 'HTML', 'label': _('HTML')},
                    {'id': 'Text', 'label': _('Text')}]

    # Dummy permission instanciation.
    # Permissions has to be "dummily" instanciated in order to be reachable for the factory_type_information structure.
    # In order to be very clear, we just declare each and every permission we use in this product.
    # security.declareProtected(ChangeNewsletterTheme, "dummyMethod_editPermission")

    # Init method
    def __init__(self, id, title=''):
        """__init__(self, id, title='')"""
        # NOTA : We shouldn't call parent's __init__ method as it would link to PortalFolder.__init__ and this
        # method sets 'self.id' and 'self.title' which is unuseful for us.

        DefaultDublinCoreImpl.__init__(self)
        self._internalVersion = 2
        self._subscribersCount = 0
        self.id = id
        self.default_format = 'HTML'
        self.title = title
        self.description = ''
        self.testEmail = ''
        self.authorEmail = ''
        self.replyto = ''
        self.notify = False
        self.renderTemplate = ''
        self._v_renderTemplate = None
        self.extraRecipients = ''
        self._v_extraRecipients = None
        self.subscriber_folder_id = ''
        self._new_object = True
        self.alternative_portal_url = None
        self.text_format=''
        self.text=''
        self.activationMailSubject = ''
        self.activationMailTemplate = ''
        self.newsletterFooter = ''

    @property
    def _scatalog(self):
        return getattr(self, PG_CATALOG, None)

    security.declarePrivate('_post_init')
    def _post_init(self):
        """Post-init method (that is, method that is called AFTER the class has been set into the ZODB)
        """
        self.activationMailSubject = translate(_("Please activate your newsletter account"), context=self.REQUEST)
        self.activationMailTemplate = translate(_('default_activation_mail_template',
                                                  default=u"""Dear subscriber,

We have received and recorded your newsletter subscription.
You must now activate your account to receive our newsletters.
To do this, just browse to this URL...
%(url)s
Then you'll receive our next newsletters at %(email)s

PLEASE DON'T REPLY TO THIS MAIL"""), context=self.REQUEST)
        self.newsletterFooter = translate(_('default_newsletter_footer',
                                            default=u"""Thank you for subscribing to this newsletter.<br />
You can <a href="%(url)s">change your preferences</a> at any time.
"""), context=self.REQUEST)
        self.invokeFactory('NewsletterBTree', 'subscribers',
                           title=translate(_('Subscribers'), context=self.REQUEST))
        getattr(self, 'subscribers').indexObject()
        self.indexObject()
        self._initCatalog()
        return

    security.declarePublic('get_available_formats')
    def get_available_formats(self):
        # we define a setter because in complex situation you can have "private" newsletter themes
        formats = []
        for f in self._format_list:
            formats.append(dict(id=f['id'], label=translate(f['label'], context=self.REQUEST)))
        return formats

    def _edit(self, text, text_format=''):
        level = self._stx_level
        if not text_format:
            text_format = self.text_format

        if self.text_format:
            self.text_format = text_format
        if text_format == 'html':
            self.text = self.cooked_text = text
        elif text_format == 'plain':
            self.text = text
            self.cooked_text = html_quote(text).replace('\n', '<br />')
        else:
            if HTML:
                html_renderer = HTML()
                self.cooked_text = html_renderer(text=text, level=level)
            else:
                self.cooked_text = format_stx(text=text, level=level)
            self.text = text

    security.declareProtected(ChangeNewsletterTheme, 'edit')
    def edit(self, title='',  default_format='', testEmail='', authorEmail='', replyto='',
             activationMailSubject='', activationMailTemplate='', newsletterFooter='', notify=False,
             renderTemplate='', extraRecipients='', subscriber_folder_id='',
             alternative_portal_url=None, text_format='', text=''):
        """Changes values"""
        self.title = title.strip()
        self.default_format = default_format
        self.testEmail = testEmail.strip()
        self.authorEmail = authorEmail.strip()
        self.replyto = replyto.strip()
        self.activationMailSubject = activationMailSubject.strip()
        self.activationMailTemplate = activationMailTemplate.strip()
        self.newsletterFooter = newsletterFooter.strip()
        self.notify = notify
        self.renderTemplate = renderTemplate.strip()
        self.extraRecipients = extraRecipients.strip()
        self.getRenderTemplate(recompile=1)
        self.getExtraRecipients(recompile=1)

        if text_format:
            self.setFormat(text_format)
        if text:
            self._edit(text=text, text_format=text_format)

        if self._new_object and title:
            plone_tool = getToolByName(self, 'plone_utils')
            newid = plone_tool.normalizeString(title)
            parent = self.aq_parent
            if newid not in parent.objectIds():
                transaction.savepoint(optimistic=True)
                self._v_cp_refs = 1
                parent.manage_renameObject(self.id, newid)
                self._setId(newid)

        self._new_object=False

        self.reindexObject()
        self.subscriber_folder_id = subscriber_folder_id
        self.alternative_portal_url = alternative_portal_url

    security.declareProtected(permissions.View, 'CookedBody')
    def CookedBody(self, stx_level=None, setLevel=0):
        """
        """
        if (self.text_format == 'html' or self.text_format == 'plain'
            or (stx_level is None)
            or (stx_level == self._stx_level)):
            return self.cooked_text
        else:
            if HTML:
                html_renderer = HTML()
                cooked = html_renderer(self.text, stx_level)
            else:
                cooked = format_stx(self.text, stx_level)
            if setLevel:
                self._stx_level = stx_level
                self.cooked_text = cooked
            return cooked

    security.declareProtected(permissions.View, 'Format')
    def Format(self):
        """
        """
        if self.text_format == 'html':
            return 'text/html'
        else:
            return 'text/plain'

    security.declareProtected(permissions.ModifyPortalContent, 'setFormat')
    def setFormat(self, format):
        """
        """
        value = str(format)
        if value == 'text/html' or value == 'html':
            self.text_format = 'html'
        elif value == 'text/plain':
            if self.text_format not in ('structured-text', 'plain'):
                self.text_format = 'structured-text'
        elif value =='plain':
            self.text_format = 'plain'
        else:
            self.text_format = 'structured-text'

    security.declareProtected(permissions.View, 'getNewsletters')
    def getNewsletters(self):
        """
        Return the "Newsletter" objects
        """
        mtool = getToolByName(self, 'portal_membership')
        checkPermission = mtool.checkPermission
        result = [ x for x in self.objectValues('Newsletter') if checkPermission('View', x)]
        return result

    security.declarePublic('createSubscriberObject')
    def createSubscriberObject(self, id):
        """
        """

        target_folder = self.getSubscriberFolder()
        if target_folder is None:
            target_folder = self

        target_folder.invokeFactory(self.getSubscriberTypes()[0], id)
        obj = getattr(target_folder, id)
        return obj

    security.declarePublic('getSubscriberFolder')
    def getSubscriberFolder(self):
        """
        Return the folder where subscriber objects will be create.
        It will be a "NewsletterBTree" if it exist, or the "NewsletterTheme" itself.
        """
        target_folder = None
        subscriber_folder_id = self.subscriber_folder_id
        if subscriber_folder_id and subscriber_folder_id in self.objectIds('NewsletterBTree'):
            target_folder = getattr(self, subscriber_folder_id)

        return target_folder

    security.declarePublic('getSubscriberById')
    def getSubscriberById(self, id):
        """Obtain a subscriber object from its id"""
        subscriber = None
        result = self._scatalog(id=id)
        if result:
            path = result[0].getPath()
            subscriber = self.unrestrictedTraverse(path)

        return subscriber

    security.declareProtected(permissions.ModifyPortalContent, 'activateAllSubscribers')
    def activateAllSubscribers(self, csv_string=None):
        """Activate all subscribers of this theme.
        You can provide a string in a CSV format (compatible with CSV generated by PloneGazette) to
        activate only users that are active on this CSV.
        """
        # if CSV provided
        if csv_string:
            lines = csv_string.split("\n")
            csv_users = {}
            for line in lines[1:]:
                if not line:
                    continue # skip empty lines
                email, active, format = line.split(',')
                csv_users[email] = {'active': active=='1', 'format': format}
        # activation
        results = self._scatalog()
        for x in results:
            subscriber = x.getObject()
            # if csv_string, enable any active users in the CSV
            if csv_string and (subscriber.email not in csv_users.keys() or \
                    (subscriber.email in csv_users.keys() and not csv_users[subscriber.email]['active']) ):
                continue
            subscriber.active = True
            subscriber.reindexObject('active')
        self.REQUEST.RESPONSE.redirect(self.absolute_url()+'/subscribers_infos')

    security.declareProtected(permissions.ModifyPortalContent, 'subscribers_status_csv')
    def subscribers_status_csv(self):
        """Obtain a CSV with infos for subscribers
        email,active,format
        ...
        """
        response = self.REQUEST.RESPONSE
        response.setHeader('Content-Type', 'text/csv')
        response.setHeader("Content-Disposition","inline; filename=subscribers.csv") 
        response.write('email,active,format\n')
        results = self._scatalog()
        for x in results:
            subscriber = x.getObject()
            response.write('%s,%s,%s\n' % (subscriber.email, subscriber.active and 1 or 0, subscriber.format))


    ##################
    ## UI handlings ##
    ##################

    security.declarePrivate('_getRandomIdForSubscriber')
    def _getRandomIdForSubscriber(self):
        """
        """
        validChars = [c for c in string.letters + string.digits if ord(c) < 128]
        newId = "%05d" % self._subscribersCount + ''.join([random.choice(validChars) for x in range(5)])
        return newId

    def getSubscriberTypes(self):
        '''return all possible subscriber portal types'''
        return ['Subscriber']

    security.declarePublic('subscribeFormProcess')
    def subscribeFormProcess(self, REQUEST=None):
        """Handles NewsletterTheme_subscribeForm"""

        if REQUEST is None:
            REQUEST = self.REQUEST
        errors = {}
        data = {}
        charset = self.ploneCharset()
        if REQUEST.form.has_key('email'):
            # Form submitted
            emailaddress = REQUEST.form.get('email', '').strip()
            data['email'] = emailaddress

            if not emailaddress:
                errors['email'] = translate(_('input_required',
                                              default=u'Input is required but no input given'),
                                            context=REQUEST)
                return data, errors

            if not checkMailAddress(self, emailaddress):
                errors['email'] = translate(_('invalid_email_address',
                                              default=u'This is not a valid mail address'),
                                            context=REQUEST)
                return data, errors
            format = REQUEST.form.get('format', self.default_format)
            data['format'] = format
            if self.alreadySubscriber(emailaddress):
                errors['email'] = translate(_('already_subscribed',
                                              default=u'There is already a subscriber with this address'),
                                            context=REQUEST)
            if not errors:
                # Creating the new account
                self._subscribersCount += 1
                newId = self._getRandomIdForSubscriber()
                # Continue method as owner of this object for "invokeFactory" security checkings.
                # (creating new objects through invokeFactory is not possible as anonymous because an owner is required)
                oldSecurityManager = getSecurityManager()
                newSecurityManager(REQUEST, ownerOfObject(self))
                newSubscriber = self.createSubscriberObject(newId)
                newSubscriber.edit(format=format, active=0, email=emailaddress)
                setSecurityManager(oldSecurityManager)

                # Make URL for editing this object
                subscriberEditUrl = newSubscriber.absolute_url() + '/Subscriber_editForm'   # :( FIXME
                #actions_tool = getToolByName(self, 'portal_actions')
                #actions = actions_tool.listFilteredActionsFor(object=newSubscriber)
                #subscriberEditUrl = [action['url'] for action in actions['object']
                #                     if action['id'] == 'edit'][0]

                # Make and send the activation mail
                """
                mailBody = ("From: %s\r\n"
                            "To: %s\r\n"
                            "Content-Type: text/plain; charset=%s\r\n"
                            "Subject: %s\r\n\r\n")
                mailBody = mailBody % (self.authorEmail, data['email'],
                                       self.ploneCharset(), self.activationMailSubject)
                mailBody += self.activationMailTemplate % {'url': self.absolute_url() + '?active=%s&format=%s' % (newId, format), 'email': emailaddress}

                """
                
                mailMsg=email.Message.Message()
                mailMsg["To"]=data['email']
                mailMsg["From"]=self.authorEmail
                mailMsg["Subject"]=str(Header(safe_unicode(self.activationMailSubject), 'utf8'))
                mailMsg["Date"]=email.Utils.formatdate(localtime=1)
                mailMsg["Message-ID"]=email.Utils.make_msgid()
                mailMsg["Mime-version"]="1.0"

                bodyText = self.activationMailTemplate % {'url': self.absolute_url() + '?active=%s&format=%s' % (newId, format), 'email': emailaddress}
                mailMsg["Content-type"]="text/plain"
                mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
                #mailMsg.preamble="Mime message\n"
                mailMsg.epilogue="\n" # To ensure that message ends with newline

                try:
                    self.sendmail(self.authorEmail, (emailaddress,), mailMsg, subject = mailMsg['subject'])
                except Exception, e:
                    # The email could not be sent, probably the specified address doesn't exist
                    errors['email'] = translate('Email could not be sent. Error message is: ${error}', mapping={'error':str(e)}, context=self)
                    data['email'] = emailaddress
                    data['format'] = self.default_format
                    transaction.abort()
                    return data, errors

                if self.notify:
                    # Notify the NewsletterTheme owner
                    """mailBody = ("From: %s\r\n"
                                "To: %s\r\n"
                                "Content-Type: text/plain; charset=%s\r\n"
                                "Subject: %s : %s\r\n\r\n"
                                "%s\n%s")
                    mailBody = mailBody % (self.authorEmail, self.testEmail,
                                           self.ploneCharset(),
                                           self.title,
                                           translate("Newsletter new subscriber", domain='plonegazette', context=REQUEST),
                                           translate("See the new account at...", domain='plonegazette', context=REQUEST),
                                           subscriberEditUrl)
                    subject = "Subject: %s : %s" % (self.title,
                                           translate("Newsletter new subscriber", domain='plonegazette', context=REQUEST))
                    """
                    subject = "%s : %s" % (self.title,
                                           translate("Newsletter new subscriber", domain='plonegazette', context=REQUEST))
                    mailMsg=email.Message.Message()
                    mailMsg["To"]=self.testEmail
                    mailMsg["From"]=self.authorEmail
                    mailMsg["Subject"]=str(Header(safe_unicode(subject), 'utf8'))
                    mailMsg["Date"]=email.Utils.formatdate(localtime=1)
                    mailMsg["Message-ID"]=email.Utils.make_msgid()
                    mailMsg["Mime-version"]="1.0"

                    bodyText = "%s\n%s" % (translate("See the new account at...", context=REQUEST, domain='plonegazette'),
                                           subscriberEditUrl)
                    mailMsg["Content-type"]="text/plain"
                    #mailMsg.set_charset(charset)
                    mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
                    #mailMsg.preamble="Mime message\n"
                    mailMsg.epilogue="\n" # To ensure that message ends with newline

                    self.sendmail(self.authorEmail, (self.testEmail,), mailMsg, subject = mailMsg['subject'])
                data['success'] = 1
        else:
            # First entry in the form
            data['email'] = ''
            data['format'] = self.default_format
        return data, errors

    security.declarePublic('unSubscribe')
    def unSubscribe(self, subscriber_id, REQUEST=None):
        """The subscriber clicked the Unsubscribe button
        """
        subscriber = self.getSubscriberById(subscriber_id)
        mtool = getToolByName(self, 'portal_membership')
        checkPermission = mtool.checkPermission
        can_access_theme = checkPermission(permissions.View, self)
        newSecurityManager(REQUEST, ownerOfObject(self))
        if subscriber is not None:
            parent = subscriber.aq_parent
            parent.manage_delObjects([subscriber_id,])

        if REQUEST is not None:
            # Check if we have access to the newsletter theme
            if can_access_theme:
                REQUEST.RESPONSE.redirect(self.absolute_url() + '/NewsletterTheme_unsubscribed')
            else:
                portal_url = getToolByName(self, 'portal_url')()
                plone_utils = getToolByName(self, 'plone_utils')
                plone_utils.addPortalMessage(_('unsubscribe_success_message',
                                               default=u"You have been successfully unsubscribed from this newsletter."))
                REQUEST.RESPONSE.redirect(portal_url)
        return

    def checkMailAddress(self, mail):
        return  checkMailAddress(self,mail)


    def checkTalExpressions(self, talExpressions, state=None, errors=None):
        """
        Check TALES expressions for edit_form validation
        """
        talEngine = Expressions.getEngine()
        for fieldId, value in talExpressions:
            if not value:
                continue
            try:
                talEngine.compile(value)
            except CompilerError, e:
                msg = _('TALES compilation error: ${error}', mapping={'error':str(e)})
                if state is not None:
                    state.setError(fieldId, msg)
                if errors is not None:
                    errors[fieldId] = msg
        if state is not None:
            return state
        elif errors is not None:
            return errors
        return

    ##############
    ## Utilities #
    ##############

    security.declarePublic('alreadySubscriber')
    def alreadySubscriber(self, email):
        """Checks wether email is in the subscribers
        """
        catalog = self._scatalog
        return not not catalog(email=email)

    security.declarePublic('sendmail')
    def sendmail(self, mailfrom, mailto, mailBody, subject = None):
        """"""
        portal_properties = getToolByName(self, 'portal_properties')
        mail_host_id = getattr(portal_properties.site_properties, 'plonegazette_mailhost', 'MailHost')
        mail_host = getattr(self, mail_host_id, None)
        try:
            mail_host.send(str(mailBody), mailto, mailfrom, subject=subject)
        except AttributeError:
            mail_host.secureSend(mailBody, mailto, mailfrom, subject=subject)

    security.declarePublic('getRenderTemplate')
    def getRenderTemplate(self, recompile=0):
        """Returns the template that renders the HTML newsletter
        recompile=1 -> recompile TAL expression"""

        talEngine = Expressions.getEngine()
        try:
            self._v_renderTemplate
        except AttributeError, e:
            recompile = 1
        if recompile:
            if self.renderTemplate:
                self._v_renderTemplate = talEngine.compile(self.renderTemplate)
            else:
                self._v_renderTemplate = None
        if self._v_renderTemplate:
            data = {'here': self}
            template = self._v_renderTemplate(talEngine.getContext(data))
        else:
            template = getattr(self, 'newsletter_mua_formatter')
        return template

    security.declarePublic('getExtraRecipients')
    def getExtraRecipients(self, recompile=0):
        """Provides a TALES compiled extra list of recipients
        recompile=1 -> recompile TAL expression"""

        talEngine = Expressions.getEngine()
        try:
            self._v_extraRecipients
        except AttributeError, e:
            recompile = 1
        if recompile:
            # Not used since last cache extraction
            if self.extraRecipients:
                self._v_extraRecipients = talEngine.compile(self.extraRecipients)
            else:
                self._v_extraRecipients = None
        if self._v_extraRecipients:
            data = {'here': self}
            return self._v_extraRecipients(talEngine.getContext(data))()
        else:
            return []

    security.declareProtected(ChangeNewsletterTheme, 'mailingInfos')
    def mailingInfos(self, active=True):
        """Return mailing info from all subscribers.
        Default: return active subcribers
        """

        subscribers = self.getSubscribers()
        mi = []
        for s in subscribers:
            if (active and s.active) or (not active and not s.active):
                mi.append((s.email, s.format, s.getURL() + '/Subscriber_editForm'))
        return mi

    security.declarePrivate('_getStatsForSubscriber')
    def _getStatsForSubscriber(self, subscriber, stats, listing):
        """
        """
        format = subscriber.format
        active = subscriber.active
        if format == 'HTML':
            if active:
                stats['htmlactive'] += 1
            else:
                stats['htmlinactive'] += 1
        else:
            if active:
                stats['plaintextactive'] += 1
            else:
                stats['plaintextinactive'] += 1

        # getURL = brain
        url = getattr(subscriber, 'getURL', subscriber.absolute_url)()
        # the same dict is generated in newsletterbtree_view browser class, so change in this
        # dict has to be propagated to the newsletterbtree view class too.
        listing.append({'email' : subscriber.email, 'id':subscriber.id, 'url' : url, 'active' : active, 'format' : format})

        return (stats, listing)

    security.declareProtected(ChangeNewsletterTheme, 'subscriberStats')
    def subscriberStats(self):
        """Returns a dict with statistics about subscribers"""
        def checkfilter(subscriber, email, active, format):
            if email!='':
                emailOk = email in subscriber.email
            else:
                emailOk = True
            if active!=-1:
                activeOk = active==subscriber.active
            else:
                activeOk = True
            if format!='':
                formatOk = format in subscriber.format
            else:
                formatOk = True
            return emailOk and activeOk and formatOk


        listing = []
        stats = {'total': 0,
                 'htmlactive': 0,
                 'plaintextactive': 0,
                 'htmlinactive': 0,
                 'plaintextinactive': 0,
                 'totalhtml': 0,
                 'totalplaintext': 0,
                 'totalactive': 0,
                 'totalinactive': 0}

        filterEmail = self.REQUEST.get('email', '')
        filterActive = int(self.REQUEST.get('active', -1))
        filterFormat = self.REQUEST.get('format', '')

        subscribers = self.getSubscribers()
        stats['total'] = stats['total'] + len(subscribers)
        for subscriber in subscribers:
            if checkfilter(subscriber, filterEmail, filterActive, filterFormat):
                stats, listing = self._getStatsForSubscriber(subscriber, stats, listing)

        stats['totalhtml'] = stats['htmlactive'] + stats['htmlinactive']
        stats['totalplaintext'] = stats['plaintextactive'] + stats['plaintextinactive']
        stats['totalactive'] = stats['htmlactive'] + stats['plaintextactive']
        stats['totalinactive'] = stats['htmlinactive'] + stats['plaintextinactive']
        return (stats, listing)

    security.declareProtected(ChangeNewsletterTheme, 'extraRecipientStats')
    def extraRecipientStats(self):
        """Returns a dict with statistics about extra recipients"""
        extraRecipients = self.getExtraRecipients()
        stats = {'total': len(extraRecipients),
                 'html': 0,
                 'plaintext': 0}
        for mail, html, editurl in extraRecipients:
            if html == 'HTML':
                stats['html'] += 1
            else:
                stats['plaintext'] += 1
        return stats

    def getTemplateStylesheet(self, css_name="base_newsletter_styles.css"):
        """
        Try to get a css file (in portal_skins), parse it, and return the styles to the template.
        """
        portal_state = getMultiAdapter((self, self.REQUEST), name=u'plone_portal_state')
        portal = portal_state.portal()
        portal_url = portal_state.portal_url()
        try:
            css = portal.unrestrictedTraverse("%s/%s" % (portal.getId(), css_name))
        except KeyError:
            logger.error("Newsletter Styles. CSS %s not found. Is it available in portal_skins?" % css_name)
            return ""
        try:
            css_str = str(css)
            #in the css we can use a dynamic variable for portal_url
            return css_str.replace("${portal_url}", portal_url)
        except:
            logger.error("Invalid CSS file: %s. Cannot convert to string" % css_name)
            return ""

    ############################
    ## portal_catalog support ##
    ############################

    security.declarePublic('SearchableText')
    def SearchableText(self):
        return self.title + self.description.encode('utf-8') + self.text

    ##########################
    ## CSV import features
    #########################

    security.declareProtected(ChangeNewsletterTheme, 'createSubscribersFromCSV')
    def createSubscribersFromCSV(self, file_upload):
        """
        Create all subscribers objects from csv file uploaded
        """

        # Reset old log
        self._csv_import_log = ''

        filename = file_upload.filename
        filedatas = file_upload.read()
        var_directory = self.Control_Panel.getCLIENT_HOME()

        dialect = csv.excel

        # first, create a temp file on file system
        self._createTempFile(var_directory, filename, filedatas)

        # open temp csv file
        reader = csv.DictReader(open('%s/%s' % (var_directory, filename)), ['email', 'active', 'format'], dialect=dialect)

        # get target folder for subscribers object, or create it if not exist
        subscriber_folder = self.getSubscriberFolder()
        if subscriber_folder is None:
            self.invokeFactory('NewsletterBTree', 'subscribers')
            self.subscriber_folder_id = 'subscribers'
            subscriber_folder = getattr(self, 'subscribers')

        # remove headers
        first_row = reader.next()
        if first_row['email']!='email':
            return _('csv_headers_error',
                     default=u"You must add headers to the csv file : email, active, format ('email' at least)")

        # for each row, create a subscriber object
        default_format = self.default_format
        k = 0
        already_used = []
        not_valid = []
        for row in reader:

            # get the field value, or the default value
            if row['active']=='1':
                active = True
            elif row['active']=='0':
                active = False
            else:
                active = False

            if row['format']:
                if row['format'].lower()=='html':
                    format = 'HTML'
                elif row['format'].lower()=='text':
                    format = 'Text'
                else:
                    format = default_format
            else:
                format = default_format

            email = row['email']
            email = email.strip()

            # check mail address validity
            if not checkMailAddress(self,email):
                not_valid.append(email)
            else:

                # check if subscriber already exist
                if self.alreadySubscriber(email):
                    already_used.append(email)
                else:
                    newId = self._getRandomIdForSubscriber()
                    subscriber = self.createSubscriberObject(newId)

                    subscriber.edit(format=format, active=active, email=email)
                    k += 1
                    self._subscribersCount += 1

        # remove temp csv file
        os.remove('%s/%s' % (var_directory, filename))

        self._logCSVImportResult(not_valid, already_used)

        msg = _('csv_import_report',
                default=u"""${count_created} subscribers created.
${count_already_there} users were already subscriber on this newsletter theme.
${count_not_valid} emails were not valid.""",
                mapping={'count_created': k,
                         'count_already_there': len(already_used),
                         'count_not_valid': len(not_valid)})
        return msg

    security.declareProtected(ChangeNewsletterTheme, 'getCSVImportLogs')
    def getCSVImportLogs(self):
        """
        """
        return self._csv_import_log.strip()

    security.declarePrivate('_logCSVImportResult')
    def _logCSVImportResult(self, not_valid, already_used):
        """
        """
        result = ''
        if len(already_used):
            result += '<h2>Already subscribed</h2>'
            result += '<p>'
            result += '<br />'.join(already_used)
            result += '</p>'
        if len(not_valid):
            result += '<h2>Not valid emails</h2>'
            result += '<p>'
            result += '<br />'.join(not_valid)
            result += '</p>'
        self._csv_import_log = result
        return

    security.declarePrivate('_createTempFile')
    def _createTempFile(self, home, filename, filedatas):
        """
        Create a temp file inside zope "var" directory
        """
        temp_file = open('%s/%s' % (home, filename), 'w')
        temp_file.write(filedatas)
        temp_file.close()
        return

    # do not allow anonymous to list all subscribers
    security.declareProtected(ChangeNewsletterTheme, 'getSubscribers')
    def getSubscribers(self, full_objects=False, currentLargeFolder=True, path=None):
        # get all items from catalog (all subscribers)
        cat = getattr(self, PG_CATALOG, None)
        if cat is None:
            return []
        filters = {}
        if path:
            filters['path'] = path
        elif currentLargeFolder:
            filters['path'] = '/'.join(self.getPhysicalPath()) + '/' + self.subscriber_folder_id 
        result = cat(**filters)
        if full_objects:
            result = [x.getObject() for x in result]
        return result

    def _initCatalog(self):
        """Add subscribers catalog"""

        if not base_hasattr(self, PG_CATALOG):
            add_catalog = manage_addSubscribersCatalog
            add_catalog(self)

        catalog = getattr(self, PG_CATALOG)
        catalog.refreshCatalog()
        return catalog

    security.declareProtected(permissions.ListFolderContents, 'listFolderContents')
    def listFolderContents( self, spec=None, contentFilter=None, suppressHiddenFiles=0 ):
        """
        Hook around 'contentValues' to let 'folder_contents'
        be protected.  Duplicating skip_unauthorized behavior of dtml-in.

        In the world of Plone we do not want to show objects that begin with a .
        So we have added a simply check.  We probably dont want to raise an
        Exception as much as we want to not show it.

        """
        ctool = getToolByName(self, 'portal_catalog')
        terms = dict(path={'query':'/'.join(self.getPhysicalPath()), 'depth':1},
                           sort_on='sortable_title')
        terms.update(contentFilter)
        return ctool(**terms)

    security.declareProtected(permissions.ListFolderContents, 'listLargeFolders')
    def listLargeFolders(self):
        """
        Show all contained NewsletterBTree
        """
        return [{'title': x.Title,
                 'id': x.id} for x in self.listFolderContents(contentFilter={'portal_type': 'NewsletterBTree'})]

    # For plone 2.1+ to show unindexed content
    security.declareProtected(ChangeNewsletterTheme, 'getFolderContents')
    def getFolderContents(self, contentFilter=None, batch=False, b_size=100, full_objects=False):
        """Override getFolderContents to show all objects"""
        contents = self.listFolderContents(contentFilter=contentFilter)
        if batch:
            from Products.CMFPlone import Batch
            b_start = self.REQUEST.get('b_start', 0)
            batch = Batch(contents, b_size, int(b_start), orphan=0)
            return batch
        return contents

# Class instanciation
InitializeClass(NewsletterTheme)
