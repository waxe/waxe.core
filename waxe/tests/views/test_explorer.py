import os
import json
from pyramid import testing
from mock import patch
from waxe.tests.testing import LoggedBobTestCase, WaxeTestCase, login_user
from waxe.views.explorer import ExplorerView


class TestExplorerView(LoggedBobTestCase):

    def test__get_navigation_data(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = ExplorerView(request)._get_navigation_data()
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
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = ExplorerView(request)._get_navigation_data()
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

        res = ExplorerView(request)._get_navigation_data(
            add_previous=True,
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
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = ExplorerView(request)._get_navigation()
        expected = (
            '<ul id="file-navigation" class="list-unstyled" data-path="">\n'
            '    <li><i class="glyphicon glyphicon-folder-close"></i>'
            '<a data-href="/filepath" href="/filepath" class="folder">'
            'folder1'
            '</a>'
            '</li>\n'
            '    <li><i class="glyphicon glyphicon-file"></i>'
            '<a data-href="/filepath" href="/filepath" class="file">'
            'file1.xml'
            '</a>'
            '</li>\n'
            '</ul>\n')
        self.assertEqual(res, expected)

        request = testing.DummyRequest(params={'path': 'folder1'})
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = ExplorerView(request)._get_navigation()
        expected = (
            '<ul id="file-navigation" class="list-unstyled" data-path="folder1">\n'
            '    <li><i class="glyphicon glyphicon-arrow-left"></i>'
            '<a data-href="/filepath" href="/filepath" class="previous">'
            '..'
            '</a>'
            '</li>\n'
            '    <li><i class="glyphicon glyphicon-file"></i>'
            '<a data-href="/filepath" href="/filepath" class="file">'
            'file2.xml'
            '</a>'
            '</li>\n'
            '</ul>\n')
        self.assertEqual(res, expected)

    def test_home(self):
        self.user_bob.config.root_path = '/unexisting'
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s' % args[0]
        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" class="list-unstyled" data-path="">\n</ul>\n',
            'editor_login': u'Bob',
        }
        with patch('waxe.views.base.BaseView._is_json', return_value=False):
            res = ExplorerView(request).home()
            self.assertEqual(res, expected)

        expected = {
            'breadcrumb': '<li class="active">root</li>',
            'content': u'<ul id="file-navigation" class="list-unstyled" data-path="">\n</ul>\n',
        }
        with patch('waxe.views.base.BaseView._is_json', return_value=True):
            res = ExplorerView(request).home()
            self.assertEqual(res, expected)

    def test_open(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = ExplorerView(request).open()
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
            path = os.path.join(os.getcwd(), 'waxe/tests/files')
            request = testing.DummyRequest()
            res = ExplorerView(request).create_folder()
            expected = {'status': False, 'error_msg': 'No path given'}
            self.assertEqual(res, expected)
            request = testing.DummyRequest(params={'path': 'new_folder'})
            res = ExplorerView(request).create_folder()
            expected = {'status': True}
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))
            self.assertEqual(res, expected)

            res = ExplorerView(request).create_folder()
            expected = {
                'status': False,
                'error_msg': ("mkdir: cannot create directory `%s'"
                              ": File exists\n") % (
                                  os.path.join(path, 'new_folder'))
            }
            self.assertEqual(res, expected)
        finally:
            os.rmdir(os.path.join(path, 'new_folder'))


class TestFunctionalTestExplorerView(WaxeTestCase):

    def test_home_forbidden(self):
        res = self.testapp.get('/account/Bob/', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Faccount%2FBob%2F')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Fred')
    def test_home_bad_login(self):
        res = self.testapp.get('/account/Fred/', status=302)
        self.assertEqual(res.location,
                         'http://localhost/forbidden')

    @login_user('Admin')
    def test_home_admin(self):
        res = self.testapp.get('/account/Admin/', status=200)
        expected = ('Go to your <a href="/admin">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_home(self):
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/account/Bob/', status=200)
        self.assertTrue('<ul id="file-navigation" class="list-unstyled" data-path="">\n</ul>' in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Admin')
    def test_home_json_admin(self):
        res = self.testapp.get('/account/Admin/home.json', status=200)
        expected = ('Go to your <a href=\\"/admin\\">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_home_json(self):
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/account/Bob/home.json', status=200)
        expected = (
            '{"content": '
            '"<ul id=\\"file-navigation\\" class=\\"list-unstyled\\" data-path=\\"\\">\\n</ul>\\n", '
            '"breadcrumb": "<li class=\\"active\\">root</li>"'
            '}'
        )
        self.assertEqual(res.body,  expected)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    def test_open_forbidden(self):
        res = self.testapp.get('/account/Bob/open.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Faccount%2FBob%2Fopen.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_open(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/open.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {
            "folders": [
                {"data_href": "/account/Bob/open.json?path=folder1",
                 "name": "folder1"}],
            "path": "",
            "previous": None,
            "nav_btns": [
                {"data_href": "/account/Bob/open.json?path=",
                 "name": "root"}],
            "filenames": [
                {"data_href": "/account/Bob/edit.json?filename=file1.xml",
                 "name": "file1.xml"}]
        }
        self.assertEqual(json.loads(res.body), expected)

    def test_create_folder_forbidden(self):
        res = self.testapp.get('/account/Bob/create-folder.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Faccount%2FBob%2Fcreate-folder.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_create_folder(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/create-folder.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "No path given"}
        self.assertEqual(json.loads(res.body), expected)

        try:
            res = self.testapp.get('/account/Bob/create-folder.json',
                                   status=200,
                                   params={'path': 'new_folder'})
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))
            expected = {'status': True}
            self.assertEqual(json.loads(res.body), expected)

            res = self.testapp.get('/account/Bob/create-folder.json',
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

