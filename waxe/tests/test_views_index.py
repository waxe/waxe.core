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
    bad_request,
    _get_tags
)
from urllib2 import HTTPError


class TestViews(WaxeTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config = testing.setUp(settings=self.settings)

    def tearDown(self):
        testing.tearDown()
        super(TestViews, self).tearDown()

    def test__get_tags(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        res = _get_tags(dtd_url)
        expected = ['Exercise', 'comments', 'mqm', 'qcm', 'test']
        self.assertEqual(res, expected)

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

    def test__get_navigation_data(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path)
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request)._get_navigation_data()
        expected = {
            'folders': [
                {'data_href': '/home_json/filepath',
                 'href': '/home/filepath',
                 'name': 'folder1'}],
            'path': '',
            'previous': None,
            'filenames': [
                {'data_href': '/edit_json/filepath',
                 'href': '/edit/filepath', 'name': 'file1.xml'}]
        }
        self.assertEqual(res, expected)

        request = testing.DummyRequest(
            root_path=path, params={'path': 'folder1'})
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request)._get_navigation_data()
        expected = {
            'folders': [],
            'path': 'folder1',
            'previous': None,
            'filenames': [
                {'data_href': '/edit_json/filepath',
                 'href': '/edit/filepath',
                 'name': 'file2.xml'}]
        }
        self.assertEqual(res, expected)

        res = Views(request)._get_navigation_data(add_previous=True,
                                                  folder_route='folder_route',
                                                  file_route='file_route',
                                                  only_json=True)
        expected = {
            'folders': [],
            'path': 'folder1',
            'previous': {
                'data_href': '/folder_route_json/filepath', 'name': '..'
            },
            'filenames': [{
                'data_href': '/file_route_json/filepath',
                'name': 'file2.xml'}]
        }
        self.assertTrue(res, expected)

    def test__get_navigation(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path)
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_navigation()
        expected = (
            '<ul id="file-navigation" data-path="">\n'
            '    <li>'
            '<a data-href="/filepath" href="/filepath" class="folder">'
            'folder1'
            '</a>'
            '</li>\n'
            '    <li>'
            '<a data-href="/filepath" href="/filepath" class="file">'
            'file1.xml'
            '</a>'
            '</li>\n'
            '</ul>\n')
        self.assertEqual(res, expected)

        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path,
                                       params={'path': 'folder1'})
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_navigation()
        expected = (
            '<ul id="file-navigation" data-path="folder1">\n'
            '    <li>'
            '<a data-href="/filepath" href="/filepath" class="previous">'
            '..'
            '</a>'
            '</li>\n'
            '    <li>'
            '<a data-href="/filepath" href="/filepath" class="file">'
            'file2.xml'
            '</a>'
            '</li>\n'
            '</ul>\n')
        self.assertEqual(res, expected)

    def test__get_breadcrumb_data(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path)
        res = Views(request)._get_breadcrumb_data('')
        expected = [('root', '')]
        self.assertEqual(res, expected)

        res = Views(request)._get_breadcrumb_data('folder1')
        expected = [('root', ''), ('folder1', 'folder1')]
        self.assertEqual(res, expected)

    def test__get_breadcrumb(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path)
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_breadcrumb('folder1')
        expected = (
            '<li>'
            '<a data-href="/filepath" href="/filepath">root</a> '
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
            '<a data-href="/filepath" href="/filepath">root</a> '
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
        class C(object): pass
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path, user=self.user_bob)
        expected = {
            'error_msg': 'A filename should be provided',
        }
        res = Views(request).edit()
        self.assertEqual(res, expected)

        with patch('xmltool.generate_form', return_value='My form content'):
            expected_breadcrumb = (
                '<li><a data-href="/filepath" href="/filepath">root</a> '
                '<span class="divider">/</span></li>'
                '<li class="active">file1.xml</li>')
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'filename': 'file1.xml'})
            request.route_path = lambda *args, **kw: '/filepath'
            request.matched_route = C()
            request.matched_route.name = 'route_json'
            res = Views(request).edit()
            keys = res.keys()
            keys.sort()
            self.assertEqual(keys, ['breadcrumb', 'content', 'jstree_data'])
            self.assertEqual(res['breadcrumb'],  expected_breadcrumb)
            self.assertTrue('<form method="POST" id="xmltool-form">' in
                            res['content'])
            self.assertTrue(isinstance(res['jstree_data'], dict))

            request.matched_route.name = 'route'
            res = Views(request).edit()
            keys = res.keys()
            keys.sort()
            self.assertEqual(keys, ['breadcrumb', 'content', 'jstree_data'])
            self.assertEqual(res['breadcrumb'],  expected_breadcrumb)
            self.assertTrue('<form method="POST" id="xmltool-form">' in
                            res['content'])
            self.assertTrue(isinstance(res['jstree_data'], str))

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.load') as m:
            m.side_effect = raise_func
            expected = {
                'error_msg': 'My error',
            }
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'filename': 'file1.xml'})
            request.matched_route = C()
            request.matched_route.name = 'route_json'
            res = Views(request).edit()
            self.assertEqual(res, expected)

        def raise_http_func(*args, **kw):
            raise HTTPError('http://url', 404, 'Not found', [], None)

        with patch('xmltool.load') as m:
            m.side_effect = raise_http_func
            expected = {
                'error_msg': 'The dtd of file1.xml can\'t be loaded.',
            }
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'filename': 'file1.xml'})
            request.matched_route = C()
            request.matched_route.name = 'route_json'
            res = Views(request).edit()
            self.assertEqual(res, expected)

    def test_get_tags(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest(root_path='/path',
                                       user=self.user_bob)
        res = Views(request).get_tags()
        self.assertEqual(res, {})

        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        request = testing.DummyRequest(root_path='/path',
                                       user=self.user_bob,
                                       params={'dtd_url': dtd_url})
        res = Views(request).get_tags()
        expected = {'tags': ['Exercise', 'comments', 'mqm', 'qcm', 'test']}
        self.assertEqual(res, expected)

    def test_new(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        DBSession.add(self.user_bob)
        request = testing.DummyRequest(root_path='/path',
                                       user=self.user_bob)
        request.dtd_urls = [dtd_url]
        res = Views(request).new()
        self.assertEqual(len(res), 1)
        self.assertTrue('<h3>New file</h3>' in res['content'])

        request = testing.DummyRequest(root_path='/path',
                                       user=self.user_bob,
                                       params={
                                           'dtd_url': dtd_url,
                                           'dtd_tag': 'Exercise'
                                       })
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request).new()
        self.assertEqual(len(res), 2)
        self.assertTrue('<form method="POST" id="xmltool-form">'
                        in res['content'])
        self.assertTrue('<a data-href="/filepath" href="/filepath">root</a>'
                        in res['breadcrumb'])

    def test_open(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path,
                                       user=self.user_bob)
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request).open()
        expected = {
            'folders': [
                {'data_href': '/filepath',
                 'name': 'folder1'}
            ],
            'path': '',
            'previous': None,
            'nav_btns': [{'data_href': '/filepath', 'name': 'root'}],
            'filenames': [{'data_href': '/filepath', 'name': 'file1.xml'}]
        }
        self.assertEqual(res, expected)

    def test_create_folder(self):
        try:
            DBSession.add(self.user_bob)
            path = os.path.join(os.getcwd(), 'waxe/tests/files')
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob)
            res = Views(request).create_folder()
            expected = {'status': False, 'error_msg': 'No path given'}
            self.assertEqual(res, expected)
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'path': 'new_folder'})
            res = Views(request).create_folder()
            expected = {'status': True}
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))
            self.assertEqual(res, expected)

            res = Views(request).create_folder()
            expected = {
                'status': False,
                'error_msg': ("mkdir: cannot create directory `%s'"
                              ": File exists\n") % (
                                  os.path.join(path, 'new_folder'))
            }
            self.assertEqual(res, expected)
        finally:
            os.rmdir(os.path.join(path, 'new_folder'))

    def test_update(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path,
                                       user=self.user_bob,
                                       params={},
                                      )
        res = Views(request).update()
        expected = {'status': False, 'error_msg': 'No filename given'}
        self.assertEqual(res, expected)

        with patch('xmltool.update', return_value=False):
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'_xml_filename': 'test.xml'},
                                          )
            request.route_path = lambda *args, **kw: '/filepath'
            res = Views(request).update()
            expected = {
                'status': True,
                'breadcrumb': (
                    '<li><a data-href="/filepath" href="/filepath">root</a> '
                    '<span class="divider">/</span></li>'
                    '<li class="active">test.xml</li>')
            }
            self.assertEqual(res, expected)

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.update') as m:
            m.side_effect = raise_func
            request = testing.DummyRequest(root_path=path,
                                           user=self.user_bob,
                                           params={'_xml_filename': 'test.xml'},
                                          )
            request.route_path = lambda *args, **kw: '/filepath'
            expected = {
                'status': False,
                'error_msg': 'My error',
            }
            res = Views(request).update()
            self.assertEqual(res, expected)

    def test_add_element_json(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(root_path=path,
                                       user=self.user_bob,
                                       params={})
        expected = {'status': False, 'error_msg': 'Bad parameter'}
        res = Views(request).add_element_json()
        self.assertEqual(res, expected)

        dtd_url = os.path.join(path, 'exercise.dtd')
        request = testing.DummyRequest(root_path=path,
                                       user=self.user_bob,
                                       params={'dtd_url': dtd_url,
                                               'elt_id': 'Exercise'})
        res = Views(request).add_element_json()
        self.assertTrue(res)
        self.assertTrue(isinstance(res, dict))


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
        self.assertEqual(len(dic), 3)
        self.assertTrue('<form method="POST" id="xmltool-form">' in
                        dic['content'])
        self.assertTrue(isinstance(dic['jstree_data'], dict))

    def test_get_tags_forbidden(self):
        res = self.testapp.get('/get-tags.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fget-tags.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_get_tags(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/get-tags.json', status=200)
        self.assertEqual(simplejson.loads(res.body), {})

        res = self.testapp.get('/get-tags.json',
                               status=200,
                               params={'dtd_url': dtd_url})
        expected = {'tags': ['Exercise', 'comments', 'mqm', 'qcm', 'test']}
        self.assertEqual(simplejson.loads(res.body), expected)

    def test_new_forbidden(self):
        res = self.testapp.get('/new.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fnew.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_new(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/new.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        dic = simplejson.loads(res.body)
        self.assertEqual(len(dic), 1)
        self.assertTrue('<h3>New file</h3>' in dic['content'])

        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        dtd_tag = 'Exercise'
        res = self.testapp.get('/new.json',
                               status=200,
                               params={'dtd_url': dtd_url,
                                       'dtd_tag': dtd_tag})
        dic = simplejson.loads(res.body)
        self.assertEqual(len(dic), 2)
        self.assertTrue('<form method="POST" id="xmltool-form">' in
                        dic['content'])
        self.assertTrue(dic['breadcrumb'])
        self.assertTrue('data-href="/home.json?="' in dic['breadcrumb'])

    def test_open_forbidden(self):
        res = self.testapp.get('/open.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fopen.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_open(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/open.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"folders": [{"data_href": "/open.json?path=folder1", "name": "folder1"}], "path": "", "previous": None, "nav_btns": [{"data_href": "/open.json?path=", "name": "root"}], "filenames": [{"data_href": "/edit.json?filename=file1.xml", "name": "file1.xml"}]}
        self.assertEqual(simplejson.loads(res.body), expected)

    def test_create_folder_forbidden(self):
        res = self.testapp.get('/create-folder.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fcreate-folder.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_create_folder(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/create-folder.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "No path given"}
        self.assertEqual(simplejson.loads(res.body), expected)

        try:
            res = self.testapp.get('/create-folder.json',
                                   status=200,
                                   params={'path': 'new_folder'})
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))
            expected = {'status': True}
            self.assertEqual(simplejson.loads(res.body), expected)

            res = self.testapp.get('/create-folder.json',
                                   status=200,
                                   params={'path': 'new_folder'})
            expected = {
                'status': False,
                'error_msg': ("mkdir: cannot create directory `%s'"
                              ": File exists\n") % (
                                  os.path.join(path, 'new_folder'))
            }
            self.assertEqual(simplejson.loads(res.body), expected)
        finally:
            os.rmdir(os.path.join(path, 'new_folder'))

    def test_update_forbidden(self):
        res = self.testapp.get('/update.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fupdate.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_update(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.post('/update.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "No filename given"}
        self.assertEqual(simplejson.loads(res.body), expected)

        with patch('xmltool.update', return_value=False):
            res = self.testapp.post('/update.json',
                                    status=200,
                                    params={'_xml_filename': 'test.xml'})
            expected = {
                "status": True,
                "breadcrumb": (
                    "<li><a data-href=\"/home.json?=\" href=\"/?=\">root</a> "
                    "<span class=\"divider\">/</span></li>"
                    "<li class=\"active\">test.xml</li>")}
        self.assertEqual(simplejson.loads(res.body), expected)

    def test_add_element_json_forbidden(self):
        res = self.testapp.get('/add-element.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fadd-element.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_add_element_json(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/add-element.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Bad parameter"}
        self.assertEqual(simplejson.loads(res.body), expected)

        dtd_url = os.path.join(path, 'exercise.dtd')
        res = self.testapp.get('/add-element.json', status=200,
                               params={'dtd_url': dtd_url,
                                       'elt_id': 'Exercise'})

        dic = simplejson.loads(res.body)
        self.assertTrue(dic['status'])

    def test_get_comment_modal_json_forbidden(self):
        res = self.testapp.get('/get-comment-modal.json', status=302)
        self.assertEqual(
            res.location,
            ('http://localhost/login?next=http%3A%2F%2Flocalhost%2F'
             'get-comment-modal.json'))
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_get_comment_modal_json(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config = UserConfig(root_path=path)
        res = self.testapp.get('/get-comment-modal.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        body = simplejson.loads(res.body)
        self.assertEqual(len(body), 1)
        self.assertTrue('<div class="modal ' in body['content'])
