import os
import json
from pyramid import testing
from ..testing import WaxeTestCase, WaxeTestCaseVersioning, login_user, local_login_user
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
    BadRequestView,
    HTTPBadRequest,
    JSONHTTPBadRequest,
    _get_tags
)
from urllib2 import HTTPError


class TestViewsNoVersioning(WaxeTestCase):

    def setUp(self):
        super(TestViewsNoVersioning, self).setUp()
        self.config = testing.setUp(settings=self.settings)
        self.config.include('pyramid_mako')

    def tearDown(self):
        testing.tearDown()
        super(TestViewsNoVersioning, self).tearDown()

    @local_login_user('Bob')
    def test__response(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
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
                                   'logins': ['Bob', 'contributor']})

            request.session = {}
            self.user_bob.config.root_path = ''
            class C(object): pass
            request.matched_route = C()
            request.matched_route.name = 'login_selection'
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': 'Account',
                                   'logins': ['contributor']})

    @local_login_user('Bob')
    def test_home(self):
        DBSession.add(self.user_bob)
        self.user_bob.config.root_path = '/unexisting'
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" class="unstyled" data-path="">\n</ul>\n',
            'editor_login': u'Bob',
        }
        with patch('waxe.views.index.Views._is_json', return_value=False):
            res = Views(request).home()
            self.assertEqual(res, expected)

        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" class="unstyled" data-path="">\n</ul>\n',
        }
        with patch('waxe.views.index.Views._is_json', return_value=True):
            res = Views(request).home()
            self.assertEqual(res, expected)


