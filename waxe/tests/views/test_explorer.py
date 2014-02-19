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
                {'data_href': '/explore_json/filepath',
                 'data_relpath': 'folder1',
                 'href': '/explore/filepath',
                 'name': 'folder1'}],
            'path': '',
            'previous': None,
            'filenames': [
                {'data_href': '/edit_json/filepath',
                 'data_relpath': 'file1.xml',
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
                 'data_relpath': 'folder1/file2.xml',
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
                'data_relpath': 'folder1/file2.xml',
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
            '<a data-href="/filepath" href="/filepath" class="folder" '
            'data-relpath="folder1">'
            'folder1'
            '</a>'
            '</li>\n'
            '    <li><i class="glyphicon glyphicon-file"></i>'
            '<a data-href="/filepath" href="/filepath" class="file" '
            'data-relpath="file1.xml">'
            'file1.xml'
            '</a>'
            '</li>\n'
            '</ul>\n\n\n')
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
            '<a data-href="/filepath" href="/filepath" class="file" '
            'data-relpath="folder1/file2.xml">'
            'file2.xml'
            '</a>'
            '</li>\n'
            '</ul>\n\n\n')
        self.assertEqual(res, expected)

        request.custom_route_path = lambda *args, **kw: '/%s' % args[0]
        o = ExplorerView(request)
        res = o._get_navigation()
        expected = 'data-versioning-path="/versioning_dispatcher_json"'
        self.assertFalse(expected in res)

        o.has_versioning = lambda *args: True
        res = o._get_navigation()
        self.assertTrue(expected in res)

    def test_home(self):
        class C(object): pass
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).home()
        expected = ExplorerView(request).explore()
        self.assertEqual(res, expected)

        request.params['path'] = 'file1.xml'
        res = ExplorerView(request).home()
        self.assertEqual(res.status, "302 Found")
        self.assertEqual(res.location,
                         '/edit/filepath?path=file1.xml')

    def test_explore(self):
        class C(object): pass
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).explore()
        expected = {
            'content': (
                u'<ul id="file-navigation" class="list-unstyled" '
                u'data-path="">\n    '
                u'<li><i class="glyphicon glyphicon-folder-close"></i>'
                u'<a data-href="/explore_json/filepath" '
                u'href="/explore/filepath" class="folder" '
                u'data-relpath="folder1">folder1</a>'
                u'</li>\n    '
                u'<li><i class="glyphicon glyphicon-file"></i>'
                u'<a data-href="/edit_json/filepath" href="/edit/filepath" '
                u'class="file" '
                u'data-relpath="file1.xml">file1.xml</a></li>\n</ul>\n\n\n'),
            'breadcrumb': '<li class="active">root</li>',
            'editor_login': 'Bob',
            'versioning': False,
        }
        self.assertEqual(res, expected)

        self.user_bob.config.root_path = '/unexisting'
        res = ExplorerView(request).explore()
        expected = {
            'error_msg': "Directory . doesn't exist",
            'editor_login': u'Bob',
            'versioning': False,
        }
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
                 'data_relpath': 'folder1',
                 'name': 'folder1'}
            ],
            'path': '',
            'previous': None,
            'nav_btns': [{'data_href': '/filepath', 'name': 'root'}],
            'filenames': [{'data_href': '/filepath',
                           'data_relpath': 'file1.xml',
                           'name': 'file1.xml'}]
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
            self.assertEqual(len(res), 2)
            self.assertEqual(res['status'], False)
            self.assertTrue('mkdir: cannot create directory' in
                            res['error_msg'])
            self.assertTrue('File exists' in res['error_msg'])
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
        self.assertTrue('Directory . doesn\'t exist' in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_explore(self):
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/account/Bob/explore', status=200)
        self.assertTrue('Directory . doesn\'t exist' in res.body)
        self.assertTrue(('Content-Type', 'text/html; charset=UTF-8') in
                        res._headerlist)

    @login_user('Admin')
    def test_explore_json_admin(self):
        res = self.testapp.get('/account/Admin/explore.json', status=200)
        expected = ('Go to your <a href=\\"/admin\\">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_explore_json(self):
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/account/Bob/explore.json', status=200)
        expected = '{"error_msg": "Directory . doesn\'t exist"}'
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
                 "data_relpath": "folder1",
                 "name": "folder1"}],
            "path": "",
            "previous": None,
            "nav_btns": [
                {"data_href": "/account/Bob/open.json?path=",
                 "name": "root"}],
            "filenames": [
                {"data_href": "/account/Bob/edit.json?path=file1.xml",
                 "data_relpath": "file1.xml",
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
                u'status': False,
                u'error_msg': (
                    u"mkdir: cannot create directory \u2018%s\u2019"
                    u": File exists\n") % (os.path.join(path, 'new_folder'))
            }
            dic = json.loads(res.body)
            self.assertEqual(len(dic), 2)
            self.assertEqual(dic['status'], False)
            self.assertTrue('mkdir: cannot create directory' in
                            dic['error_msg'])
            self.assertTrue('File exists' in dic['error_msg'])
        finally:
            os.rmdir(os.path.join(path, 'new_folder'))
