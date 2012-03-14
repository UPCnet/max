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
    'requests'
    ]

test_requires = ['WebTest', 'mock', ]

setup(name='max',
      version='2.0',
      description='Extended Activity Stream and Subscriptions Engine (Motor extes d\'activitat i subscripcions)',
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
      keywords='web pylons pyramid',
      packages=find_packages(),
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
      """,
      paster_plugins=['pyramid'],
      )

