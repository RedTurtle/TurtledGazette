#
# $Id: PNLUtils.py 54384 2007-11-24 18:35:03Z naro $
#

"""Misc utilities"""

import re

def checkMailAddress(obj,someAddr):
    """Checks the validity of a mail address"""
    return obj.plone_utils.validateSingleEmailAddress(someAddr)

from AccessControl import SpecialUsers

def ownerOfObject(obj):
    """Provides acl_user acquisition wrapped owner of object"""
    udb, uid = obj.getOwnerTuple()
    root = obj.getPhysicalRoot()
    udb = root.unrestrictedTraverse(udb, None)
    if udb is None:
        user = SpecialUsers.nobody
    else:
        user = udb.getUserById(uid, None)
        if user is None:
            user = SpecialUsers.nobody
        else:
            user = user.__of__(udb)
    return user

def escPercent(text):
    """Replace '%' with '%%' except '%('"""
    pat = re.compile(r'%(?!\()')
    return pat.sub('%%', text)

def sizeof_fmt(num, suffix='B'):
    """See http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size"""
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