class TestViews(WaxeTestCaseVersioning):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config = testing.setUp(settings=self.settings)
        self.config.include('pyramid_mako')

    def tearDown(self):
        testing.tearDown()
        super(TestViews, self).tearDown()

    def test__get_tags(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        res = _get_tags(dtd_url)
        expected = ['Exercise', 'comments', 'mqm', 'qcm', 'test']
        self.assertEqual(res, expected)

    def test_class_init(self):
        request = testing.DummyRequest()
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

    @local_login_user('Bob')
    def test__is_json(self):
        request = testing.DummyRequest()

        class C(object):
            pass
        request.matched_route = C()
        request.matched_route.name = 'route'
        self.assertFalse(Views(request)._is_json())

        request.matched_route.name = 'route_json'
        self.assertTrue(Views(request)._is_json())

    @local_login_user('Bob')
    def test__response(self):
        DBSession.add(self.user_bob)
        DBSession.add(self.user_fred)
        request = testing.DummyRequest()
        with patch('waxe.views.index.Views._is_json', return_value=True):
            res = Views(request)._response({})
            self.assertEqual(res, {})

        with patch('waxe.views.index.Views._is_json', return_value=False):
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': self.user_bob.login,
                                   'versioning': True})
            request.session = {'editor_login': self.user_fred.login}

            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': self.user_fred.login,
                                   'versioning': True})

            contributor = User(login='contributor', password='pass1')
            contributor.roles = [Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()]
            contributor.config = UserConfig(root_path='/path')
            DBSession.add(contributor)
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': self.user_fred.login,
                                   'versioning': True,
                                   'logins': ['Bob', 'contributor']})

            self.user_fred.config.use_versioning = False
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': self.user_fred.login,
                                   'logins': ['Bob', 'contributor']})

            request.session = {}
            request.root_path = None

            class C(object):
                pass
            request.matched_route = C()
            request.matched_route.name = 'login_selection'
            res = Views(request)._response({})
            self.assertEqual(res, {'editor_login': 'Bob',
                                   'logins': ['contributor'],
                                   'versioning': True})

    @local_login_user('Bob')
    def test__get_navigation_data(self):
        request = testing.DummyRequest()
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

        request = testing.DummyRequest(params={'path': 'folder1'})
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

    @local_login_user('Bob')
    def test__get_navigation(self):
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_navigation()
        expected = (
            '<ul id="file-navigation" class="unstyled" data-path="">\n'
            '    <li><i class="icon-folder-close"></i>'
            '<a data-href="/filepath" href="/filepath" class="folder">'
            'folder1'
            '</a>'
            '</li>\n'
            '    <li><i class="icon-file"></i>'
            '<a data-href="/filepath" href="/filepath" class="file">'
            'file1.xml'
            '</a>'
            '</li>\n'
            '</ul>\n')
        self.assertEqual(res, expected)

        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(params={'path': 'folder1'})
        request.route_path = lambda *args, **kw: '/filepath'
        res = Views(request)._get_navigation()
        expected = (
            '<ul id="file-navigation" class="unstyled" data-path="folder1">\n'
            '    <li>'
            '<a data-href="/filepath" href="/filepath" class="previous">'
            '..'
            '</a>'
            '</li>\n'
            '    <li><i class="icon-file"></i>'
            '<a data-href="/filepath" href="/filepath" class="file">'
            'file2.xml'
            '</a>'
            '</li>\n'
            '</ul>\n')
        self.assertEqual(res, expected)

    @local_login_user('Bob')
    def test__get_breadcrumb_data(self):
        request = testing.DummyRequest()
        res = Views(request)._get_breadcrumb_data('')
        expected = [('root', '')]
        self.assertEqual(res, expected)

        res = Views(request)._get_breadcrumb_data('folder1')
        expected = [('root', ''), ('folder1', 'folder1')]
        self.assertEqual(res, expected)

    @local_login_user('Bob')
    def test__get_breadcrumb(self):
        request = testing.DummyRequest()
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

    @local_login_user('Bob')
    def test_home(self):
        DBSession.add(self.user_bob)
        self.user_bob.config.root_path = '/unexisting'
        request = testing.DummyRequest()
        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" class="unstyled" data-path="">\n</ul>\n',
            'editor_login': u'Bob',
            'versioning': True
        }
        with patch('waxe.views.index.Views._is_json', return_value=False):
            res = Views(request).home()
            self.assertEqual(res, expected)

        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" class="unstyled" data-path="">\n</ul>\n',
        }
        with patch('waxe.views.index.Views._is_json', return_value=True):
            res = Views(request).home()
            self.assertEqual(res, expected)

    @local_login_user('Bob')
    def test_login_selection(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        try:
            res = Views(request).login_selection()
            assert 0
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'Invalid login')

        request = testing.DummyRequest(params={'login': 'editor'})
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

    @local_login_user('Bob')
    def test_bad_request(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        dic = BadRequestView(request).bad_request()
        self.assertEqual(len(dic), 1)
        expected = ('Go to your <a href="/admin_home">'
                    'admin interface</a> to insert a new user')
        self.assertEqual(dic['content'], expected)

        editor = User(login='editor', password='pass1')
        editor.roles = [Role.query.filter_by(name=ROLE_EDITOR).one()]
        editor.config = UserConfig(root_path='/path')
        DBSession.add(editor)

        request.route_path = lambda *args, **kw: '/editorpath'
        dic = BadRequestView(request).bad_request()
        expected = {'content': (u'  <a href="/editorpath">Bob</a>\n'
                                u'  <a href="/editorpath">editor</a>\n')}
        self.assertEqual(dic, expected)

    @local_login_user('Fred')
    def test_bad_request_not_admin(self):
        DBSession.add(self.user_fred)
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        dic = BadRequestView(request).bad_request()
        self.assertEqual(len(dic), 1)
        expected = 'There is a problem with your configuration'
        self.assertTrue(expected in dic['content'])

    @local_login_user('Bob')
    def test_edit(self):
        class C(object): pass
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
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
            request = testing.DummyRequest(
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
            request = testing.DummyRequest(
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
            request = testing.DummyRequest(
                params={'filename': 'file1.xml'})
            request.matched_route = C()
            request.matched_route.name = 'route_json'
            res = Views(request).edit()
            self.assertEqual(res, expected)

    @local_login_user('Bob')
    def test_get_tags(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        res = Views(request).get_tags()
        self.assertEqual(res, {})

        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        request = testing.DummyRequest(params={'dtd_url': dtd_url})
        res = Views(request).get_tags()
        expected = {'tags': ['Exercise', 'comments', 'mqm', 'qcm', 'test']}
        self.assertEqual(res, expected)

    @local_login_user('Bob')
    def test_new(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        request.dtd_urls = [dtd_url]
        res = Views(request).new()
        self.assertEqual(len(res), 1)
        self.assertTrue('<h3>New file</h3>' in res['content'])

        request = testing.DummyRequest(
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

    @local_login_user('Bob')
    def test_open(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
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

    @local_login_user('Bob')
    def test_create_folder(self):
        try:
            DBSession.add(self.user_bob)
            path = os.path.join(os.getcwd(), 'waxe/tests/files')
            request = testing.DummyRequest()
            res = Views(request).create_folder()
            expected = {'status': False, 'error_msg': 'No path given'}
            self.assertEqual(res, expected)
            request = testing.DummyRequest(params={'path': 'new_folder'})
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

    @local_login_user('Bob')
    def test_update(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={})
        res = Views(request).update()
        expected = {'status': False, 'error_msg': 'No filename given'}
        self.assertEqual(res, expected)

        with patch('xmltool.update', return_value=False):
            request = testing.DummyRequest(
                params={'_xml_filename': 'test.xml'})
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
            request = testing.DummyRequest(
                params={'_xml_filename': 'test.xml'})
            request.route_path = lambda *args, **kw: '/filepath'
            expected = {
                'status': False,
                'error_msg': 'My error',
            }
            res = Views(request).update()
            self.assertEqual(res, expected)

    @local_login_user('Bob')
    def test_update_text(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={})
        res = Views(request).update_text()
        expected = {'status': False, 'error_msg': 'Missing parameters!'}
        self.assertEqual(res, expected)

        request = testing.DummyRequest(
            params={'filecontent': 'content of the file',
                    'filename': 'thefilename.xml'})

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.load_string') as m:
            m.side_effect = raise_func
            res = Views(request).update_text()
            expected = {'status': False, 'error_msg': 'My error'}
            self.assertEqual(res,  expected)

        filecontent = open(os.path.join(path, 'file1.xml'), 'r').read()
        # The dtd should be an absolute url!
        filecontent = filecontent.replace('exercise.dtd',
                                          os.path.join(path, 'exercise.dtd'))
        request = testing.DummyRequest(
            params={'filecontent': filecontent,
                    'filename': 'thefilename.xml'})

        with patch('xmltool.elements.Element.write', return_value=None):
            res = Views(request).update_text()
            expected = {'status': True, 'content': 'File updated'}
            self.assertEqual(res,  expected)

            request.params['commit'] = True
            res = Views(request).update_text()
            self.assertEqual(len(res), 2)
            self.assertEqual(res['status'], True)
            self.assertTrue('class="modal' in res['content'])
            self.assertTrue('Commit message' in res['content'])

    @local_login_user('Bob')
    def test_update_texts(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={})
        res = Views(request).update_texts()
        expected = {'status': False, 'error_msg': 'Missing parameters!'}
        self.assertEqual(res, expected)

        request = testing.DummyRequest(
            params={
                'data:0:filecontent': 'content of the file 1',
                'data:0:filename': 'thefilename1.xml',
                'data:1:filecontent': 'content of the file 2',
                'data:1:filename': 'thefilename2.xml',
            })

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.load_string') as m:
            m.side_effect = raise_func
            res = Views(request).update_texts()
            expected = {'status': False, 'error_msg': 'thefilename1.xml: My error<br />thefilename2.xml: My error'}
            self.assertEqual(res,  expected)

        filecontent = open(os.path.join(path, 'file1.xml'), 'r').read()
        filecontent = filecontent.replace('exercise.dtd',
                                          os.path.join(path, 'exercise.dtd'))
        request = testing.DummyRequest(
            params={'data:0:filecontent': filecontent,
                    'data:0:filename': 'thefilename.xml'})

        with patch('xmltool.elements.Element.write', return_value=None):
            res = Views(request).update_texts()
            expected = {'status': True, 'content': 'Files updated'}
            self.assertEqual(res,  expected)

            request.params['commit'] = True
            res = Views(request).update_texts()
            self.assertEqual(len(res), 2)
            self.assertEqual(res['status'], True)
            self.assertTrue('class="modal' in res['content'])
            self.assertTrue('Commit message' in res['content'])

    @local_login_user('Bob')
    def test_add_element_json(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(params={})
        expected = {'status': False, 'error_msg': 'Bad parameter'}
        res = Views(request).add_element_json()
        self.assertEqual(res, expected)

        dtd_url = os.path.join(path, 'exercise.dtd')
        request = testing.DummyRequest(params={'dtd_url': dtd_url,
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

    @login_user('Admin')
    def test_home_admin(self):
        res = self.testapp.get('/', status=200)
        expected = ('Go to your <a href="/admin">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_home(self):
        DBSession.add(self.user_bob)
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/', status=200)
        self.assertTrue('<ul id="file-navigation" class="unstyled" data-path="">\n</ul>' in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Admin')
    def test_home_json_admin(self):
        res = self.testapp.get('/home.json', status=200)
        expected = ('Go to your <a href=\\"/admin\\">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_home_json(self):
        DBSession.add(self.user_bob)
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/home.json', status=200)
        expected = (
            '{"content": '
            '"<ul id=\\"file-navigation\\" class=\\"unstyled\\" data-path=\\"\\">\\n</ul>\\n", '
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
        expected = ('Go to your <a href="/admin">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)

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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/edit.json', status=200)
        expected = '{"error_msg": "A filename should be provided"}'
        self.assertEqual(res.body,  expected)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

        res = self.testapp.get('/edit.json',
                               status=200,
                               params={'filename': 'file1.xml'})
        dic = json.loads(res.body)
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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/get-tags.json', status=200)
        self.assertEqual(json.loads(res.body), {})

        res = self.testapp.get('/get-tags.json',
                               status=200,
                               params={'dtd_url': dtd_url})
        expected = {'tags': ['Exercise', 'comments', 'mqm', 'qcm', 'test']}
        self.assertEqual(json.loads(res.body), expected)

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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/new.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 1)
        self.assertTrue('<h3>New file</h3>' in dic['content'])

        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        dtd_tag = 'Exercise'
        res = self.testapp.get('/new.json',
                               status=200,
                               params={'dtd_url': dtd_url,
                                       'dtd_tag': dtd_tag})
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 2)
        self.assertTrue('<form method="POST" id="xmltool-form">' in
                        dic['content'])
        self.assertTrue(dic['breadcrumb'])
        self.assertTrue('data-href="/home.json?path="' in dic['breadcrumb'])

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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/open.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"folders": [{"data_href": "/open.json?path=folder1", "name": "folder1"}], "path": "", "previous": None, "nav_btns": [{"data_href": "/open.json?path=", "name": "root"}], "filenames": [{"data_href": "/edit.json?filename=file1.xml", "name": "file1.xml"}]}
        self.assertEqual(json.loads(res.body), expected)

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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/create-folder.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "No path given"}
        self.assertEqual(json.loads(res.body), expected)

        try:
            res = self.testapp.get('/create-folder.json',
                                   status=200,
                                   params={'path': 'new_folder'})
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))
            expected = {'status': True}
            self.assertEqual(json.loads(res.body), expected)

            res = self.testapp.get('/create-folder.json',
                                   status=200,
                                   params={'path': 'new_folder'})
            expected = {
                'status': False,
                'error_msg': ("mkdir: cannot create directory `%s'"
                              ": File exists\n") % (
                                  os.path.join(path, 'new_folder'))
            }
            self.assertEqual(json.loads(res.body), expected)
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
        self.user_bob.config.root_path = path
        res = self.testapp.post('/update.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "No filename given"}
        self.assertEqual(json.loads(res.body), expected)

        with patch('xmltool.update', return_value=False):
            res = self.testapp.post('/update.json',
                                    status=200,
                                    params={'_xml_filename': 'test.xml'})
            expected = {
                "status": True,
                "breadcrumb": (
                    "<li><a data-href=\"/home.json?path=\" href=\"/?path=\">root</a> "
                    "<span class=\"divider\">/</span></li>"
                    "<li class=\"active\">test.xml</li>")}
        self.assertEqual(json.loads(res.body), expected)

    def test_update_text_forbidden(self):
        res = self.testapp.get('/update-text.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fupdate-text.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_update_text(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/update-text.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Missing parameters!"}
        self.assertEqual(json.loads(res.body), expected)

    def test_update_texts_forbidden(self):
        res = self.testapp.get('/update-texts.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fupdate-texts.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_update_texts(self):
        DBSession.add(self.user_bob)
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/update-texts.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Missing parameters!"}
        self.assertEqual(json.loads(res.body), expected)

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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/add-element.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Bad parameter"}
        self.assertEqual(json.loads(res.body), expected)

        dtd_url = os.path.join(path, 'exercise.dtd')
        res = self.testapp.get('/add-element.json', status=200,
                               params={'dtd_url': dtd_url,
                                       'elt_id': 'Exercise'})

        dic = json.loads(res.body)
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
        self.user_bob.config.root_path = path
        res = self.testapp.get('/get-comment-modal.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        body = json.loads(res.body)
        self.assertEqual(len(body), 1)
        self.assertTrue('<div class="modal ' in body['content'])
