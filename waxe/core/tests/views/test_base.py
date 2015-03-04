from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
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
    NavigationView,
    BaseUserView,
    JSONHTTPBadRequest,
    NAV_EDIT,
    NAV_EDIT_TEXT,
    NAV_DIFF,
)


class EmptyClass(object):
    pass


def fake__get_xmltool_transform():
    return 'Hello world'


class TestBaseView(BaseTestCase):

    def setUp(self):
        super(TestBaseView, self).setUp()
        self.config.registry.settings.update({
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.core.security.'
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

        with patch('waxe.core.security.get_userid_from_request',
                   return_value=self.user_bob.login):
            obj = BaseView(request)
            self.assertEqual(obj.request, request)
            self.assertEqual(obj.logged_user_login, self.user_bob.login)
            self.assertEqual(obj.logged_user, self.user_bob)
            self.assertEqual(obj.current_user, self.user_bob)
            self.assertEqual(obj.root_path, None)

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

    def test__get_xmltool_transform(self):
        request = self.DummyRequest()
        res = BaseView(request)._get_xmltool_transform()
        self.assertEqual(res, None)

        func_str = '%s.fake__get_xmltool_transform' % (
            fake__get_xmltool_transform.__module__)

        request.registry.settings['waxe.xml.xmltool.transform'] = func_str
        func = BaseView(request)._get_xmltool_transform()
        res = func()
        self.assertEqual(res, 'Hello world')

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
        expected = {
            'editor_login': self.user_fred.login,
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        }
        self.assertEqual(res, expected)

        view = BaseView(request)
        view.current_user = self.user_bob
        view.root_path = 'something'
        res = view._response({})
        expected = {
            'editor_login': 'Bob',
            'logins': ['Fred'],
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        }
        self.assertEqual(res, expected)

        res = view._response({'key': 'value'})
        expected = {
            'editor_login': 'Bob',
            'logins': ['Fred'],
            'key': 'value',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        }
        self.assertEqual(res, expected)

    @login_user('Admin')
    def test__response_admin(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': self.user_admin.login,
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        view = BaseView(request)
        view.current_user = self.user_bob
        view.root_path = 'something'
        res = view._response({})
        self.assertEqual(res, {
            'editor_login': 'Bob',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        request.registry.settings['waxe.versioning'] = 'true'
        view = BaseView(request)
        view.current_user = self.user_bob
        res = view._response({})
        self.assertEqual(res, {
            'editor_login': 'Bob',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        # The user which we edit support versioning!
        self.user_bob.config.use_versioning = True
        res = view._response({})
        self.assertEqual(res, {
            'editor_login': 'Bob',
            'versioning': True,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        self.user_admin.config = UserConfig()
        self.user_admin.config.tree_position = 'tree_position'
        self.user_admin.config.readonly_position = 'readonly_position'
        res = view._response({})
        self.assertEqual(res, {
            'editor_login': 'Bob',
            'versioning': True,
            'search': False,
            'layout_readonly_position': 'readonly_position',
            'layout_tree_position': 'tree_position',
            'root_template_path': None,
            'xml_renderer': False,
        })

    def test__response_unexisting_user(self):
        # Will not fail even if the editor is not in the DB
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'
        o = BaseView(request)
        o.root_path = None
        o.logged_user_login = 'John'
        o.current_user = None
        res = o._response({})
        expected = {
            'editor_login': 'John',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test__response_bob_admin(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': self.user_bob.login,
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': 'Bob',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        self.user_fred.roles = [self.role_editor, self.role_contributor]
        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': 'Bob',
            'logins': ['Fred'],
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

    @login_user('LeResKP')
    def test__response_lereskp(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': 'LeResKP',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

    @login_user('Admin')
    def test__response_seach(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': self.user_admin.login,
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

        request.registry.settings['whoosh.path'] = '/tmp/fake'
        res = BaseView(request)._response({})
        self.assertEqual(res, {
            'editor_login': self.user_admin.login,
            'versioning': False,
            'search': True,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'root_template_path': None,
            'xml_renderer': False,
        })

    def test__get_last_files_no_current_user(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.route_path = lambda *args, **kw: '/filepath'
        res = BaseView(request)._get_last_files()
        self.assertEqual(res, '')

    @login_user('Bob')
    def test__get_last_files(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.route_path = lambda *args, **kw: '/filepath'
        res = BaseView(request)._get_last_files()
        self.assertEqual(res, '')

        request.current_user = self.user_bob
        self.user_bob.opened_files = [UserOpenedFile(path='/path')]
        res = BaseView(request)._get_last_files()
        self.assertTrue('Last opened files' in res)
        self.assertFalse('Last commited files' in res)
        expected = '<a href="/filepath" data-href="/filepath">/path</a>'
        self.assertTrue(expected in res)
        self.assertFalse('/cpath' in res)

        self.user_bob.opened_files[0].iduser_owner = self.user_fred.iduser
        res = BaseView(request)._get_last_files()
        self.assertTrue('Last opened files' in res)
        self.assertFalse('Last commited files' in res)
        expected = '<a href="/filepath">/path</a> (Fred)'
        self.assertTrue(expected in res)
        self.assertFalse('/cpath' in res)

        self.user_bob.commited_files = [UserCommitedFile(path='/cpath')]
        res = BaseView(request)._get_last_files()
        self.assertTrue('Last opened files' in res)
        self.assertTrue('Last commited files' in res)
        self.assertTrue('/path' in res)
        self.assertTrue('/cpath' in res)


class TestNavigationView(LoggedBobTestCase):

    def test__generate_link_tag(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        obj = NavigationView(request)
        res = obj._generate_link_tag(name='Hello', relpath='/path',
                                     route_name='test')
        expected = (
            '<a data-href="/filepath" href="/filepath">Hello</a>'
        )
        self.assertEqual(res, expected)

        res = obj._generate_link_tag(name='Hello', relpath='/path',
                                     route_name='test',
                                     data_href_name='data-modal-href')
        expected = (
            '<a data-modal-href="/filepath" href="/filepath">Hello</a>'
        )
        self.assertEqual(res, expected)

        res = obj._generate_link_tag(name='Hello', relpath='/path',
                                     route_name='test',
                                     data_href_name='data-modal-href',
                                     extra_attrs=[('id', 'myid')])
        expected = (
            '<a data-modal-href="/filepath" href="/filepath" id="myid">'
            'Hello</a>'
        )
        self.assertEqual(res, expected)

        res = obj._generate_link_tag(name='Hello', relpath='/path',
                                     route_name=None,
                                     data_href_name='data-modal-href',
                                     extra_attrs=[('id', 'myid')])
        expected = (
            '<a href="#" id="myid">Hello</a>'
        )
        self.assertEqual(res, expected)

    def test__get_breadcrumb_data(self):
        request = testing.DummyRequest()
        res = NavigationView(request)._get_breadcrumb_data('')
        expected = [('root', '')]
        self.assertEqual(res, expected)

        res = NavigationView(request)._get_breadcrumb_data('folder1')
        expected = [('root', ''), ('folder1', 'folder1')]
        self.assertEqual(res, expected)

        res = NavigationView(request)._get_breadcrumb_data(
            'folder1/folder2/folder3',
            'folder1/folder2')
        expected = [('root', 'folder1/folder2'),
                    ('folder3', 'folder1/folder2/folder3')]
        self.assertEqual(res, expected)

    def test__get_breadcrumb(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = NavigationView(request)._get_breadcrumb('folder1')
        expected = (
            '<li>'
            '<a data-href="/filepath" href="/filepath">root</a>'
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
            '<a data-href="/filepath" href="/filepath">root</a>'
            '</li>'
        )
        self.assertEqual(res, expected)

        res = NavigationView(request)._get_breadcrumb('',
                                                      data_href_name='data-modal-href', force_link=True)
        expected = (
            '<li>'
            '<a data-modal-href="/filepath" href="/filepath">root</a>'
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
        res = view.add_opened_file('/tmp-1')
        self.assertEqual(res, False)

        self.user_bob.config = None
        res = view.add_opened_file('/tmp-1')
        self.assertEqual(res, None)
        self.assertEqual(self.user_bob.opened_files[0].iduser_owner,
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

        with patch('taskq.models.Task.create') as m:
            request.registry.settings['whoosh.path'] = '/tmp/fake'
            res = view.add_indexation_task()
            m.assert_called_once()

    def test__get_nav_editor(self):
        class C(object): pass
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        self.config.testing_securitypolicy(userid='Bob', permissive=True)

        res = BaseUserView(request)._get_nav_editor(
            'file1.xml',
            kind=NAV_EDIT)
        expected = (
            '<ul class="nav nav-tabs">'
            '<li class="active"><a>XML</a></li>'
            '<li><a href="/edit_text/filepath" '
            'data-href="/edit_text_json/filepath">Source</a></li>'
            '</ul>'
        )
        self.assertEqual(res, expected)

        request.registry.settings['waxe.versioning'] = 'true'
        self.user_bob.config.use_versioning = True
        res = BaseUserView(request)._get_nav_editor(
            'file1.xml',
            kind=NAV_EDIT)
        expected = (
            '<ul class="nav nav-tabs">'
            '<li class="active"><a>XML</a></li>'
            '<li><a href="/edit_text/filepath" '
            'data-href="/edit_text_json/filepath">Source</a></li>'
            '<li><a href="/versioning_diff/filepath" '
            'data-href="/versioning_diff_json/filepath">Diff</a></li>'
            '</ul>'
        )
        self.assertEqual(res, expected)

        res = BaseUserView(request)._get_nav_editor(
            'file1.xml',
            kind=NAV_EDIT_TEXT)
        expected = (
            '<ul class="nav nav-tabs">'
            '<li>'
            '<a href="/edit/filepath" data-href="/edit_json/filepath">XML</a>'
            '</li>'
            '<li class="active"><a>Source</a></li>'
            '<li>'
            '<a href="/versioning_diff/filepath" '
            'data-href="/versioning_diff_json/filepath">'
            'Diff</a></li>'
            '</ul>'
        )
        self.assertEqual(res, expected)

