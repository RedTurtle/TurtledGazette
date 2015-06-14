# -*- coding: utf8 -*-

import json
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope import interface

try:
    import mockup
except ImportError:
    mockup = None


class ITinyMCEConfView(interface.Interface):

    def configuration(select=True):
        """
        Site configuration for the tinymce pattern.
        If select is true, configuration is textareamimetypeselector pattern instead.
        """

    def mockup_available(self):
        """Check we can use Plone mockup or note"""


class TinyMCEConfView(BrowserView):
    """
    Get TinyMCE configuration for PloneGazette WYSIWYG editor
    """
    interface.implements(ITinyMCEConfView)

    def configuration(self, select=True):
        context = self.context
        request = self.request
        pattern_options = getMultiAdapter((context, request, None),
                                          name="plone_settings").tinymce()['data-pat-tinymce']
        tiny_options = json.loads(pattern_options)
        if not select:
            json.dumps(tiny_options)
        conf = {"textareaName": "text",
                "widget": {"text/html": {"pattern": "tinymce",
                                         "patternOptions": tiny_options}}}
        return json.dumps(conf)

    def mockup_available(self):
        return mockup is not None
