# -*- coding: utf-8 -*-

import re
import traceback
import cStringIO
import email.Message
import email.Utils
import StringIO
import transaction
import logging

from AccessControl import ClassSecurityInfo
from AccessControl.SpecialUsers import nobody
from AccessControl.requestmethod import postonly
from DateTime import DateTime
from DocumentTemplate.DT_Util import html_quote
from Globals import InitializeClass
from OFS import Folder
from email.Header import Header
from email.mime.base import MIMEBase
from email import encoders
from PNLBase import PNLContentBase
from PNLPermissions import *
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.permissions import ListFolderContents
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFPlone.utils import safe_unicode
from Products.PloneGazette import PloneGazetteFactory as _
from Products.PloneGazette.PNLUtils import sizeof_fmt
from elementtree import ElementTree
from elementtree import HTMLTreeBuilder
from plone.app.blob.interfaces import IBlobbable
from plone.app.blob.field import BlobWrapper
from plone.app.blob.field import ReuseBlob
from urlparse import urlparse
from zope.i18n import translate

try:
    from zope.structuredtext.html import HTML as format_stx
except:
    from Products.CMFCore.utils import format_stx



logger = logging.getLogger('PloneGazette')

#################
## The factory ##
#################

def addNewsletter(self, id, title = '', REQUEST = {}):
    """
    Factory method for a Newsletter object
    """
    obj = Newsletter(id, title)
    self._setObject(id, obj)
    getattr(self, id)._post_init()
    if REQUEST.has_key('RESPONSE'):
        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')

#################################
## The Newsletter content type ##
#################################

lynx_file_url = re.compile(r'file://localhost[^%]+%\(url\)s')

