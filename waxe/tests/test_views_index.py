import os
import simplejson
from pyramid import testing
from ..testing import WaxeTestCase, login_user
from mock import patch
from ..models import (
    DBSession,
    User,
    UserConfig,
    Role,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR
)

from ..views.index import (
    Views,
    HTTPBadRequest,
    JSONHTTPBadRequest,
    bad_request
)
from urllib2 import HTTPError


class TestViews(WaxeTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config = testing.setUp(settings=self.settings)

    def tearDown(self):
        testing.tearDown()
        super(TestViews, self).tearDown()

    def test_class_init(self):
        request = testing.DummyRequest(root_path=None)
        class C(object): pass
        request.matched_route = C()
        request.matched_route.name = 'route'
        try:
            Views(request)
            assert 0
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

        request.matched_route.name = 'route_json'
        try:
            Views(request)
            assert 0
        except JSONHTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

        request.matched_route.name = 'login_selection'
        o = Views(request)
        self.assertEqual(o.request, request)

    def test__is_json(self):
        request = testing.DummyRequest(root_path='/path', user=self.user_bob)
        class C(object): pass
        request.matched_route = C()
        request.matched_route.name = 'route'
        self.assertFalse(Views(request)._is_json())

        request.matched_route.name = 'route_json'
        self.assertTrue(Views(request)._is_json())

    def test__response(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest(root_path='/path', user=self.user_bob)
        with patch('waxe.views.index.Views._is_json', return_value=True):
            res = Views(request)._response({})
            self.assertEqual(res, {})

        with patch('waxe.views.index.Views._is_json', return_value=False):
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': self.user_bob.login})
            request.session = {'editor_login': 'Fred'}

            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': 'Fred'})

            contributor = User(login='contributor', password='pass1')
            contributor.roles = [Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()]
            contributor.config = UserConfig(root_path='/path')
            DBSession.add(contributor)
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': 'Fred',
                                   'logins': ['contributor']})

            request.session = {}
            request.root_path = None
            class C(object): pass
            request.matched_route = C()
            request.matched_route.name = 'login_selection'
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': 'Account',
                                   'logins': ['contributor']})

    def test__get_navigation(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path)
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_navigation()
        expected = ('<ul id="file-navigation" data-path="">\n'
                    '    <li>'
                    '<a data-href="/filepath" class="folder">folder1</a>'
                    '</li>\n'
                    '    <li>'
                    '<a data-href="/filepath" class="file">file1.xml</a>'
                    '</li>\n'
                    '</ul>\n')
        self.assertEqual(res, expected)

        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path,
                                       params={'path': 'folder1'})
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_navigation()
        expected = ('<ul id="file-navigation" data-path="folder1">\n'
                    '    <li>'
                    '<a data-href="/filepath" class="previous">..</a>'
                    '</li>\n'
                    '    <li>'
                    '<a data-href="/filepath" class="file">file2.xml</a>'
                    '</li>\n'
                    '</ul>\n')
        self.assertEqual(res, expected)

    def test__get_breadcrumb(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path)
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_breadcrumb('folder1')
        expected = (
            '<li>'
            '<a data-href="/filepath">root</a> '
            '<span class="divider">/</span>'
            '</li>'
            '<li class="active">folder1</li>'
        )
        self.assertEqual(res, expected)

        res = Views(request)._get_breadcrumb('')
        expected = (
            '<li class="active">root</li>'
        )
        self.assertEqual(res, expected)

        res = Views(request)._get_breadcrumb('', force_link=True)
        expected = (
            '<li>'
            '<a data-href="/filepath">root</a> '
            '</li>'
        )
        self.assertEqual(res, expected)

    def test_home(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest(root_path='/path', user=self.user_bob)
        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" data-path="">\n</ul>\n',
            'editor_login': u'Bob'
        }
        with patch('waxe.views.index.Views._is_json', return_value=False):
            res = Views(request).home()
            self.assertEqual(res, expected)

        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" data-path="">\n</ul>\n',
        }
        with patch('waxe.views.index.Views._is_json', return_value=True):
            res = Views(request).home()
            self.assertEqual(res, expected)

    def test_login_selection(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest(root_path='/path', user=self.user_bob)
        try:
            res = Views(request).login_selection()
            assert 0
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'Invalid login')

        request = testing.DummyRequest(root_path='/path', user=self.user_bob,
                                       params={'login': 'editor'})
        try:
            res = Views(request).login_selection()
            assert 0
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'Invalid login')

        editor = User(login='editor', password='pass1')
        editor.roles = [Role.query.filter_by(name=ROLE_EDITOR).one()]
        editor.config = UserConfig(root_path='/path')
        DBSession.add(editor)

        res = Views(request).login_selection()
        self.assertEqual(res.status, "302 Found")
        self.assertEqual(res.location, '/')
        expected = {'editor_login': 'editor', 'root_path': '/path'}
        self.assertEqual(request.session, expected)

    def test_bad_request(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest(user=self.user_bob)
        dic = bad_request(request)
        self.assertEqual(len(dic), 1)
        self.assertTrue('There is a problem with your configuration' in
                        dic['content'])

        editor = User(login='editor', password='pass1')
        editor.roles = [Role.query.filter_by(name=ROLE_EDITOR).one()]
        editor.config = UserConfig(root_path='/path')
        DBSession.add(editor)

        request.route_path = lambda *args, **kw: '/editorpath'
        dic = bad_request(request)
        expected = {'content': u'  <a href="/editorpath">editor</a>\n'}
        self.assertEqual(dic, expected)

    def test_edit(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path, user=self.user_bob)
        expected = {
            'error_msg': 'A filename should be provided',
        }
        res = Views(request).edit()
        self.assertEqual(res, expected)

        with patch('xmltool.generate_form', return_value='My form content'):
            expected = {
                'content': 'My form content',
                'breadcrumb': ('<li><a data-href="/filepath">root</a> '
                               '<span class="divider">/</span></li>'
                               '<li class="active">file1.xml</li>')
            }
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'filename': 'file1.xml'})
            request.route_path = lambda *args, **kw: '/filepath'
            res = Views(request).edit()
            self.assertEqual(res, expected)

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.generate_form') as m:
            m.side_effect = raise_func
            expected = {
                'error_msg': 'My error',
            }
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'filename': 'file1.xml'})
            res = Views(request).edit()
            self.assertEqual(res, expected)

        def raise_http_func(*args, **kw):
            raise HTTPError('http://url', 404, 'Not found', [], None)

        with patch('xmltool.generate_form') as m:
            m.side_effect = raise_http_func
            expected = {
                'error_msg': 'The dtd of file1.xml can\'t be loaded.',
            }
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'filename': 'file1.xml'})
            res = Views(request).edit()
            self.assertEqual(res, expected)


