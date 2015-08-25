import os
import json
from pyramid import testing
import pyramid.httpexceptions as exc
from webob.multidict import MultiDict
from mock import patch
from waxe.core.tests.testing import LoggedBobTestCase, WaxeTestCase, login_user
from waxe.core.views.filemanager import FileManagerView


class TestFileManagerView(LoggedBobTestCase):

    def test_explore(self):
        class C(object): pass
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route'
        res = FileManagerView(request).explore()
        expected = [
            {
                'status': None,
                'link': u'folder1',
                'type': 'folder',
                'name': u'folder1'
            },
            {
                'status': None,
                'link': u'file1.xml',
                'type': 'file',
                'name': u'file1.xml'
            }]
        self.assertEqual(res, expected)

        self.user_bob.config.root_path = '/unexisting'
        try:
            res = FileManagerView(request).explore()
            assert(False)
        except exc.HTTPNotFound, e:
            expected = "Directory . doesn't exist"
            self.assertEqual(str(e), expected)

    def test_create_folder(self):
        class C(object): pass
        try:
            path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
            request = testing.DummyRequest()
            try:
                res = FileManagerView(request).create_folder()
                assert(False)
            except exc.HTTPClientError, e:
                self.assertEqual(str(e), 'No name given')

            request = testing.DummyRequest(post={'name': 'new_folder'})
            request.custom_route_path = lambda *args, **kw: '/filepath'
            request.matched_route = C()
            request.matched_route.name = 'route'
            res = FileManagerView(request).create_folder()
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))

            try:
                FileManagerView(request).create_folder()
            except exc.HTTPInternalServerError, e:
                self.assertTrue('File exists' in str(e))
        finally:
            try:
                os.rmdir(os.path.join(path, 'new_folder'))
            except OSError:
                pass

    def test_search(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
        self.user_bob.config.root_path = path

        request = testing.DummyRequest(params={'search': 'new_folder'})
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        request.custom_route_path = lambda *args, **kw: '/filepath'

        try:
            res = FileManagerView(request).search()
            assert(False)
        except exc.HTTPInternalServerError, e:
            self.assertEqual(str(e), 'The search is not available')

        request.registry.settings['whoosh.path'] = '/tmp/fake'
        try:
            res = FileManagerView(request).search()
            assert(False)
        except exc.HTTPInternalServerError, e:
            self.assertEqual(str(e), 'The search is not available')

        with patch('os.path.exists', return_value=True):
            with patch('waxe.core.search.do_search', return_value=(None, 0)):
                res = FileManagerView(request).search()
                self.assertEqual(res['nb_items'], 0)

            return_value = ([
                {'path': os.path.join(path, 'file1.xml'),
                 'tag': 'tag',
                 'excerpt': 'Excerpt of the file1'}
            ], 1)
            with patch('waxe.core.search.do_search', return_value=return_value):
                res = FileManagerView(request).search()
                self.assertEqual(res['nb_items'], 1)
                self.assertEqual(len(res['results']), 1)
                self.assertEqual(res['results'], return_value[0])

    def test_remove(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
        self.user_bob.config.root_path = path

        request = testing.DummyRequest()
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        request.custom_route_path = lambda *args, **kw: '/filepath'

        try:
            FileManagerView(request).remove()
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'No filename given')

        request = testing.DummyRequest(
            post=MultiDict([
                ('paths', 'unexisting1.xml'),
                ('paths', 'unexisting2.xml')
            ]))

        try:
            FileManagerView(request).remove()
            assert(False)
        except exc.HTTPClientError, e:
            expected = (
                "The following filenames don't exist: "
                "unexisting1.xml, unexisting2.xml"
            )
            self.assertEqual(str(e), expected)

        request = testing.DummyRequest(
            post=MultiDict([
                ('paths', 'file1.xml'),
            ]))

        with patch('os.remove', return_value=True):
            res = FileManagerView(request).remove()
            self.assertEqual(res, True)


class TestFunctionalTestFileManagerView(WaxeTestCase):

    def test_permissions(self):
        self.testapp.get('/api/1/account/Bob/explore.json', status=401)
        self.testapp.get('/api/1/account/Bob/create-folder.json', status=401)
        self.testapp.get('/api/1/account/Bob/search.json', status=401)
        self.testapp.get('/api/1/account/Bob/remove.json', status=401)

    @login_user('Admin')
    def test_explore_json_admin(self):
        res = self.testapp.get('/api/1/account/Admin/explore.json', status=400)
        self.assertEqual(res.body, '"root path not defined"')

    @login_user('Bob')
    def test_explore_json(self):
        self.user_bob.config.root_path = '/unexisting'
        res = self.testapp.get('/api/1/account/Bob/explore.json', status=404)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        # TODO: add more tests

    @login_user('Bob')
    def test_create_folder(self):
        path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/api/1/account/Bob/create-folder.json', status=400)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        self.assertEqual(res.body, '"No name given"')

        try:
            res = self.testapp.post(
                '/api/1/account/Bob/create-folder.json',
                status=200,
                params={'name': 'new_folder'})
            dic = json.loads(res.body)
            self.assertEqual(len(dic), 3)
            self.assertTrue(os.path.isdir(os.path.join(path, 'new_folder')))

            res = self.testapp.post(
                '/api/1/account/Bob/create-folder.json',
                status=500,
                params={'name': 'new_folder'})
            self.assertTrue('File exists' in res.body)
        finally:
            try:
                os.rmdir(os.path.join(path, 'new_folder'))
            except OSError:
                pass

    @login_user('Bob')
    def test_search_json(self):
        path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
        self.user_bob.config.root_path = path
        self.testapp.get('/api/1/account/Bob/search.json', status=500)
