from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
from mock import patch

from ..testing import BaseTestCase, LoggedBobTestCase, login_user
from waxe.models import UserConfig
from waxe import security
from waxe.views.base import (
    BaseView,
    NavigationView,
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
            self.assertEqual(obj.root_path, None)

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

        view = BaseView(request)
        view.current_user = self.user_bob
        view.root_path = 'something'
        res = view._response({})
        self.assertEqual(res, {'editor_login': 'Bob', 'logins': ['Fred']})

        res = view._response({'key': 'value'})
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

        view = BaseView(request)
        view.current_user = self.user_bob
        view.root_path = 'something'
        res = view._response({})
        self.assertEqual(res, {'editor_login': 'Bob'})

        request.registry.settings['versioning'] = True
        res = view._response({})
        self.assertEqual(res, {'editor_login': 'Bob'})

        # The user which we edit support versioning!
        self.user_bob.config.use_versioning = True
        res = view._response({})
        self.assertEqual(res, {'editor_login': 'Bob',
                               'versioning': True})

        # Will not fail even if the editor is not in the DB
        o = BaseView(request)
        o.root_path = None
        o.logged_user_login = 'John'
        res = o._response({})
        self.assertEqual(res, {'editor_login': 'John'})

    @login_user('Bob')
    def test__response_bob_admin(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {'editor_login': self.user_bob.login})

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


class TestNavigationView(LoggedBobTestCase):

    def test__get_breadcrumb_data(self):
        request = testing.DummyRequest()
        res = NavigationView(request)._get_breadcrumb_data('')
        expected = [('root', '')]
        self.assertEqual(res, expected)

        res = NavigationView(request)._get_breadcrumb_data('folder1')
        expected = [('root', ''), ('folder1', 'folder1')]
        self.assertEqual(res, expected)

    def test__get_breadcrumb(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = NavigationView(request)._get_breadcrumb('folder1')
        expected = (
            '<li>'
            '<a data-href="/filepath" href="/filepath">root</a> '
            '</li>'
            '<li class="active">folder1</li>'
        )
        self.assertEqual(res, expected)

        res = NavigationView(request)._get_breadcrumb('')
        expected = (
            '<li class="active">root</li>'
        )
        self.assertEqual(res, expected)

        res = NavigationView(request)._get_breadcrumb('', force_link=True)
        expected = (
            '<li>'
            '<a data-href="/filepath" href="/filepath">root</a> '
            '</li>'
        )
        self.assertEqual(res, expected)


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

        request.matched_route.name = 'redirect'
        res = BaseUserView(request)
        self.assertFalse(res.root_path)
        self.assertTrue(res)

        request.matched_route.name = 'test'
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        res = BaseUserView(request)
        self.assertTrue(res.root_path)
        self.assertTrue(res)

    def test___init___bad_user(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        request.matchdict['login'] = 'unexisting'
        try:
            res = BaseUserView(request)
            assert(False)
        except HTTPBadRequest, e:
            self.assertEqual(str(e), "The user doesn't exist")

        request.matched_route.name = 'test_json'
        try:
            res = BaseUserView(request)
            assert(False)
        except JSONHTTPBadRequest, e:
            self.assertEqual(str(e), "The user doesn't exist")

        # Current user
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        request.matchdict['login'] = 'Bob'
        res = BaseUserView(request)
        self.assertEqual(res.current_user, res.logged_user)

        self.user_fred.roles += [self.role_editor]
        request.matchdict['login'] = 'Fred'
        res = BaseUserView(request)
        self.assertEqual(res.current_user, self.user_fred)