class FunctionalTestViews(WaxeTestCase):

    def test_home_forbidden(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2F')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Fred')
    def test_home_bad_login(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(res.location,
                         'http://localhost/forbidden')

    @login_user('Bob')
    def test_home(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue(
            'There is a problem with your configuration' in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

        DBSession.remove()
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path='/path')
        res = self.testapp.get('/', status=200)
        self.assertTrue('<ul id="file-navigation" data-path="">\n</ul>' in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_home_json(self):
        res = self.testapp.get('/home.json', status=200)
        self.assertTrue(
            'There is a problem with your configuration' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

        DBSession.remove()
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path='/path')
        res = self.testapp.get('/home.json', status=200)
        expected = (
            '{"content": '
            '"<ul id=\\"file-navigation\\" data-path=\\"\\">\\n</ul>\\n", '
            '"breadcrumb": "<li class=\\"active\\">root</li>"'
            '}'
        )
        self.assertEqual(res.body,  expected)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    def test_login_selection_forbidden(self):
        res = self.testapp.get('/login-selection', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Flogin-selection')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_login_selection(self):
        res = self.testapp.get('/login-selection', status=200)
        self.assertTrue('There is a problem with your configuration' in
                        res.body)

    def test_edit_forbidden(self):
        res = self.testapp.get('/edit.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fedit.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_edit(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/edit.json', status=200)
        expected = '{"error_msg": "A filename should be provided"}'
        self.assertEqual(res.body,  expected)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

        res = self.testapp.get('/edit.json',
                               status=200,
                               params={'filename': 'file1.xml'})
        dic = simplejson.loads(res.body)
        self.assertEqual(len(dic), 2)
        self.assertTrue('<form method="POST" id="xmltool-form">' in
                        dic['content'])
        self.assertTrue(dic['breadcrumb'])

