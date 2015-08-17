import os
from pyramid import testing
import pyramid.httpexceptions as exc
import json
from ..testing import BaseTestCase, WaxeTestCase, login_user
from waxe.core.views.index import IndexView, IndexUserView
from waxe.core import security
from waxe.core.models import UserOpenedFile, UserCommitedFile


class EmptyClass(object):
    pass


class TestIndexView(BaseTestCase):

    def setUp(self):
        super(TestIndexView, self).setUp()
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

    @login_user('Unexisting')
    def test__profile_unexisting_user(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route_json'
        request.registry.settings['dtd_urls'] = 'http://dtd_url'

        res = IndexView(request).profile()
        expected = {
            'logins': [],
            'has_file': False,
            'login': 'Unexisting',
            'layout_tree_position': 'west',
            'layout_readonly_position': 'south'
        }
        self.assertEqual(res, expected)

    @login_user('Fred')
    def test__profile_editor(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route_json'
        request.registry.settings['dtd_urls'] = 'http://dtd_url'

        res = IndexView(request).profile()
        expected = {
            'logins': ['Fred'],
            'has_file': True,
            'login': 'Fred',
            'layout_tree_position': 'west',
            'layout_readonly_position': 'south'
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test__profile_admin(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'
        request.registry.settings['dtd_urls'] = 'http://dtd_url'

        res = IndexView(request).profile()
        expected = {
            'logins': ['Bob'],
            'has_file': True,
            'login': 'Bob',
            'layout_tree_position': 'west',
            'layout_readonly_position': 'south'
        }
        self.assertEqual(res, expected)

        self.user_fred.roles = [self.role_editor, self.role_contributor]
        self.user_bob.config.tree_position = 'tree'
        self.user_bob.config.readonly_position = 'readonly'

        res = IndexView(request).profile()
        expected = {
            'logins': ['Bob', 'Fred'],
            'has_file': True,
            'login': 'Bob',
            'layout_tree_position': 'tree',
            'layout_readonly_position': 'readonly'
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_last_files(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.route_path = lambda *args, **kw: '/filepath'
        res = IndexView(request).last_files()
        expected = {
            'opened_files': [],
            'commited_files': [],
        }
        self.assertEqual(res, expected)

        request.current_user = self.user_bob
        self.user_bob.opened_files = [UserOpenedFile(path='/path')]
        res = IndexView(request).last_files()
        expected = {
            'opened_files': [{'path': '/path', 'user': ''}],
            'commited_files': [],
        }
        self.assertEqual(res, expected)

        self.user_bob.opened_files[0].user_owner = self.user_fred
        res = IndexView(request).last_files()
        expected = {
            'opened_files': [{'path': '/path', 'user': 'Fred'}],
            'commited_files': [],
        }
        self.assertEqual(res, expected)

        self.user_bob.commited_files = [UserCommitedFile(path='/cpath')]
        res = IndexView(request).last_files()
        expected = {
            'opened_files': [{'path': '/path', 'user': 'Fred'}],
            'commited_files': [{'path': '/cpath', 'user': ''}],
        }
        self.assertEqual(res, expected)


class TestIndexUserView(BaseTestCase):

    def setUp(self):
        super(TestIndexUserView, self).setUp()
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

    @login_user('Fred')
    def test_account_profile_editor(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route_json'
        request.registry.settings['dtd_urls'] = 'http://dtd_url'

        res = IndexUserView(request).account_profile()
        expected = {
            'account_profile': {
                'templates_path': None,
                'has_versioning': False,
                'dtd_urls': ['http://dtd_url'],
                'has_search': False,
                'login': 'Fred',
                'has_template_files': False,
                'has_xml_renderer': False
            }
        }
        self.assertEqual(res, expected)

        request.registry.settings['whoosh.path'] = 'search_path'
        request.registry.settings['waxe.renderers'] = 'render'
        path = os.path.join(os.getcwd(), 'waxe', 'core', 'tests', 'files')
        self.user_fred.config.root_path = path
        self.user_fred.config.root_template_path = os.path.join(path,
                                                                'folder1')
        res = IndexUserView(request).account_profile()
        expected = {
            'account_profile': {
                'templates_path': 'folder1',
                'has_versioning': False,
                'dtd_urls': ['http://dtd_url'],
                'has_search': True,
                'login': 'Fred',
                'has_template_files': True,
                'has_xml_renderer': True
            }
        }
        self.assertEqual(res, expected)

        request.GET = {'full': True}
        res = IndexUserView(request).account_profile()
        self.assertTrue('account_profile' in res)
        self.assertTrue('user_profile' in res)


class FunctionalTestIndexView(WaxeTestCase):

    def test_forbidden(self):
        self.testapp.get('/api/1/profile.json', status=401)
        self.testapp.get('/api/1/last-files.json', status=401)

    @login_user('Admin')
    def test_profile(self):
        res = self.testapp.get('/api/1/profile.json', status=200)
        dic = json.loads(res.body)
        self.assertTrue('login' in dic)

    @login_user('Admin')
    def test_last_files(self):
        res = self.testapp.get('/api/1/last-files.json', status=200)
        dic = json.loads(res.body)
        expected = {
            'opened_files': [],
            'commited_files': [],
        }
        self.assertEqual(dic, expected)


class FunctionalTestIndexUserView(WaxeTestCase):

    def test_forbidden(self):
        self.testapp.get('/api/1/account/admin/account-profile.json', status=401)

    @login_user('Bob')
    def test_account_profile(self):
        res = self.testapp.get('/api/1/account/Bob/account-profile.json',
                               status=200)
        self.assertTrue(res)
