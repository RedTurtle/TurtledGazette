# -*- coding: utf8 -*-

from Products.Five import BrowserView
from zope.component import getMultiAdapter
import json


class TinyMCEConfView(BrowserView):
    """
    Get TinyMCE configuration for PloneGazette WYSIWYG editor
    """
    
    def __call__(self):
        context = self.context
        request = self.request
        pattern_options = getMultiAdapter((context, request, None),
                                          name="plone_settings").tinymce()['data-pat-tinymce']
        tiny_options = json.loads(pattern_options)
        conf = {"textareaName": "text",
                "widget": {"text/html": {"pattern": "tinymce",
                                         "patternOptions": tiny_options}}}
        return json.dumps(conf)
