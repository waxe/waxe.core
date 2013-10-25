from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
from mock import patch

from ..testing import BaseTestCase, login_user
from waxe.models import UserConfig
from waxe import security
from waxe.views.base import (
    BaseView,
    BaseUserView,
    JSONHTTPBadRequest,
)


class EmptyClass(object):
    pass


class TestBaseView(BaseTestCase):

    def setUp(self):
        super(TestBaseView, self).setUp()
        self.config.registry.settings.update({
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.security.'
                                               'get_user_permissions')
        })
        self.config.include('pyramid_auth')

    def DummyRequest(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        return request

    def test___init__(self):
        request = self.DummyRequest()
        obj = BaseView(request)
        self.assertEqual(obj.request, request)
        self.assertEqual(obj.logged_user_login, None)
        self.assertEqual(obj.logged_user, None)
        self.assertEqual(obj.current_user, None)
        self.assertEqual(obj.root_path, None)

        with patch('waxe.security.get_userid_from_request',
                   return_value=self.user_bob.login):
            obj = BaseView(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user_login, self.user_bob.login)
            self.assertEqual(obj.logged_user, self.user_bob)
            self.assertEqual(obj.current_user, self.user_bob)
            self.assertEqual(obj.root_path, self.user_bob.config.root_path)

            request.session = {'editor_login': 'Admin'}
            obj = BaseView(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user_login, self.user_bob.login)
            self.assertEqual(obj.logged_user, self.user_bob)
            self.assertEqual(obj.current_user, self.user_admin)
            self.assertEqual(obj.root_path, None)

    def test_get_current_user(self):
        request = self.DummyRequest()
        res = BaseView(request)._get_current_user()
        self.assertEqual(res, None)

        request.session = {'editor_login': 'Fake User'}
        res = BaseView(request)._get_current_user()
        self.assertEqual(res, None)

        obj = BaseView(request)
        obj.logged_user = 'Tom'
        res = obj._get_current_user()
        self.assertEqual(res, 'Tom')

        request.session = {'editor_login': 'Bob'}
        res = BaseView(request)._get_current_user()
        self.assertEqual(res.login, self.user_bob.login)

    def test_user_is_admin(self):
        request = self.DummyRequest()
        res = BaseView(request).user_is_admin()
        self.assertEqual(res, False)

        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_bob.login):
            res = BaseView(request).user_is_admin()
            self.assertEqual(res, True)

    def test_user_is_editor(self):
        request = self.DummyRequest()
        res = BaseView(request).user_is_editor()
        self.assertEqual(res, False)

        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).user_is_editor()
            self.assertEqual(res, False)

        self.user_fred.roles += [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).user_is_editor()
            self.assertEqual(res, True)

        self.user_fred.roles = [self.role_contributor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).user_is_editor()
            self.assertEqual(res, False)

    def test_user_is_contributor(self):
        request = self.DummyRequest()
        res = BaseView(request).user_is_contributor()
        self.assertEqual(res, False)

        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_bob.login):
            res = BaseView(request).user_is_contributor()
            self.assertEqual(res, False)

            self.user_bob.roles = [self.role_contributor]
            res = BaseView(request).user_is_contributor()
            self.assertEqual(res, True)

    def test__is_json(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        res = BaseView(request)._is_json()
        self.assertEqual(res, False)

        request.matched_route.name = 'test_json'
        res = BaseView(request)._is_json()
        self.assertEqual(res, True)

    def test_get_editable_logins_admin(self):
        request = self.DummyRequest()
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_admin.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [])

        self.user_fred.roles += [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_admin.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

        self.user_bob.roles += [self.role_contributor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_admin.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_bob.login, self.user_fred.login])

        self.user_admin.config = UserConfig(root_path='/admin/path')
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_admin.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_admin.login,
                                   self.user_bob.login,
                                   self.user_fred.login])

    def test_get_editable_logins_editor(self):
        request = self.DummyRequest()
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

        self.user_bob.roles += [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

        self.user_fred.roles += [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

        self.user_bob.roles += [self.role_contributor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_bob.login, self.user_fred.login])

    def test_get_editable_logins_contributor(self):
        request = self.DummyRequest()
        self.user_fred.roles = [self.role_contributor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

        self.user_bob.roles += [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

        self.user_bob.roles += [self.role_contributor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_fred.login):
            res = BaseView(request).get_editable_logins()
            self.assertEqual(res, [self.user_fred.login])

    @login_user('Fred')
    def test__response_editor(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route_json'

        res = BaseView(request)._response({})
        self.assertEqual(res, {})

        res = BaseView(request)._response({'key': 'value'})
        self.assertEqual(res, {'key': 'value'})

        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': self.user_fred.login})

        request.session = {'editor_login': 'Bob'}
        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': 'Bob', 'logins': ['Fred']})

        res = BaseView(request)._response({'key': 'value'})
        self.assertEqual(res, {'editor_login': 'Bob',
                               'logins': ['Fred'],
                               'key': 'value'})

    @login_user('Admin')
    def test__response_admin(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': self.user_admin.login})

        request.session = {'editor_login': 'Bob'}
        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': 'Bob'})

    @login_user('Bob')
    def test__response_bob_admin(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': self.user_bob.login})

        request.session = {'editor_login': 'Bob'}
        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': 'Bob'})

        self.user_fred.roles = [self.role_editor, self.role_contributor]
        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': 'Bob', 'logins': ['Fred']})

    @login_user('LeResKP')
    def test__response_lereskp(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': 'LeResKP'})


class TestBaseUserView(BaseTestCase):

    def test___init__(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        try:
            BaseUserView(request)
            assert(False)
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

        request.matched_route.name = 'test_json'
        try:
            BaseUserView(request)
            assert(False)
        except JSONHTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

        request.matched_route.name = 'login_selection'
        res = BaseUserView(request)
        self.assertFalse(res.root_path)
        self.assertTrue(res)

        request.matched_route.name = 'test'
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        res = BaseUserView(request)
        self.assertTrue(res.root_path)
        self.assertTrue(res)
