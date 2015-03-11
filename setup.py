import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
CONTRIBUTORS = open(os.path.join(here, 'CONTRIBUTORS.rst')).read()

requires = [
    'setuptools',
    'pyramid',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'pyramid_beaker',
    'pymongo',
    'rfc3339',
    'requests',
    'tweepy',
    'waitress',
    'Paste',
    'bleach',
    'pika',
    'Pillow',
    'maxcarrot',
    'maxutils'
]

test_requires = ['WebTest', 'mock', 'robotsuite', 'pyramid_robot']
docs_requires = ['manuel', 'pygments', 'sphinx_bootstrap_theme']

setup(name='max',
      version='4.0.26',
      description='Activity Stream and Subscription Enhanced Engine (Motor d\'Activitat i subscripcions eXtes)',
      long_description=README + '\n\n' + CHANGES + '\n\n' + CONTRIBUTORS,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pylons",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='UPCnet Content Management Team',
      author_email='victor.fernandez@upcnet.es',
      url='https://github.com/upcnet/max',
      keywords='web pylons pyramid mongodb',
      packages=['max'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires + docs_requires,
      tests_require=requires + test_requires,
      test_suite="max.tests",
      extras_require={
          'test': ['WebTest', 'mock', 'HTTPretty', 'manuel', 'pyramid-beaker']
      },
      entry_points="""
      [paste.app_factory]
      main = max:main
      """,
      )
