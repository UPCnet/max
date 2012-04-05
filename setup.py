import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'pyramid_who',
    'pymongo',
    'rfc3339',
    'requests',
    'tweepy',
    'celery'
    ]

test_requires = ['WebTest', 'mock', ]

setup(name='max',
      version='3.0',
      description='Activity Stream and Subscription Enhanced Engine (Motor d\'activitat i subscripcions extes)',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='UPCnet Content Management Team',
      author_email='victor.fernandez@upcnet.es',
      url='http://github.com/upcnet/max',
      keywords='web pylons pyramid mongodb',
      packages=['max', 'maxclient', 'maxrules'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires + test_requires,
      test_suite="max.tests",
      extras_require={
        'test': ['WebTest', 'mock', ]
      },
      entry_points="""\
      [paste.app_factory]
      main = max:main
      [console_scripts]
      maxrules.twitter = maxrules.twitter:main
      """,
      )
