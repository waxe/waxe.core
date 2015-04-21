from pyramid import testing
import json
from ..testing import BaseTestCase, WaxeTestCase, login_user
from waxe.core.views.index import IndexView
from waxe.core import security


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

    @login_user('Fred')
    def test__profile_editor(self):
        request = self.DummyRequest()
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route_json'
        request.registry.settings['dtd_urls'] = 'http://dtd_url'

        res = IndexView(request).profile()
        expected = {
            'base_path': '/account/Fred',
            'dtd_urls': ['http://dtd_url'],
            'editor_login': 'Fred',
            'extenstions': ['.xml'],
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'login': 'Fred',
            'logins': ['Fred'],
            'root_path': self.user_fred.config.root_path,
            'root_template_path': None,
            'search': False,
            'versioning': False,
            'xml_renderer': False
        }
        self.assertEqual(res, expected)

        # Search & versioning
        request.registry.settings['whoosh.path'] = '/tmp/fake'
        request.registry.settings['waxe.versioning'] = 'true'
        self.user_bob.config.use_versioning = True

        res = IndexView(request).profile()
        expected = {
            'base_path': '/account/Fred',
            'dtd_urls': ['http://dtd_url'],
            'editor_login': 'Fred',
            'extenstions': ['.xml'],
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'login': 'Fred',
            'logins': ['Fred'],
            'root_path': self.user_fred.config.root_path,
            'root_template_path': None,
            'search': True,
            'versioning': True,
            'xml_renderer': False
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
            'base_path': '/account/Bob',
            'dtd_urls': ['http://dtd_url'],
            'editor_login': 'Bob',
            'extenstions': ['.xml'],
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'login': 'Bob',
            'logins': ['Bob'],
            'root_path': self.user_bob.config.root_path,
            'root_template_path': None,
            'search': False,
            'versioning': False,
            'xml_renderer': False
        }

        self.assertEqual(res, expected)

        self.user_fred.roles = [self.role_editor, self.role_contributor]

        res = IndexView(request).profile()
        self.assertEqual(res, {
            'base_path': '/account/Bob',
            'dtd_urls': ['http://dtd_url'],
            'editor_login': 'Bob',
            'extenstions': ['.xml'],
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'login': 'Bob',
            'logins': ['Bob', 'Fred'],
            'root_path': self.user_bob.config.root_path,
            'root_template_path': None,
            'search': False,
            'versioning': False,
            'xml_renderer': False
        })

        view = IndexView(request)
        view.current_user = self.user_fred
        res = view.profile()
        self.assertEqual(res, {
            'base_path': '/account/Fred',
            'dtd_urls': ['http://dtd_url'],
            'editor_login': 'Fred',
            'extenstions': ['.xml'],
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
            'login': 'Bob',
            'logins': ['Bob', 'Fred'],
            'root_path': self.user_bob.config.root_path,
            'root_template_path': None,
            'search': False,
            'versioning': False,
            'xml_renderer': False
        })


class FunctionalTestIndexView2(WaxeTestCase):

    def test_forbidden(self):
        self.testapp.get('/profile.json', status=401)

    @login_user('Admin')
    def test_profile(self):
        res = self.testapp.get('/profile.json', status=200)
        dic = json.loads(res.body)
        self.assertTrue('login' in dic)
