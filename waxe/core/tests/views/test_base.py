from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
import pyramid.httpexceptions as exc
from webob.multidict import MultiDict
from mock import patch

from ..testing import BaseTestCase, LoggedBobTestCase, login_user
from waxe.core.models import (
    UserConfig,
    DBSession,
    UserOpenedFile,
    UserCommitedFile
)
from waxe.core import security
from waxe.core.views.base import (
    BaseView,
    BaseUserView,
    JSONView,
)


class EmptyClass(object):
    pass


class TestJSONView(BaseTestCase):

    def test_req_get(self):
        request = testing.DummyRequest()
        view = JSONView(request)
        res = view.req_get
        self.assertEqual(res, {})

    def test_req_post(self):
        request = testing.DummyRequest()
        view = JSONView(request)
        res = view.req_post
        self.assertEqual(res, {})

        request.body = '{"hello": "world"}'
        request.json_body = {"hello": "world"}
        res = view.req_post
        self.assertEqual(res, {'hello': 'world'})

        request.POST = {'key': 'value'}
        res = view.req_post
        self.assertEqual(res, {'key': 'value'})

    def test_req_post_getall(self):
        request = testing.DummyRequest()
        view = JSONView(request)
        res = view.req_post_getall('key')
        self.assertEqual(res, {})

        request.body = '{"hello": ["world"]}'
        request.json_body = {"hello": ["world"]}
        res = view.req_post_getall('hello')
        self.assertEqual(res, ['world'])

        request.POST = MultiDict([('key', 'value')])
        res = view.req_post_getall('key')
        self.assertEqual(res, ['value'])


class TestBaseView(BaseTestCase):

    def setUp(self):
        super(TestBaseView, self).setUp()
        self.config.registry.settings.update({
            'pyramid_auth.no_routes': 'true',
            'pyramid_auth.cookie.secret': 'scrt',
            'pyramid_auth.cookie.callback': ('waxe.core.security.'
                                             'get_user_permissions'),
            'pyramid_auth.cookie.validate_function': (
                'waxe.core.security.validate_password'),
        })
        self.config.include('pyramid_auth')

    def DummyRequest(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        return request

    def test___init__(self):
        request = self.DummyRequest()
        with patch('waxe.core.security.get_userid_from_request',
                   return_value='Unexisting'):
            obj = BaseView(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user_login, 'Unexisting')
            # The user has been inserted
            self.assertEqual(obj.logged_user.login, 'Unexisting')
            self.assertEqual(obj.current_user, obj.logged_user)
            self.assertEqual(obj.root_path, None)

        with patch('waxe.core.security.get_userid_from_request',
                   return_value=self.user_bob.login):
            obj = BaseView(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user_login, self.user_bob.login)
            self.assertEqual(obj.logged_user, self.user_bob)
            self.assertEqual(obj.current_user, self.user_bob)
            self.assertEqual(obj.root_path, self.user_bob.config.root_path)

    @login_user('Bob')
    def test_custom_route_path(self):
        request = self.DummyRequest()
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        obj = BaseView(request)
        path = obj.request.custom_route_path('home')
        self.assertEqual(path, '/home')

        # Make sure it works without current_user.
        # This special case come for example when the logged_user is not in the
        # DB and no account is selected.
        obj.current_user = None
        path = obj.request.custom_route_path('home')
        self.assertEqual(path, '/home')

    def test_user_is_admin(self):
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value='Unexisting'):
            request = self.DummyRequest()
            res = BaseView(request).user_is_admin()
            self.assertEqual(res, False)

        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=self.user_bob.login):
            res = BaseView(request).user_is_admin()
            self.assertEqual(res, True)

    def test_user_is_editor(self):
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value='Unexisting'):
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
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value='Unexisting'):
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

    @login_user('Bob')
    def test_has_versioning(self):
        request = self.DummyRequest()
        res = BaseView(request).has_versioning()
        self.assertEqual(res, False)

        request.registry.settings['waxe.versioning'] = 'true'
        res = BaseView(request).has_versioning()
        self.assertEqual(res, False)

        self.user_bob.config.use_versioning = True
        res = BaseView(request).has_versioning()
        self.assertEqual(res, True)

        request.registry.settings['waxe.versioning'] = 'false'
        res = BaseView(request).has_versioning()
        self.assertEqual(res, False)


