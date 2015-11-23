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
                'path': u'folder1',
                'type': 'folder',
                'name': u'folder1'
            },
            {
                'status': None,
                'path': u'file1.xml',
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

    def test_remove(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
        self.user_bob.config.root_path = path

        request = testing.DummyRequest(GET=MultiDict())
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        request.custom_route_path = lambda *args, **kw: '/filepath'

        try:
            FileManagerView(request).remove()
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'No filename given')

        request = testing.DummyRequest(
            GET=MultiDict([
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

        os.mkdir(os.path.join(path, 'newfolder'))
        request = testing.DummyRequest(
            GET=MultiDict([
                ('paths', 'newfolder'),
            ]))

        res = FileManagerView(request).remove()
        self.assertEqual(res, True)

        with open(os.path.join(path, 'newfile.xml'), 'w') as f:
            f.write('empty')
        request = testing.DummyRequest(
            GET=MultiDict([
                ('paths', 'newfile.xml'),
            ]))

        res = FileManagerView(request).remove()
        self.assertEqual(res, True)

    def test_move(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/core/tests/files')
        self.user_bob.config.root_path = path

        request = testing.DummyRequest(GET=MultiDict())
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        request.custom_route_path = lambda *args, **kw: '/filepath'

        try:
            FileManagerView(request).move()
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'No filename given')

        request = testing.DummyRequest(
            post=MultiDict([
                ('paths', 'unexisting1.xml'),
                ('paths', 'unexisting2.xml')
            ]))

        try:
            FileManagerView(request).move()
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'No destination given')

        request = testing.DummyRequest(
            post=MultiDict([
                ('paths', 'unexisting1.xml'),
                ('paths', 'unexisting2.xml'),
                ('newpath', '')
            ]))

        try:
            FileManagerView(request).move()
            assert(False)
        except exc.HTTPClientError, e:
            expected = (
                "Can't move the following filenames: "
                "unexisting1.xml, unexisting2.xml"
            )
            self.assertEqual(str(e), expected)

        os.mkdir(os.path.join(path, 'newfolder'))
        request = testing.DummyRequest(
            post=MultiDict([
                ('paths', 'newfolder'),
                ('newpath', 'folder1')
            ]))

        res = FileManagerView(request).move()
        self.assertEqual(res, True)

        try:
            FileManagerView(request).move()
            assert(False)
        except exc.HTTPClientError, e:
            expected = (
                "Can't move the following filenames: "
                "newfolder"
            )
            self.assertEqual(str(e), expected)
        os.rmdir(os.path.join(path, 'folder1', 'newfolder'))

        with open(os.path.join(path, 'newfile.xml'), 'w') as f:
            f.write('empty')
        request = testing.DummyRequest(
            post=MultiDict([
                ('paths', 'newfile.xml'),
                ('newpath', 'folder1')
            ]))

        res = FileManagerView(request).move()
        self.assertEqual(res, True)
        os.remove(os.path.join(path, 'folder1', 'newfile.xml'))


class TestFunctionalTestFileManagerView(WaxeTestCase):

    def test_permissions(self):
        self.testapp.get('/api/1/account/Bob/explore.json', status=401)
        self.testapp.get('/api/1/account/Bob/create-folder.json', status=401)

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