class Newsletter(PortalContent, DefaultDublinCoreImpl, PNLContentBase):
    """Newsletter class"""

    ########################################
    ## Registration info for portal_types ##
    ########################################

    factory_type_information = {
        'id': 'Newsletter',
        'portal_type': 'Newsletter',
        'meta_type': 'Newsletter',
        'description': 'A newletter (has no sense oudside a NewsletterTheme object)',
        'content_icon': 'Newsletter.gif',
        'product': 'PloneGazette',
        'factory': 'addNewsletter',
        'immediate_view': 'folder_listing',
        'global_allow': 0,
        'filter_content_types': 1,
        'allowed_content_types': ('Section', 'Topic', 'NewsletterReference', 'NewsletterRichReference'),
        'actions': (
            {
                'id': 'view',
                'name': 'View',
                'action': 'string:${object_url}',
                'permissions': (View, ),
                'category': 'object'
                },
            {
                'id': 'edit',
                'name': 'Edit',
                'action': 'string:${object_url}/edit',
                'permissions': (ChangeNewsletter,),
                'category': 'object'
                },
            {
                'id': 'test',
                'name': 'Test',
                'action': 'string:${object_url}/Newsletter_testForm',
                'permissions': (ChangeNewsletter,),
                'category': 'object'
                },

            {
                'id': 'send',
                'name': 'Send',
                'action': 'string:${object_url}/Newsletter_sendForm',
                'permissions': (ChangeNewsletter,),
                'category': 'object'
                },
            ),
            'aliases' : {
                '(Default)'  : 'Newsletter_view',
                'view'       : 'Newsletter_view',
                'index.html' : '',
                'edit'       : 'Newsletter_editForm',
                'properties' : 'base_metadata',
                'sharing'    : 'folder_localrole_form',
            },
        }

    ###########################
    ## Basic class behaviour ##
    ###########################

    meta_type = factory_type_information['meta_type']
    manage_options = Folder.Folder.manage_options

    # Standard security settings
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)
    #security.declareProtected(ChangeNewsletter, "dummyMethod_editPermission")

    _stx_level = 1
    cooked_text = text = text_format = ''
    _new_object = False
    _dynamic_content = None

    # Init method
    security.declarePrivate('__init__')
    def __init__(self, id, title='', description='', text_format='', text='', dateEmitted=None,
                 attachment=None):
        """__init__(self, id, title='')"""

        DefaultDublinCoreImpl.__init__(self)
        self.id = id
        self.title = title
        self.description = description
        self._edit(text=text, text_format=text_format)
        self.setFormat(text_format)
        self.dateEmitted = dateEmitted
        self.attachment=attachment
        self._new_object=True
        self._dynamic_content = None
        return

    security.declarePrivate('_post_init')
    def _post_init(self):
        """
        _post_init(self) => Post-init method (that is, method that is called AFTER the class has been set into the ZODB)
        """

        self.indexObject()
        return

    #############################
    ## Content editing methods ##
    #############################

    def _edit(self, text, text_format=''):
        """
        """
        level = self._stx_level
        if not text_format:
            text_format = self.text_format

        if self.text_format:
            self.text_format = text_format
        if text_format == 'html' or text_format == 'text/html':
            self.text = self.cooked_text = text
        elif text_format == 'plain' or text_format == 'text/plain':
            self.text = text
            self.cooked_text = html_quote(text).replace('\n', '<br />')
        else:
            self.cooked_text = format_stx(text=text, level=level)
            self.text = text

    # Edit method (change this to suit your needs)
    # This edit method should only change attributes that are neither 'id' or metadatas.
    security.declareProtected(ChangeNewsletter, 'edit')
    def edit(self, title='', text='', dateEmitted=None, text_format='', attachment=None):
        """
        edit(self, text = '') => object modification method
        """
        # Change attributes
        if title:
            self.title = title
        if not dateEmitted:
            # if dateEmitted is cleared, clear dynamic content attribute
            # to render newsletter again
            self._dynamic_content = None
        else:
            try:
                self.dateEmitted = DateTime(dateEmitted)
            except:
                self.dateEmitted = None

        if self.text_format:
            self.setFormat(text_format)
        if text:
            self._edit(text=text, text_format=text_format)

        if self.REQUEST.form.get('attachment_delete')=='delete':
            self.attachment = None
        elif attachment:
            self._saveBlob(attachment)

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

        # Reindex
        self.reindexObject()
        return

    security.declarePrivate('_saveBlob')
    def _saveBlob(self, attachment):
        content_type = attachment.headers.get('content-type')
        content_disposition = attachment.headers.get('content-disposition', '')
        filename = re.search(r'''filename="([^"]+)"''', content_disposition)
        if filename:
             filename = filename.groups()[0]
        data = str(attachment.read())
        blob = BlobWrapper(content_type)
        if isinstance(data, basestring):
            data = StringIO.StringIO(data) # simple strings cannot be adapted...
            setattr(data, 'filename', filename)
        if data is not None:
            blobbable = IBlobbable(data)
            try:
                blobbable.feed(blob.getBlob())
            except ReuseBlob, exception:
                blob.setBlob(exception.args[0]) # reuse the given blob
        blob.setFilename(blobbable.filename())
        self.attachment = blob
        transaction.savepoint(optimistic=True)

    security.declareProtected(View, 'attachment_data')
    def attachment_data(self):
        attachment = getattr(self, 'attachment', None)
        if not attachment:
            return None
        return {'filename': attachment.getFilename(),
                'content_type': attachment.getContentType(),
                'size': sizeof_fmt(attachment.get_size()),
                }

    security.declareProtected(View, 'download_attachment')
    def download_attachment(self):
        """Download stored attachment"""
        return self.attachment.index_html()

    security.declareProtected(View, 'CookedBody')
    def CookedBody(self, stx_level=None, setLevel=0):
        """
        """
        if (self.text_format.endswith('html') or self.text_format.endswith('plain')
            or (stx_level is None)
            or (stx_level == self._stx_level)):
            return self.cooked_text
        else:
            cooked = format_stx(self.text, stx_level)
            if setLevel:
                self._stx_level = stx_level
                self.cooked_text = cooked
            return cooked

    security.declareProtected(View, 'Format')
    def Format(self):
        """
        """
        if self.text_format == 'html':
            return 'text/html'
        else:
            return 'text/plain'

    security.declareProtected(ModifyPortalContent, 'setFormat')
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

    ############################
    ## portal_catalog support ##
    ############################

    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        "Returns a concatination of all searchable text"

        ret="%s %s %s" % (self.Title(),
                          self.Description(),
                          self.text)
        return ret


    ###################
    security.declarePrivate('changeRelativeToAbsolute')
    def changeRelativeToAbsolute(self, text):
        """
            Kupu, TinyMCE and other editors insert relative URLS for links, images and anchors in content.
            Those links don't work in certain mailclients. This is where this method comes in.
            This changes relative links to absolute ones, without base-tags, because that doesn't work
            in all mailclients.
        """
        tree = HTMLTreeBuilder.TreeBuilder(encoding='utf-8')

        # add a root node for the parser
        tree.feed('<div>%s</div>' % text)
        rootnode = tree.close()

        # add /view to current_url so all links are correct - BBB Crappy!!!
        #current_url = "%s/view" % self.absolute_url()
        current_url = self.absolute_url()
        parsed_url = urlparse(current_url)

        for x in rootnode.getiterator():
            current_keys = x.keys()
            # fix links and anchors

            if x.tag == "a":
                # BBB: a very UGLY fix to work with TinyMCE until issue 51 will stay
                # http://plone.org/products/tinymce/issues/51
                if "href" in current_keys and "class" not in current_keys:
                    if x.attrib['href'].startswith("..") or \
                        (not x.attrib['href'].startswith("http://") and \
                         not x.attrib['href'].startswith("https://") and \
                         not x.attrib['href'].startswith("mailto:")):
                        x.attrib['href'] = self.absolute_url()+"/" + x.attrib['href']

                if "href" in current_keys and "class" in current_keys:
                    # internal-link CSS class is not there if the user make manually an internal link
                    # we keep also the class check because of resolveuid links
                    cssClasses = x.attrib['class'].split()
                    if "internal-link" in cssClasses or x.attrib['href'].startswith('../'):
                        href = x.attrib['href']
                        relative_part = "/".join(parsed_url[2].split('/')[:(len(parsed_url[2].split('/'))-len(href.split("../")))])
                        x.attrib['href'] = "%s://%s%s/%s" % (parsed_url[0], parsed_url[1], relative_part, href.split("../")[-1])

                elif "href" in current_keys:
                    # plone 2.5 uses .# for anchors, so we replace this with #
                    if ".#" in x.attrib['href']:
                        x.attrib['href'] = x.attrib['href'].replace('.#','#')

            # fix images
            elif x.tag == "img":
                if "src" in current_keys:
                    src = x.attrib['src']

                    # fix only relative links
                    if src.find('http://') != 0:
                        relative_part = "/".join(parsed_url[2].split('/')[0:(len(parsed_url[2].split('/'))-len(src.split("../")))])
                        x.attrib['src'] = "%s://%s%s/%s" % (parsed_url[0], parsed_url[1], relative_part, src.split("../")[-1])

        tree = ElementTree.ElementTree(rootnode);
        output = StringIO.StringIO()
        tree.write(output)
        text = output.getvalue()
        output.close()

        return text

    security.declarePublic('renderTextHTML')
    def renderTextHTML(self, html=True, force=False, footer_url=None, REQUEST=None):
        """Makes the HTML part for MUA of the newsletter
        """
        theme = self.getTheme()
        template = theme.getRenderTemplate()
        newsletterFooter = theme.newsletterFooter
        if '%(url)s' in newsletterFooter and footer_url is not None:
            newsletterFooter = newsletterFooter.replace('%(url)s', footer_url)

        # fix relative links
        text = self.changeRelativeToAbsolute(self.cooked_text)

        data = template(id=self.id, body=text,
                        description=self.description,
                        newsletterFooter=newsletterFooter, html=html,
                        title=self.title, date=self.dateEmitted, force=force)

        data = safe_unicode(data)

        if theme.alternative_portal_url:
            alternative_portal_url = theme.alternative_portal_url
            if alternative_portal_url.endswith('/'):
                alternative_portal_url = alternative_portal_url[:-1]
            portal_url = getToolByName(self, 'portal_url')()
            data = data.replace(portal_url, alternative_portal_url)

        if REQUEST is not None:
            # Called directly from the web; set content-type
            # The publisher will then re-encode for us
            REQUEST.RESPONSE.setHeader('content-type',
                                       'text/html; charset=%s' %
                                       self.ploneCharset())

        return data

    def manageUrls(self, html):
        # BBB: this is a mess, refactorgin using regular expression or an HTML parsing utility
        urls = []
        reference_indexes = []
        theme = self.getTheme()
        start_indexes = [m.end() for m in re.finditer('href="', html)]
        for start in start_indexes:
            end = html.find('"', start)
            urls.append(html[start:end])
            index_text = html.find('</a>', start)
            reference_indexes.append(index_text)
        reference_indexes.reverse()
        n_reference = len(reference_indexes)
        for index in reference_indexes:
            html = html[:index] + ' [' + str(n_reference) + '] ' + html[index:]
            n_reference = n_reference - 1
        html = html + '\r\n-------------- %s --------------\r\n' % translate(_(u'References'), context=self.REQUEST).encode('utf-8')
        for seq, url in enumerate(urls):
            html = html + '[' + str(seq + 1) + '] ' + url + '\r\n'
        # right now we don't send attachments in text/plain messages
        if self.attachment:
            here_url = self.absolute_url()
            if theme.alternative_portal_url:
                portal_url = getToolByName(self, 'portal_url')()
                here_url.replace(portal_url, theme.alternative_portal_url, 1)
            html = html + '\r\n-------------- %s --------------\r\n' % translate(_(u'Attachment'), context=self.REQUEST).encode('utf-8')
            html = html + '[' + self.absolute_url() + '/download_attachment\r\n'
        return html


    security.declarePublic('renderTextPlain')
    def renderTextPlain(self, force=False, footer_url=None, REQUEST=None):
        """Makes the text/plain part for MUA of the newsletter"""

        html = self.renderTextHTML(html=False, force=force, footer_url=footer_url)

        # portal_tranforms (at least lynx transform) requires encoded data
        html = html.encode('utf8') # encodes everything, good enough
        #in plain-text we show the link at bottom of the mail
        html = self.manageUrls(html)

        # Convert to text/html, preferring lynx_dump if available
        transform_tool = getToolByName(self, 'portal_transforms')
        lynxAvailable = (
            'lynx_dump' in transform_tool.objectIds() and
            transform_tool.lynx_dump.title != 'BROKEN')
        if lynxAvailable:
            # Hackery ahead! We'll tell lynx what encodings to use
            # TODO: fix portal_transforms to deal with encodings
            if not hasattr(transform_tool.lynx_dump, '_v_transform'):
                transform_tool.lynx_dump._load_transform()
            transform = transform_tool.lynx_dump._v_transform
            oldargs = transform.binaryArgs
            transform.binaryArgs += ' -assume_charset=utf8'
            transform.binaryArgs += ' -display_charset=utf8'

            text = transform_tool('lynx_dump', html)

            transform.binaryArgs = oldargs

            if footer_url is None:
                # fixup URL references
                text = lynx_file_url.sub('%(url)s', text)
        else:
            text = transform_tool.convertToData('text/plain', html)
        #remove some garbage in the string
        text =  text.lstrip(' \n')
        if REQUEST is not None:
            # called directly from the web; set content-type
            # The publisher will then re-encode for us
            REQUEST.RESPONSE.setHeader('Content-Type',
                                       'text/plain; charset=%s' %
                                       self.ploneCharset())

        return safe_unicode(text)

    security.declarePublic('renderTextHTMLEncoded')
    def renderTextHTMLEncoded(self, html=True, force=False, footer_url=None, REQUEST=None):
        return self.renderTextHTML(html=html, force=force, footer_url=footer_url, REQUEST=REQUEST).encode(self.ploneCharset())

    security.declarePublic('renderTextPlainEncoded')
    def renderTextPlainEncoded(self, html=True, force=False, footer_url=None, REQUEST=None):
        return self.renderTextPlain(html=html, force=force, footer_url=footer_url, REQUEST=REQUEST).encode(self.ploneCharset())


    security.declareProtected(ChangeNewsletter, 'testSendToMe')
    def testSendToMe(self, REQUEST=None, email=None):
        """Sends HTML/mixed and plain text newsletter to the author"""
        if REQUEST is None:
            REQUEST = self.REQUEST
        theme = self.getTheme()
        email = REQUEST.get('email', None) or theme.testEmail
        editurl = theme.absolute_url() + '/xxx'

        # We want to test the unsubscribe url too and we asume the test subscriber is located in the theme
        for subscriber in theme.objectValues('Subscriber'):
            if subscriber.Title() == email:
                si = subscriber.mailingInfo()
                # si is None if user is inactive
                if si is not None:
                    editurl = si[2]
                break;

        recipients = [(email, 'HTML', editurl), (email, 'Text', editurl)]
        # force fresh rendering of the template - do not use dynamic content stored in instance.
        errors = self.sendToRecipients(recipients, force=True)
        return self.Newsletter_testForm(errors=errors, sent=1)

    ########################
    ## Sending newsletter ##
    ########################

    security.declareProtected(ChangeNewsletter, 'sendToRecipients')
    def sendToRecipients(self, recipients, force=False):
        """Send the newsletter to a list of recipients

        switched to email.Message.Message
        recipients is a list of tuples in the form:
        [(email, format, editurl),...]
        email is the mail address
        format is 'HTML' to receive HTML/mixed mail
        editurl is the user preference URL"""
        htmlTpl = self.renderTextHTML(force=force)
        hasurl = '%(url)s' in htmlTpl
        plaintextTpl = self.renderTextPlain(force=force)
        theme = self.getTheme()
        mailFrom = theme.authorEmail
        charset = self.ploneCharset()
        errors = []

        mailMethod = theme.sendmail

        titleForMessage = Header(self.title, 'utf-8')

        portal_url = getToolByName(self, 'portal_url')()
        for mailTo, format, editurl in recipients:
            if theme.alternative_portal_url:
                editurl = editurl.replace(portal_url,
                                          theme.alternative_portal_url)
            mainMsg=email.Message.Message()
            mainMsg["To"]=mailTo
            mainMsg["From"]=mailFrom
            mainMsg["Subject"]=titleForMessage
            mainMsg["Date"]=email.Utils.formatdate(localtime=1)
            mainMsg["Message-ID"]=email.Utils.make_msgid()
            mainMsg["Mime-version"]="1.0"

            if format == 'HTML':
                new_htmlTpl = htmlTpl
                if hasurl:
                    new_htmlTpl = new_htmlTpl.replace('%(url)s', editurl)

                new_plaintextTpl = plaintextTpl
                if hasurl:
                    new_plaintextTpl = new_plaintextTpl.replace('%(url)s', editurl)
                mainMsg["Content-type"]="multipart/alternative"
                #mainMsg.preamble="This is the preamble.\n"
                mainMsg.epilogue="\n" # To ensure that message ends with newline

                # plain
                secondSubMsg=email.Message.Message()
                secondSubMsg.add_header("Content-Type", "text/plain", charset= charset)
                secondSubMsg["Content-Disposition"]="inline"
                secondSubMsg.set_payload(safe_unicode(new_plaintextTpl).encode(charset), charset)
                mainMsg.attach(secondSubMsg)
                # html
                subMsg=email.Message.Message()
                subMsg.add_header("Content-Type", "text/html", charset= charset)
                subMsg["Content-Disposition"]="inline"
                subMsg.set_payload(safe_unicode(new_htmlTpl).encode(charset), charset)
                mainMsg.attach(subMsg)

                # BBB: there's now reason why text/plain newsletter must not carry also attachments
                if self.attachment:
                    fp = self.attachment.getBlob().open()
                    attachMsg = MIMEBase(*self.attachment.getContentType().split('/'))
                    attachMsg.set_payload(fp.read())
                    fp.close()
                    encoders.encode_base64(attachMsg)
                    attachMsg.add_header('Content-Disposition', 'attachment', filename=self.attachment.getFilename())
                    mainMsg.attach(attachMsg)
                
            else:
                # Plain text
                new_plaintextTpl = plaintextTpl
                if hasurl:
                    new_plaintextTpl = new_plaintextTpl.replace('%(url)s', editurl)
                mainMsg["Content-type"]="text/plain"
                mainMsg.set_payload(safe_unicode(new_plaintextTpl).encode(charset), charset)
                mainMsg.epilogue="\n" # To ensure that message ends with newline

            try:
                mailMethod(mailFrom, (mailTo,), mainMsg)
            except Exception:
                errors.append(mailTo)
                tbfile = cStringIO.StringIO()
                traceback.print_exc(file=tbfile)
                logger.warning('Error when sending to %s\n%s' % (mailTo, tbfile.getvalue()))
                tbfile.close()
        return errors

    security.declareProtected(ChangeNewsletter, 'sendToSubscribers')
    @postonly
    def sendToSubscribers(self, REQUEST=None, active=True):
        """Sends that newsletter to all subscribers and extra recipients
        Use active as False to send email to non-active subcribers. Seems stupid? Try to forget about activating
        some of them...
        Using firebug you can add this to the post form: <input type="hidden" name="active:int" value="0" />
        """
        theme = self.getTheme()
        recipients = theme.mailingInfos(active=active)
        if not active:
            self.plone_utils.addPortalMessage(_(u'SENDING TO NOT ACTIVE USERS.'))
        # we are sending to all recipients. Render dynamic content and store it persistently
        errors1 = self.sendToRecipients(recipients)
        recipients = theme.getExtraRecipients()
        errors2 = self.sendToRecipients(recipients)
        self.dateEmitted = DateTime()
        if REQUEST is not None:
            if errors1 or errors2:
                statusMsg = _(u'SMTP server related errors') ##!: display recipient
            else:
                statusMsg = _(u'The newsletter has been sent.')
            self.plone_utils.addPortalMessage(statusMsg)
            return self.Newsletter_sendForm(errors1=errors1, errors2=errors2)
        else:
            return (errors1, errors2)

    ###############
    ## Utilities ##
    ###############

    security.declarePublic('getObjects')
    def getObjects(self):
        """
        """
        hasPermission = nobody.has_permission
        objects = [object for object in self.objectValues(('Section','NewsletterTopic', 'NewsletterReference', 'NewsletterRichReference')) if hasPermission('View', object)]
        objects.sort(lambda a,b:cmp(self.getObjectPosition(a.getId()), self.getObjectPosition(b.getId())))
        return objects

    security.declareProtected(ListFolderContents, 'listFolderContents')
    def listFolderContents( self, spec=None, contentFilter=None, suppressHiddenFiles=0 ):
        """
        Hook around 'contentValues' to let 'folder_contents'
        be protected.  Duplicating skip_unauthorized behavior of dtml-in.

        In the world of Plone we do not want to show objects that begin with a .
        So we have added a simply check.  We probably dont want to raise an
        Exception as much as we want to not show it.

        """
        ctool = getToolByName(self, 'portal_catalog')
        items = ctool(path={'query':'/'.join(self.getPhysicalPath()), 'depth':1},
                      sort_on='sortable_title')
        return items

    # For plone 2.1+ to show unindexed content
    security.declareProtected(ChangeNewsletterTheme, 'getFolderContents')
    def getFolderContents(self, contentFilter=None,batch=False,b_size=100,full_objects=False):
        """Override getFolderContents to show all objects"""
        contents = self.listFolderContents(contentFilter=contentFilter)
        if batch:
            from Products.CMFPlone import Batch
            b_start = self.REQUEST.get('b_start', 0)
            batch = Batch(contents, b_size, int(b_start), orphan=0)
            return batch
        return contents


# Class instanciation
InitializeClass(Newsletter)
