import unittest
import transaction
from webtest import TestApp
from functools import wraps

from mock import patch
import tw2.core as twc
from sqlalchemy import create_engine
import bcrypt

from . import main
from .models import (
    DBSession,
    Base,
    User,
    UserConfig,
    Role,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
)


def login_user(login):
    """Decorator to log the user
    """
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kw):
            with patch('pyramid.authentication.'
                       'AuthTktAuthenticationPolicy.unauthenticated_userid',
                       return_value=login):
                func(*args, **kw)
        return wrapper
    return deco


SETTINGS = {
    'sqlalchemy.url': 'sqlite://',
    'authentication.cookie.secret': 'secret',
    'mako.directories': 'waxe:templates',
    'session.key': 'session_key',
    'pyramid.includes': ['pyramid_auth', 'pyramid_sqladmin', 'pyramid_mako'],
    'authentication.cookie.validate_function': 'waxe.security.validate_password',
    'authentication.cookie.callback': 'waxe.security.get_user_permissions',
    'dtd_urls': 'http://xmltool.lereskp.fr/static/exercise.dtd'
}


class WaxeTestCase(unittest.TestCase):

    def setUp(self):
        self.settings = SETTINGS.copy()
        app = main({}, **self.settings)
        app = twc.middleware.TwMiddleware(app)
        self.testapp = TestApp(app)
        engine = create_engine('sqlite://')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            for role in [ROLE_EDITOR, ROLE_CONTRIBUTOR]:
                r = Role(name=role)
                DBSession.add(r)
            admin = Role(name="admin")
            pwd = bcrypt.hashpw('secret_bob', bcrypt.gensalt())
            self.user_bob = User(login="Bob", password=pwd)
            self.user_bob.roles = [admin]
            DBSession.add(self.user_bob)

            pwd = bcrypt.hashpw('secret_fred', bcrypt.gensalt())
            self.user_fred = User(login='Fred', password=pwd)
            self.user_fred.config = UserConfig(
                root_path='',
                use_versioning=True,
                versioning_password='secret_fred',
            )
            DBSession.add(self.user_fred)

    def tearDown(self):
        DBSession.remove()


class WaxeTestCaseVersioning(unittest.TestCase):

    def setUp(self):
        self.settings = SETTINGS.copy()
        self.settings['versioning'] = True
        app = main({}, **self.settings)
        app = twc.middleware.TwMiddleware(app)
        self.testapp = TestApp(app)
        engine = create_engine('sqlite://')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            for role in [ROLE_EDITOR, ROLE_CONTRIBUTOR]:
                r = Role(name=role)
                DBSession.add(r)
            admin = Role(name="admin")
            self.user_bob = User(login="Bob", password='secret_bob')
            self.user_bob.config = UserConfig(root_path='',
                                              use_versioning=True)
            self.user_bob.roles = [admin]
            DBSession.add(self.user_bob)

            self.user_fred = User(login='Fred', password='secret_fred')
            self.user_fred.config = UserConfig(root_path='',
                                               use_versioning=True)
            DBSession.add(self.user_fred)

    def tearDown(self):
        DBSession.remove()
