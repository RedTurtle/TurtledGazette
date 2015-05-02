# -*- coding: utf-8 -*-


class NewsletterConversation(object):
    """Fake support for commenting in Plone, beating the plone.app.discussion incompatibility"""

    def __init__(self, context):
        self.context = context
        self.total_comments = 0
    
    def enabled(self):
        return False

    def getComments(start=0, size=None):
        return []
    
    def getThreads(start=0, size=None, root=0, depth=None):
        return []

    def objectIds(self, *args, **kwargs):
        return []
