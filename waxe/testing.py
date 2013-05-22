import unittest
import transaction
from webtest import TestApp

from mock import patch
import tw2.core as twc
from sqlalchemy import create_engine

from . import main
from .models import (
    DBSession,
    Base,
    User,
    Role,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
)


def login_user(login):
    """Decorator to log the user
    """
    def deco(func):
        def wrapper(*args, **kw):
            with patch('pyramid.authentication.'
                       'AuthTktAuthenticationPolicy.unauthenticated_userid',
                       return_value=login):
                func(*args, **kw)
        return wrapper
    return deco


class WaxeTestCase(unittest.TestCase):

    def setUp(self):
        self.settings = {
            'sqlalchemy.url': 'sqlite://',
            'authentication.key': 'secret',
            'authentication.debug': True,
            'mako.directories': 'waxe:templates',
            'session.key': 'session_key',
            'pyramid.includes': ['pyramid_auth'],
            'pyramid_auth.validate_function': 'waxe.security.validate_password',
            'dtd_urls': 'http://xmltool.lereskp.fr/static/exercise.dtd'
        }
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
            self.user_bob = User(login="Bob", password='secret')
            self.user_bob.roles = [admin]
            DBSession.add(self.user_bob)

    def tearDown(self):
        DBSession.remove()
