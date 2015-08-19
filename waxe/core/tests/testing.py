import os
import unittest
import transaction
from webtest import TestApp
from functools import wraps

from mock import patch
import tw2.core as twc
from sqlalchemy import create_engine
import bcrypt
from pyramid import testing

from .. import main
from ..models import (
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


def local_login_user(login):
    """Decorator to log the user
    """
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kw):
            with patch('waxe.core.security.unauthenticated_userid',
                       return_value=login):
                func(*args, **kw)
        return wrapper
    return deco

path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
dtd_url = os.path.join(path, 'exercise.dtd')

SETTINGS = {
    'sqlalchemy.url': 'sqlite://',
    'mako.directories': 'waxe.core:templates',
    'session.key': 'session_key',
    'pyramid.includes': ['pyramid_auth', 'pyramid_sqladmin', 'pyramid_mako'],
    'pyramid_auth.no_routes': 'true',
    'pyramid_auth.cookie.secret': 'secret',
    'pyramid_auth.cookie.validate_function': 'waxe.core.security.validate_password',
    'pyramid_auth.cookie.callback': 'waxe.core.security.get_user_permissions',
    'dtd_urls': dtd_url,
    # HACK: in waiting the package are correctly splitted we need the routes
    # existing
    'waxe.editors': 'waxe.xml.views.editor',
}

SECRET_ADMIN = bcrypt.hashpw('secret_admin', bcrypt.gensalt())
SECRET_BOB = bcrypt.hashpw('secret_bob', bcrypt.gensalt())
SECRET_FRED = bcrypt.hashpw('secret_fred', bcrypt.gensalt())


class DBTestCase(unittest.TestCase):
    BOB_RELPATH = 'waxe/core/tests/files'

    def setUp(self):
        super(DBTestCase, self).setUp()
        engine = create_engine('sqlite://')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        self.role_editor = Role(name=ROLE_EDITOR)
        DBSession.add(self.role_editor)
        self.role_contributor = Role(name=ROLE_CONTRIBUTOR)
        DBSession.add(self.role_contributor)
        self.role_admin = Role(name="admin")
        DBSession.add(self.role_admin)
        self.user_admin = User(login="Admin", password=SECRET_ADMIN)
        self.user_admin.config = UserConfig()
        self.user_admin.roles = [self.role_admin]
        DBSession.add(self.user_admin)

        self.user_bob = User(login="Bob", password=SECRET_BOB)
        self.user_bob.roles = [self.role_admin]
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(
            root_path=os.path.join(os.getcwd(), self.BOB_RELPATH)
        )

        self.user_fred = User(login='Fred', password=SECRET_FRED)
        self.user_fred.config = UserConfig(
            root_path='/fred/path',
            use_versioning=True,
            versioning_password='secret_fred',
        )
        DBSession.add(self.user_fred)

    def tearDown(self):
        DBSession.remove()
        super(DBTestCase, self).tearDown()


class BaseTestCase(DBTestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.config = testing.setUp()
        self.config.registry.settings.update({
            'mako.directories': 'waxe.core:templates',
            'waxe.extensions': ['.xml'],
        })
        self.config.include('pyramid_mako')

    def tearDown(self):
        testing.tearDown()
        super(BaseTestCase, self).tearDown()


class LoggedBobTestCase(BaseTestCase):
    def setUp(self):
        super(LoggedBobTestCase, self).setUp()
        self.config.testing_securitypolicy(userid=self.user_bob.login,
                                           permissive=True)


class WaxeTestCase(DBTestCase):

    def setUp(self):
        if not hasattr(self, 'settings'):
            self.settings = SETTINGS.copy()

        app = main({}, **self.settings)
        app = twc.middleware.TwMiddleware(app)
        self.testapp = TestApp(app)
        super(WaxeTestCase, self).setUp()


class WaxeTestCaseVersioning(DBTestCase):

    def setUp(self):
        self.settings = SETTINGS.copy()
        self.settings['waxe.versioning'] = True
        app = main({}, **self.settings)
        app = twc.middleware.TwMiddleware(app)
        self.testapp = TestApp(app)
        super(WaxeTestCaseVersioning, self).setUp()
        DBSession.add(self.user_fred)
        DBSession.add(self.user_bob)
        self.user_fred.config.use_versioning = True
        self.user_bob.config.use_versioning = True
