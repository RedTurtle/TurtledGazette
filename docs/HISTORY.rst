HISTORY
=======

4.1.1 (unreleased)
==================

- Fixed issues with old Newsletters without the new ``attachment`` attribute
  [keul]
- Fixed utf-8 encoding issues when sending text/plain messages
  [keul]
- Is now possible to behave "private" newsletter themes.
  Subscribers will be able to unsubscribe from theme they can't reach
  [keul]
- Other i18n enhancment
  [keul]

4.1.0 (2015-04-09)
==================

- I18n fixes
  [keul]
- Automatically create a subscribers folder inside the theme on creation.
  This close `#3`__.
  [keul]
- Subscriber folder selection is now a combobox selection
  [keul]
- Multiple subscribers folder are now supported again. That means that selecting
  a folder will use that as adresses source when sending.
- "Activate account" is now unshow to subscribers. This close `#4`__
  [keul]
- Added a newsletter attachment
  [keul]
- Accessibility fixes, lot of label not bound to form elements
  [keul]

__ https://github.com/RedTurtle/TurtledGazette/issues/3
__ https://github.com/RedTurtle/TurtledGazette/issues/4

4.0.0 (2013-12-16)
==================

Where branch started (PloneGazette 3.0.1) plus:

- Inserted a section call 'references' into the plain-text mail with the links contained into the e-mail
- Added the ``activateAllSubscribers`` method to NLTheme objects
- Disabled Newsletter sub-objects
- Subscription to the theme now is in the theme view
- Possibile to get infos (and send newsletter) to non-active members
- Fixed newsletter action aliases
- Newsletter is no-more a folderish type
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
- Removed unused dynamic content methods [cekk]
- Fixed encoding error in newsletter indexer for descriptions [cekk]
- Fixed renderTextPlain to remove some garbage to converted strings [cekk]
- Added external css support for newsletter templates [cekk]

__ https://pypi.python.org/pypi/Products.MaildropHost
