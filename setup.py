from setuptools import setup, find_packages
import os


setup(name='TurtledGazette',
      version='4.1.0.dev0',
      description='A complete Newsletter product for Plone (an alternate version of Products.PloneGazette)',
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      author='Pilot Systems',
      author_email='',
      maintainer='RedTurtle Technology',
      maintainer_email='sviluppoplone@redturtle.it',
      classifiers=[
            'Programming Language :: Python',
            'Framework :: Plone',
            'Framework :: Plone :: 3.3',
            'Framework :: Plone :: 4.0',
            'Framework :: Plone :: 4.1',
            'Framework :: Plone :: 4.2',
            'Framework :: Plone :: 4.3',
      ],
      keywords='plone newsletter',
      url='http://github.com/RedTurtle/TurtledGazette',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data = True,
      zip_safe=False,
      install_requires=[
            'setuptools',
            'elementtree',
      ],
      namespace_packages=['Products'],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