class TestBaseUserView(BaseTestCase):

    def test___init__(self):
        self.config.testing_securitypolicy(userid='Unexisting',
                                           permissive=True)
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        try:
            BaseUserView(request)
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'root path not defined')

        self.config.testing_securitypolicy(userid='Bob',
                                           permissive=True)
        request.matched_route.name = 'test'
        res = BaseUserView(request)
        self.assertTrue(res.root_path)
        self.assertTrue(res)

    def test___init___bad_user(self):
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        request.matchdict['login'] = 'unexisting'
        try:
            res = BaseUserView(request)
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), "The user doesn't exist")

        # Current user
        request.matchdict['login'] = 'Bob'
        res = BaseUserView(request)
        self.assertEqual(res.current_user, res.logged_user)

        self.user_fred.roles += [self.role_editor]
        request.matchdict['login'] = 'Fred'
        res = BaseUserView(request)
        self.assertEqual(res.current_user, self.user_fred)

    def test_get_search_dirname(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        view = BaseUserView(request)
        res = view.get_search_dirname()
        self.assertEqual(res, None)

        request.registry.settings['whoosh.path'] = '/tmp/fake'
        view = BaseUserView(request)
        res = view.get_search_dirname()
        self.assertEqual(res, '/tmp/fake/user-2')

    def test_add_opened_file(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'

        # No logged user
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        view = BaseUserView(request)
        view.logged_user = None
        res = view.add_opened_file('/tmp')
        self.assertEqual(res, False)

        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        view = BaseUserView(request)
        res = view.add_opened_file('/tmp')
        self.assertEqual(len(self.user_bob.opened_files), 1)
        self.assertEqual(self.user_bob.opened_files[0].path, '/tmp')
        self.assertEqual(res, None)

        # We need to call flush to make the object deletable
        DBSession.flush()
        # The previous same path will be deleted and the new one added
        res = view.add_opened_file('/tmp')
        self.assertEqual(len(self.user_bob.opened_files), 1)
        self.assertEqual(self.user_bob.opened_files[0].path, '/tmp')

        view.current_user = self.user_fred
        self.user_bob.config = None
        res = view.add_opened_file('/tmp-1')
        self.assertEqual(res, None)
        self.assertEqual(self.user_bob.opened_files[0].iduser_owner,
                         self.user_fred.iduser)

    def test_add_commited_file(self):
        # Same test as test_add_opened_file
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'

        # No logged user
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        view = BaseUserView(request)
        view.logged_user = None
        res = view.add_commited_file('/tmp')
        self.assertEqual(res, False)

        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        view = BaseUserView(request)
        res = view.add_commited_file('/tmp')
        self.assertEqual(len(self.user_bob.commited_files), 1)
        self.assertEqual(self.user_bob.commited_files[0].path, '/tmp')
        self.assertEqual(res, None)

        # We need to call flush to make the object deletable
        DBSession.flush()
        # The previous same path will be deleted and the new one added
        res = view.add_commited_file('/tmp')
        self.assertEqual(len(self.user_bob.commited_files), 1)
        self.assertEqual(self.user_bob.commited_files[0].path, '/tmp')

        view.current_user = self.user_fred
        self.user_bob.config = None
        res = view.add_commited_file('/tmp-1')
        self.assertEqual(res, None)
        self.assertEqual(self.user_bob.commited_files[0].iduser_commit,
                         self.user_fred.iduser)

    def test_add_indexation_task(self):
        request = testing.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'test'
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        view = BaseUserView(request)
        # No whoosh path
        res = view.add_indexation_task()
        self.assertEqual(res, None)

        with patch('sqla_taskq.models.Task.create') as m:
            request.registry.settings['whoosh.path'] = '/tmp/fake'
            res = view.add_indexation_task()
            m.assert_called_once()
