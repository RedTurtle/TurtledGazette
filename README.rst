This is not an original product, this is a fork of `PloneGazette`__.

__ http://plone.org/products/plonegazette

Motivation
==========

**(...also know as: "why branching?"...)**

For a very long long time PloneGazette development has been stopped, and we continued a
non-official set of changes.

After a long long time the official development re-started, but our branch is **so** different that a
merge was mostly impossible. But we like our changes!

Main differences
================

Newsletter content is not a folder anymore: we removed *all* Topic/Section and broken stuff inside.

Apart this main change, here follow an (uncomplete) list of changes:

- Inserted a section call 'references' into the plain-text mail with the links contained into the e-mail
- Added the ``activateAllSubscribers`` method to NLTheme objects
- Subscription to the theme now is in the theme view
- Possibile to get infos (and send newsletter) to non-active members
- Fixed newsletter action aliases
- Fixed theme action aliases
- the testSendToMe now take a REQUEST parameter, for send to another email
- manually created internal links are no more broken
- added ``subscribers_status_csv`` method
- the ``activateAllSubscribers`` not take a csv_string parameter, to activate only some
- the newsletter theme now have a rich text field
- can override "b_size" in subscribers_infos from request
- now link check if *one* of the CSS classes is ``internal-link``
  (not comparing with the whole ``class`` attribute)
- use MailHost.send before trying to use MailHost.secureSend
- Can now use an alternative mail host providing a new site property with id ``plonegazette_mailhost``
  (can be used to use `MaildropHost`__)

__ https://pypi.python.org/pypi/Products.MaildropHost

Please note
===========

This product is compatible with PloneGazette *but* you can't use both together (they use the same namespace!).


Dependencies
============

This product has been tested on all Plone versions from 3.3 to 4.3.

Authors
=======

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.it/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.it/
