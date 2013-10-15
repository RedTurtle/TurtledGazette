from Products.CMFCore.permissions import setDefaultRoles

# New specific permissions

AddNewsletterTheme = 'PNL Add Newsletter Theme'
ChangeNewsletterTheme = 'PNL Change Newsletter Theme'
AddNewsletter = 'PNL Add Newsletter'
ChangeNewsletter = 'PNL Change Newsletter'
AddSubscriber = 'PNL Add Subscriber'
ChangeSubscriber = 'PNL Change Subscriber'

# Default roles for those permissions
setDefaultRoles(AddNewsletterTheme, ('Manager',))
setDefaultRoles(ChangeNewsletterTheme, ('Manager', 'Owner'))
setDefaultRoles(AddNewsletter, ('Manager',))
setDefaultRoles(ChangeNewsletter, ('Manager', 'Owner'))
setDefaultRoles(AddSubscriber, ('Anonymous', 'Manager', 'Owner', 'Member'))
setDefaultRoles(ChangeSubscriber, ('Anonymous', 'Manager', 'Owner'))
