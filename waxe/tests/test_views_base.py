import os
import json
from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
from ..testing import (
    BaseTestCase,
    WaxeTestCase,
    WaxeTestCaseVersioning,
    login_user,
    local_login_user
)
from mock import patch
from ..models import (
    DBSession,
    User,
    UserConfig,
    Role,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR
)

from .. import security

from ..views.base import (
    BaseViews,
    BaseUserViews,
    JSONHTTPBadRequest,
)


class EmptyClass(object):
    pass


class TestBaseView(BaseTestCase):

    def test___init__(self):
        request = testing.DummyRequest()
        obj = BaseViews(request)
        self.assertEqual(obj.request, request)
        self.assertEqual(obj.logged_user, None)
        self.assertEqual(obj.current_user, None)
        self.assertEqual(obj.root_path, None)

        DBSession.add(self.user_bob)
        DBSession.add(self.user_admin)
        with patch('waxe.security.get_user_from_request',
                   return_value=self.user_bob):
            obj = BaseViews(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user, self.user_bob)
            self.assertEqual(obj.current_user, self.user_bob)
            self.assertEqual(obj.root_path, self.user_bob.config.root_path)

            request.session = {'editor_login': 'Admin'}
            obj = BaseViews(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user, self.user_bob)
            self.assertEqual(obj.current_user, self.user_admin)
            self.assertEqual(obj.root_path, None)

    def test_get_current_user(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        res = BaseViews(request)._get_current_user()
        self.assertEqual(res, None)

        request.session = {'editor_login': 'Fake User'}
        res = BaseViews(request)._get_current_user()
        self.assertEqual(res, None)

        obj = BaseViews(request)
        obj.logged_user = 'Tom'
        res = obj._get_current_user()
        self.assertEqual(res, 'Tom')

        request.session = {'editor_login': 'Bob'}
        res = BaseViews(request)._get_current_user()
        self.assertEqual(res.login, self.user_bob.login)

    def test_user_is_admin(self):
        request = testing.DummyRequest()
        request.root = security.RootFactory(request)
        self.config.testing_securitypolicy(userid='Bob', permissive=False)
        res = BaseViews(request).user_is_admin()
        self.assertEqual(res, False)

        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        res = BaseViews(request).user_is_admin()
        self.assertEqual(res, True)

    def test__is_json(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        res = BaseViews(request)._is_json()
        self.assertEqual(res, False)

        request.matched_route.name = 'test_json'
        res = BaseViews(request)._is_json()
        self.assertEqual(res, True)


class TestBaseUserView(BaseTestCase):

    def test___init__(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        try:
            BaseUserViews(request)
            assert(False)
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

        request.matched_route.name = 'test_json'
        try:
            BaseUserViews(request)
            assert(False)
        except JSONHTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

        request.matched_route.name = 'login_selection'
        res = BaseUserViews(request)
        self.assertFalse(res.root_path)
        self.assertTrue(res)

        request.matched_route.name = 'test'
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        res = BaseUserViews(request)
        self.assertTrue(res.root_path)
        self.assertTrue(res)
