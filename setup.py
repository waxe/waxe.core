import os

from setuptools import setup, find_packages

# Hack to prevent TypeError: 'NoneType' object is not callable error
# on exit of python setup.py test
try:
    import multiprocessing
except ImportError:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid_mako',
    'pyramid==1.5.7',
    'SQLAlchemy==1.0.4',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'pyramid_auth',
    'pyramid_exclog',
    'zope.sqlalchemy',
    'waitress',
    'sqla_declarative',
    'xmltool',
    'py-bcrypt',
    'pyramid_sqladmin',
    'pyramid_logging',
    'whoosh',
    'sqla_taskq',
    'webhelpers',
    'importlib',
]

# TODO release:
# * waxe.angular
# * waxe.txt
# * waxe.xml => it should not be the case since it's a dependency
# * pysvn ? add in the doc we need to create symllinks
# => it shouldn't be dependency in case we don't use it
# xmltool: we need a new release

setup(name='waxe.core',
      version='0.1',
      description='waxe',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      setup_requires=['nose'],
      install_requires=requires,
      namespace_packages=['waxe'],
      tests_require=[
          'nose',
          'nose-cov',
          'WebTest',
          'mock',
      ],
      entry_points="""\
      [paste.app_factory]
      main = waxe.core:main
      [console_scripts]
      initialize_waxe_db = waxe.core.scripts.initializedb:main
      update_waxe_indexation = waxe.core.scripts.search_indexation:main
      """,
      )

