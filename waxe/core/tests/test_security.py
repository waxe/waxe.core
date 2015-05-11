from pyramid import testing
from .. import security
from .testing import BaseTestCase
from ..models import UserConfig, User, Group, DBSession
import logging


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }


class TestSecurity(BaseTestCase):

    def test_root_factory(self):
        request = testing.DummyRequest()
        factory = security.RootFactory(request)
        self.assertTrue(factory.__acl__)

    def test_get_user(self):
        self.assertEqual(security.get_user(None), None)
        self.assertEqual(security.get_user('Bob'), self.user_bob)
        self.assertEqual(security.get_user('bob'), None)
        self.assertEqual(security.get_user('nonexisting'), None)

    def test_get_user_logging(self):
        user = User(login='Bob', password='pass1')
        DBSession.add(user)
        handler = MockLoggingHandler()
        logging.getLogger().addHandler(handler)
        self.assertEqual(security.get_user('Bob'), None)
        self.assertEqual(handler.messages['error'],
                         ['Multiple rows were found for one()'])

    def test_validate_password(self):
        request = testing.DummyRequest()
        self.assertEqual(security.validate_password(request,
                                                    'nonexisting', ''), False)
        self.assertEqual(security.validate_password(request,
                                                    'Bob', ''), False)
        self.assertEqual(security.validate_password(request,
                                                    'Bob', 'toto'), False)
        self.assertEqual(security.validate_password(request,
                                                    'Bob', 'secret_bob'),
                         self.user_bob)

    def test_get_user_permissions(self):
        request = testing.DummyRequest()
        perms = security.get_user_permissions('nonexisting', request)
        self.assertEqual(perms, [])
        perms = security.get_user_permissions('Bob', request)
        expected = ['role:admin']
        self.assertEqual(perms, expected)
        group = Group(name='group1')
        self.user_bob.groups = [group]
        expected = ['role:admin', 'group:group1']
        perms = security.get_user_permissions('Bob', request)
        self.assertEqual(perms, expected)

    def test_get_userid_from_request(self):
        request = testing.DummyRequest()
        self.assertEqual(security.get_userid_from_request(request), None)
        self.config.testing_securitypolicy(userid=self.user_bob.login,
                                           permissive=False)
        self.assertEqual(security.get_userid_from_request(request),
                         self.user_bob.login)
        self.config.testing_securitypolicy(userid='nonexisting',
                                           permissive=False)
        self.assertEqual(security.get_userid_from_request(request),
                         'nonexisting')
