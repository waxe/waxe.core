import os
import json
from pyramid import testing
from mock import patch
from waxe.tests.testing import LoggedBobTestCase, WaxeTestCase, login_user
from waxe.views.explorer import ExplorerView
import waxe.models as models


class TestExplorerView(LoggedBobTestCase):

    def test__get_navigation_data(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = ExplorerView(request)._get_navigation_data()
        expected = {
            'folders': [
                {
                    'data_href': '/explore_json/filepath',
                    'data_relpath': 'folder1',
                    'href': '/explore/filepath',
                    'name': 'folder1',
                    'link_tag': (
                        '<a data-href="/explore_json/filepath" '
                        'href="/explore/filepath" '
                        'data-relpath="folder1" class="folder">folder1</a>')
                }],
            'path': '',
            'previous': None,
            'filenames': [
                {
                    'data_href': '/edit_json/filepath',
                    'data_relpath': 'file1.xml',
                    'href': '/edit/filepath',
                    'name': 'file1.xml',
                    'link_tag': (
                        '<a data-href="/edit_json/filepath" '
                        'href="/edit/filepath" data-relpath="file1.xml" '
                        'class="file">file1.xml</a>')
                }]
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
                {
                    'data_href': '/edit_json/filepath',
                    'data_relpath': 'folder1/file2.xml',
                    'href': '/edit/filepath',
                    'name': 'file2.xml',
                    'link_tag': (
                        '<a data-href="/edit_json/filepath" '
                        'href="/edit/filepath" '
                        'data-relpath="folder1/file2.xml" class="file">'
                        'file2.xml</a>'
                    )
                }]
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
                'data_href': '/folder_route_json/filepath', 'name': '..',
                'link_tag': (
                    '<a data-href="/folder_route_json/filepath" '
                    'href="/folder_route/filepath">..</a>'
                )
            },
            'filenames': [
                {
                    'data_href': '/file_route_json/filepath',
                    'data_relpath': 'folder1/file2.xml',
                    'name': 'file2.xml',
                    'link_tag': (
                        '<a data-href="/file_route_json/filepath" '
                        'href="/file_route/filepath" '
                        'data-relpath="folder1/file2.xml" class="file">'
                        'file2.xml</a>'
                    )
                }]
        }
        self.assertEqual(res, expected)

        # With relpath
        request = testing.DummyRequest(params={'path': ''})
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = ExplorerView(request)._get_navigation_data(
            add_previous=True,
            folder_route='folder_route',
            file_route=None,
            relpath='folder1',
            only_json=True)

        expected = {
            'folders': [],
            'path': 'folder1',
            'previous': {
                'data_href': '/folder_route_json/filepath', 'name': '..',
                'link_tag': (
                    '<a data-href="/folder_route_json/filepath" '
                    'href="/folder_route/filepath">..</a>'
                )
            },
            'filenames': [
                {
                    'data_href': '',
                    'data_relpath': 'folder1/file2.xml',
                    'name': 'file2.xml',
                    'link_tag': (
                        '<a href="#" data-relpath="folder1/file2.xml" '
                        'class="file">file2.xml</a>'
                    )
                }]
        }
        self.assertEqual(res, expected)

        res = ExplorerView(request)._get_navigation_data(
            add_previous=True,
            folder_route=None,
            file_route=None,
            relpath='',
            only_json=True)

        expected = {
            'folders': [
                {
                    'data_href': '',
                    'data_relpath': 'folder1',
                    'name': 'folder1',
                    'link_tag': (
                        '<a href="#" data-relpath="folder1" '
                        'class="folder">folder1</a>')
                }],
            'path': '',
            'previous': None,
            'filenames': [
                {
                    'data_href': '',
                    'data_relpath': 'file1.xml',
                    'name': 'file1.xml',
                    'link_tag': (
                        '<a href="#" data-relpath="file1.xml" '
                        'class="file">file1.xml</a>')
                }]
        }
        self.assertEqual(res, expected)

        res = ExplorerView(request)._get_navigation_data(
            add_previous=True,
            folder_route='folder_route',
            file_route='file_route',
            relpath='folder1',
            file_data_href_name='data-file-href',
            folder_data_href_name='data-folder-href',
            only_json=True)

        expected = {
            'folders': [],
            'path': 'folder1',
            'previous': {
                'data_href': '/folder_route_json/filepath', 'name': '..',
                'link_tag': (
                    '<a data-folder-href="/folder_route_json/filepath" '
                    'href="/folder_route/filepath">..</a>'
                )
            },
            'filenames': [
                {
                    'data_href': '/file_route_json/filepath',
                    'data_relpath': 'folder1/file2.xml',
                    'name': 'file2.xml',
                    'link_tag': (
                        '<a data-file-href="/file_route_json/filepath" '
                        'href="/file_route/filepath" '
                        'data-relpath="folder1/file2.xml" '
                        'class="file">file2.xml</a>'
                    )
                }]
        }
        self.assertEqual(res, expected)

    def test__get_navigation(self):
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = ExplorerView(request)._get_navigation()
        expected = (
            '<div class="row" style="margin-right: 0; margin-left: 0;">\n'
            '<div class="col-md-8">\n'
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
            '</ul>\n'
            '</div>\n'
            '</div>\n\n\n')
        self.assertEqual(res, expected)

        request = testing.DummyRequest(params={'path': 'folder1'})
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.current_user = self.user_bob
        self.user_bob.opened_files = [models.UserOpenedFile(path='/path')]
        res = ExplorerView(request)._get_navigation()
        expected = (
            '<div class="row" style="margin-right: 0; margin-left: 0;">\n'
            '<div class="col-md-8">\n'
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
            '</ul>\n'
            '</div>\n'
            '<div class="col-md-4">\n'
            '  <div class="panel panel-default">\n'
            '  <div class="panel-heading">Last opened files</div>\n'
            '  <div class="panel-body">\n'
            '        <a href="/filepath" data-href="/filepath">/path</a>\n'
            '      <br />\n'
            '  </div>\n'
            '</div>\n'
            '\n'
            '</div>\n'
            '</div>\n\n\n')
        self.assertEqual(res, expected)

        request.custom_route_path = lambda *args, **kw: '/%s' % args[0]
        o = ExplorerView(request)
        res = o._get_navigation()
        expected = 'data-versioning-path="/versioning_short_status_json"'
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
                u'<div class="row" style="margin-right: 0; margin-left: 0;">\n'
                u'<div class="col-md-8">\n'
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
                u'data-relpath="file1.xml">file1.xml</a></li>\n</ul>\n'
                u'</div>\n'
                u'</div>\n\n\n'),
            'breadcrumb': '<li class="active">root</li>',
            'editor_login': 'Bob',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
        }
        self.assertEqual(res, expected)

        self.user_bob.config.root_path = '/unexisting'
        res = ExplorerView(request).explore()
        expected = {
            'error_msg': "Directory . doesn't exist",
            'editor_login': u'Bob',
            'versioning': False,
            'search': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
        }
        self.assertEqual(res, expected)

    def test_folder_content(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '%s/path' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).folder_content()
        self.assertTrue('>folder1<' in res['content'])
        self.assertTrue('>file1.xml<' in res['content'])
        self.assertTrue('data-modal-href' in res['content'])
        self.assertTrue('href="folder_content/path"' in res['content'])

        res = ExplorerView(request).folder_content(folder_route='edit')
        self.assertTrue('>folder1<' in res['content'])
        self.assertTrue('>file1.xml<' in res['content'])
        self.assertTrue('data-modal-href' in res['content'])
        self.assertTrue('href="edit/path"' in res['content'])

        res = ExplorerView(request).folder_content(folder_route='edit',
                                                   relpath='folder1')
        self.assertTrue('>folder1<' not in res['content'])
        self.assertTrue('>file2.xml<' in res['content'])
        self.assertTrue('href="edit/path"' in res['content'])

    def test_open(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).open()
        keys = res.keys()
        keys.sort()
        expected_keys = [
            'editor_login', 'layout_readonly_position', 'layout_tree_position',
            'modal', 'search', 'versioning',
        ]
        self.assertEqual(keys, expected_keys)
        expected = (
            '<a data-modal-href="/filepath" href="/filepath" '
            'data-relpath="folder1" class="folder">folder1</a>'
        )
        self.assertTrue(expected in res['modal'])

        expected = (
            '<a data-href="/filepath" href="/filepath" '
            'data-relpath="file1.xml" class="file">file1.xml</a>'
        )
        self.assertTrue(expected in res['modal'])

    def test_saveas_content(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/path' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).saveas_content()
        keys = res.keys()
        keys.sort()
        expected_keys = [
            'breadcrumb',
            'content', 'editor_login', 'layout_readonly_position',
            'layout_tree_position',
            'search', 'versioning',
        ]
        self.assertEqual(keys, expected_keys)
        self.assertTrue('data-modal-href="/saveas_content_json/path"' in
                        res['content'])
        # We have 2 forms
        self.assertTrue('<form data-modal-action="/create_folder_json/path"' in
                        res['content'])
        self.assertTrue('<form class=' in res['content'])

    def test_saveas(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/path' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).saveas()
        self.assertEqual(len(res), 6)
        self.assertTrue(res['modal'])
        self.assertTrue('content' not in res)

    def test_create_folder(self):
        class C(object): pass
        try:
            path = os.path.join(os.getcwd(), 'waxe/tests/files')
            request = testing.DummyRequest()
            res = ExplorerView(request).create_folder()
            expected = {'error_msg': 'No name given'}
            self.assertEqual(res, expected)
            request = testing.DummyRequest(post={'name': 'new_folder'})
            request.custom_route_path = lambda *args, **kw: '/filepath'
            request.matched_route = C()
            request.matched_route.name = 'route'
            res = ExplorerView(request).create_folder()
            keys = res.keys()
            keys.sort()
            expected_keys = [
                'breadcrumb', 'content',
                'editor_login', 'layout_readonly_position',
                'layout_tree_position',
                'search', 'versioning',
            ]
            self.assertEqual(keys, expected_keys)
            self.assertTrue('data-modal-href' in res['content'])
            self.assertTrue('<li class=\"active\">new_folder</li>' in
                            res['breadcrumb'])
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))

            res = ExplorerView(request).create_folder()
            expected_keys = [
                'error_msg',
            ]
            keys = res.keys()
            self.assertEqual(keys, expected_keys)
            self.assertTrue('File exists' in res['error_msg'])
        finally:
            try:
                os.rmdir(os.path.join(path, 'new_folder'))
            except OSError:
                pass

    def test_search(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = ExplorerView(request).search()
        expected = {
            'error_msg': 'Nothing to search',
            'editor_login': 'Bob',
            'search': False,
            'versioning': False,
            'layout_readonly_position': 'south',
            'layout_tree_position': 'west',
        }
        self.assertEqual(res, expected)

        request = testing.DummyRequest(params={'search': 'new_folder'})
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        res = ExplorerView(request).search()
        expected = {'error_msg': 'The search is not available'}

        request.registry.settings['whoosh.path'] = '/tmp/fake'
        request.custom_route_path = lambda *args, **kw: '/filepath'
        res = ExplorerView(request).search()
        expected = {'error_msg': 'The search is not available'}

        with patch('os.path.exists', return_value=True):
            with patch('waxe.search.do_search', return_value=(None, 0)):
                res = ExplorerView(request).search()
                expected = {'content': 'No result!'}
                self.assertEqual(res, expected)

            return_value = ([
                (os.path.join(path, 'file1.xml'), 'Excerpt of the file1')
            ], 1)
            with patch('waxe.search.do_search', return_value=return_value):
                res = ExplorerView(request).search()
                expected = (
                    '\n  <a href="/filepath" '
                    'data-href="/filepath">'
                    '<i class="glyphicon glyphicon-file"></i>'
                    'file1.xml</a>\n  '
                    '<p>Excerpt of the file1</p>\n\n')
                self.maxDiff = None
                self.assertEqual(len(res), 1)
                self.assertTrue(expected in res['content'])
                self.assertTrue('class="pagination"' in res['content'])


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

    def test_folder_content_forbidden(self):
        res = self.testapp.get('/account/Bob/folder-content.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Faccount%2FBob%2Ffolder-content.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_folder_content(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/folder-content.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 2)
        self.assertTrue('content' in dic)
        self.assertTrue('breadcrumb' in dic)
        self.assertTrue('>folder1<' in dic['content'])
        self.assertTrue('>file1.xml<' in dic['content'])

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
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 1)
        self.assertTrue('modal' in dic)
        self.assertTrue('>folder1<' in dic['modal'])
        self.assertTrue('>file1.xml<' in dic['modal'])

    def test_saveas_content_forbidden(self):
        res = self.testapp.get('/account/Bob/saveas-content.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Faccount%2FBob%2Fsaveas-content.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_saveas_content(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/saveas-content.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 2)
        self.assertTrue('>folder1<' in dic['content'])
        self.assertTrue('>file1.xml<' in dic['content'])

    def test_saveas_forbidden(self):
        res = self.testapp.get('/account/Bob/saveas.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Faccount%2FBob%2Fsaveas.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_saveas(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/saveas.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 1)
        self.assertTrue('modal' in dic)
        self.assertTrue('>folder1<' in dic['modal'])
        self.assertTrue('>file1.xml<' in dic['modal'])

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
        res = self.testapp.post('/account/Bob/create-folder.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"error_msg": "No name given"}
        self.assertEqual(json.loads(res.body), expected)

        try:
            res = self.testapp.post(
                '/account/Bob/create-folder.json',
                status=200,
                params={'name': 'new_folder'})
            dic = json.loads(res.body)
            self.assertEqual(len(dic), 2)
            self.assertTrue('data-modal-href' in dic['content'])
            self.assertTrue('<li class=\"active\">new_folder</li>' in
                            dic['breadcrumb'])
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))

            res = self.testapp.post(
                '/account/Bob/create-folder.json',
                status=200,
                params={'name': 'new_folder'})
            expected = {
                u'error_msg': (
                    u"mkdir: cannot create directory \u2018%s\u2019"
                    u": File exists\n") % (os.path.join(path, 'new_folder'))
            }
            dic = json.loads(res.body)
            self.assertEqual(len(dic), 1)
            self.assertTrue('File exists' in dic['error_msg'])
        finally:
            try:
                os.rmdir(os.path.join(path, 'new_folder'))
            except OSError:
                pass

    @login_user('Bob')
    def test_search_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        self.testapp.get('/account/Bob/search.json', status=200)
