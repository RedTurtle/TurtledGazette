This is not an original product, this is a fork of `PloneGazette`__.

__ http://plone.org/products/plonegazette

Motivation
==========

**(...also know as: "why branching?"...)**

For a very long long time PloneGazette development stopped, and we continued fixing it with
a long set of changes on a `non official branch`__.

__ https://svn.plone.org/svn/collective/PloneGazette/branches/redturtle-fixes/

After a long long time the official development re-started, but our branch was **so** different that a
merge was mostly impossible. But we like our changes!

Documentation
=============

You can refer to the `official PloneGazette documentation`__.

__ https://github.com/collective/Products.PloneGazette/blob/master/Products/PloneGazette/docs/README.rst

Template stylesheets
====================

You can add a custom stylesheets to your custom templates.
To do this, you need to override **base_newsletter_styles.css** in portal_skins.

In this css, you can use a variable called "``${portal_url}``" that will be replaced to actual portal_url.

For example:    

::

    #container {
        background: transparent url(${portal_url}/header.jpg) no-repeat center top;
    }

Please note
===========

This product is compatible with PloneGazette *but* you can't use both (they use the same namespace!).

Dependencies
============

This product has been tested on all Plone versions from 4.0 to 4.3.

Authors
=======

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.it/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.it/

