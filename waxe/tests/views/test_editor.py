import os
import json
from pyramid import testing
from mock import patch
from urllib2 import HTTPError
from ..testing import WaxeTestCase, login_user, LoggedBobTestCase

from waxe.views.editor import (
    EditorView,
    _get_tags
)


class TestEditorView(LoggedBobTestCase):

    def test__get_tags(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        res = _get_tags(dtd_url)
        expected = ['Exercise', 'comments', 'mqm', 'qcm', 'test']
        self.assertEqual(res, expected)

    def test_edit(self):
        class C(object): pass
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest()
        request.matched_route = C()
        request.matched_route.name = 'route'
        expected = {
            'editor_login': 'Bob',
            'error_msg': 'A filename should be provided',
        }
        res = EditorView(request).edit()
        self.assertEqual(res, expected)

        with patch('xmltool.generate_form', return_value='My form content'):
            expected_breadcrumb = (
                '<li><a data-href="/filepath" href="/filepath">root</a> '
                '</li>'
                '<li class="active">file1.xml</li>')
            request = testing.DummyRequest(
                params={'filename': 'file1.xml'})
            request.custom_route_path = lambda *args, **kw: '/filepath'
            request.matched_route = C()
            request.matched_route.name = 'route_json'
            res = EditorView(request).edit()
            keys = res.keys()
            keys.sort()
            self.assertEqual(keys, ['breadcrumb', 'content', 'jstree_data'])
            self.assertEqual(res['breadcrumb'],  expected_breadcrumb)
            self.assertTrue(
                '<form method="POST" id="xmltool-form" '
                'data-comment-href="/filepath" data-add-href="/filepath" '
                'data-href="/filepath">' in res['content'])
            self.assertTrue(isinstance(res['jstree_data'], dict))

            request.matched_route.name = 'route'
            res = EditorView(request).edit()
            keys = res.keys()
            keys.sort()
            self.assertEqual(keys, ['breadcrumb', 'content',
                                    'editor_login', 'jstree_data'])
            self.assertEqual(res['breadcrumb'],  expected_breadcrumb)
            self.assertTrue(
                '<form method="POST" id="xmltool-form" '
                'data-comment-href="/filepath" data-add-href="/filepath" '
                'data-href="/filepath">' in res['content'])
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
            res = EditorView(request).edit()
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
            res = EditorView(request).edit()
            self.assertEqual(res, expected)

    def test_get_tags(self):
        request = testing.DummyRequest()
        res = EditorView(request).get_tags()
        self.assertEqual(res, {})

        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        request = testing.DummyRequest(params={'dtd_url': dtd_url})
        res = EditorView(request).get_tags()
        expected = {'tags': ['Exercise', 'comments', 'mqm', 'qcm', 'test']}
        self.assertEqual(res, expected)

    def test_new(self):
        class C(object): pass
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        request = testing.DummyRequest()
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        request.dtd_urls = [dtd_url]
        res = EditorView(request).new()
        self.assertEqual(len(res), 1)
        self.assertTrue(
            '<h4 class="modal-title">New file</h4>' in res['content'])

        request = testing.DummyRequest(
            params={
                'dtd_url': dtd_url,
                'dtd_tag': 'Exercise'
            })
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        res = EditorView(request).new()
        self.assertEqual(len(res), 3)
        self.assertTrue(
            '<form method="POST" id="xmltool-form" '
            'data-comment-href="/filepath" data-add-href="/filepath" '
            'data-href="/filepath">' in res['content'])
        self.assertTrue('<a data-href="/filepath" href="/filepath">root</a>'
                        in res['breadcrumb'])
        self.assertTrue(isinstance(res['jstree_data'], dict))

        request.matched_route.name = 'route'
        res = EditorView(request).new()
        self.assertEqual(len(res), 3)
        self.assertTrue(
            '<form method="POST" id="xmltool-form" '
            'data-comment-href="/filepath" data-add-href="/filepath" '
            'data-href="/filepath">' in res['content'])
        self.assertTrue('<a data-href="/filepath" href="/filepath">root</a>'
                        in res['breadcrumb'])
        self.assertTrue(isinstance(res['jstree_data'], str))

    def test_update(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={})
        res = EditorView(request).update()
        expected = {'status': False, 'error_msg': 'No filename given'}
        self.assertEqual(res, expected)

        with patch('xmltool.update', return_value=False):
            request = testing.DummyRequest(
                params={'_xml_filename': 'test.xml'})
            request.custom_route_path = lambda *args, **kw: '/filepath'
            res = EditorView(request).update()
            expected = {
                'status': True,
                'breadcrumb': (
                    '<li><a data-href="/filepath" href="/filepath">root</a> '
                    '</li>'
                    '<li class="active">test.xml</li>')
            }
            self.assertEqual(res, expected)

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.update') as m:
            m.side_effect = raise_func
            request = testing.DummyRequest(
                params={'_xml_filename': 'test.xml'})
            request.custom_route_path = lambda *args, **kw: '/filepath'
            expected = {
                'status': False,
                'error_msg': 'My error',
            }
            res = EditorView(request).update()
            self.assertEqual(res, expected)

    def test_update_text(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={})
        res = EditorView(request).update_text()
        expected = {'status': False, 'error_msg': 'Missing parameters!'}
        self.assertEqual(res, expected)

        request = testing.DummyRequest(
            params={'filecontent': 'content of the file',
                    'filename': 'thefilename.xml'})
        request.custom_route_path = lambda *args, **kw: '/filepath'

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.load_string') as m:
            m.side_effect = raise_func
            res = EditorView(request).update_text()
            expected = {'status': False, 'error_msg': 'My error'}
            self.assertEqual(res,  expected)

        filecontent = open(os.path.join(path, 'file1.xml'), 'r').read()
        # The dtd should be an absolute url!
        filecontent = filecontent.replace('exercise.dtd',
                                          os.path.join(path, 'exercise.dtd'))
        request = testing.DummyRequest(
            params={'filecontent': filecontent,
                    'filename': 'thefilename.xml'})
        request.custom_route_path = lambda *args, **kw: '/filepath'

        with patch('xmltool.elements.Element.write', return_value=None):
            res = EditorView(request).update_text()
            expected = {'status': True, 'content': 'File updated'}
            self.assertEqual(res,  expected)

            request.params['commit'] = True
            res = EditorView(request).update_text()
            self.assertEqual(len(res), 2)
            self.assertEqual(res['status'], True)
            self.assertTrue('class="modal' in res['content'])
            self.assertTrue('Commit message' in res['content'])

    def test_update_texts(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = testing.DummyRequest(params={})
        res = EditorView(request).update_texts()
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
            res = EditorView(request).update_texts()
            expected = {'status': False, 'error_msg': 'thefilename1.xml: My error<br />thefilename2.xml: My error'}
            self.assertEqual(res,  expected)

        filecontent = open(os.path.join(path, 'file1.xml'), 'r').read()
        filecontent = filecontent.replace('exercise.dtd',
                                          os.path.join(path, 'exercise.dtd'))
        request = testing.DummyRequest(
            params={'data:0:filecontent': filecontent,
                    'data:0:filename': 'thefilename.xml'})
        request.custom_route_path = lambda *args, **kw: '/filepath'

        with patch('xmltool.elements.Element.write', return_value=None):
            res = EditorView(request).update_texts()
            expected = {'status': True, 'content': 'Files updated'}
            self.assertEqual(res,  expected)

            request.params['commit'] = True
            res = EditorView(request).update_texts()
            self.assertEqual(len(res), 2)
            self.assertEqual(res['status'], True)
            self.assertTrue('class="modal' in res['content'])
            self.assertTrue('Commit message' in res['content'])

    def test_add_element_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        request = testing.DummyRequest(params={})
        expected = {'status': False, 'error_msg': 'Bad parameter'}
        res = EditorView(request).add_element_json()
        self.assertEqual(res, expected)

        dtd_url = os.path.join(path, 'exercise.dtd')
        request = testing.DummyRequest(params={'dtd_url': dtd_url,
                                               'elt_id': 'Exercise'})
        res = EditorView(request).add_element_json()
        self.assertTrue(res)
        self.assertTrue(isinstance(res, dict))


class FunctionalTestEditorView(WaxeTestCase):

    def test_forbidden(self):

        for url in [
            '/account/Bob/edit.json',
            '/account/Bob/get-tags.json',
            '/account/Bob/new.json',
            '/account/Bob/update.json',
            '/account/Bob/update-text.json',
            '/account/Bob/update-texts.json',
            '/account/Bob/add-element.json',
            '/account/Bob/get-comment-modal.json',
        ]:
            res = self.testapp.get(url, status=302)
            self.assertTrue('http://localhost/login?next=' in res.location)
            res = res.follow()
            self.assertEqual(res.status, "200 OK")
            self.assertTrue('<form' in res.body)
            self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_edit(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/edit.json', status=200)
        expected = '{"error_msg": "A filename should be provided"}'
        self.assertEqual(res.body,  expected)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

        res = self.testapp.get('/account/Bob/edit.json',
                               status=200,
                               params={'filename': 'file1.xml'})
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 3)
        self.assertTrue(
            '<form method="POST" id="xmltool-form" '
            'data-comment-href="/account/Bob/get-comment-modal.json" '
            'data-add-href="/account/Bob/add-element.json" '
            'data-href="/account/Bob/update.json">' in dic['content'])
        self.assertTrue(isinstance(dic['jstree_data'], dict))

    @login_user('Bob')
    def test_get_tags(self):
        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/get-tags.json', status=200)
        self.assertEqual(json.loads(res.body), {})

        res = self.testapp.get('/account/Bob/get-tags.json',
                               status=200,
                               params={'dtd_url': dtd_url})
        expected = {'tags': ['Exercise', 'comments', 'mqm', 'qcm', 'test']}
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_new(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/new.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 1)
        self.assertTrue(
            '<h4 class="modal-title">New file</h4>' in dic['content'])

        dtd_url = 'http://xmltool.lereskp.fr/static/exercise.dtd'
        dtd_tag = 'Exercise'
        res = self.testapp.get('/account/Bob/new.json',
                               status=200,
                               params={'dtd_url': dtd_url,
                                       'dtd_tag': dtd_tag})
        dic = json.loads(res.body)
        self.assertEqual(len(dic), 3)
        self.assertTrue(
            '<form method="POST" id="xmltool-form" '
            'data-comment-href="/account/Bob/get-comment-modal.json" '
            'data-add-href="/account/Bob/add-element.json" '
            'data-href="/account/Bob/update.json">' in dic['content'])
        self.assertTrue(dic['breadcrumb'])
        self.assertTrue('data-href="/account/Bob/home.json?path="' in dic['breadcrumb'])
        self.assertTrue(isinstance(dic['jstree_data'], dict))

    @login_user('Bob')
    def test_update(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/update.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "No filename given"}
        self.assertEqual(json.loads(res.body), expected)

        with patch('xmltool.update', return_value=False):
            res = self.testapp.post('/account/Bob/update.json',
                                    status=200,
                                    params={'_xml_filename': 'test.xml'})
            expected = {
                "status": True,
                "breadcrumb": (
                    "<li><a data-href=\"/account/Bob/home.json?path=\" href=\"/account/Bob/?path=\">root</a> "
                    "</li>"
                    "<li class=\"active\">test.xml</li>")}
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_update_text(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/update-text.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Missing parameters!"}
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_update_texts(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/update-texts.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Missing parameters!"}
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_add_element_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/add-element.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Bad parameter"}
        self.assertEqual(json.loads(res.body), expected)

        dtd_url = os.path.join(path, 'exercise.dtd')
        res = self.testapp.get('/account/Bob/add-element.json', status=200,
                               params={'dtd_url': dtd_url,
                                       'elt_id': 'Exercise'})

        dic = json.loads(res.body)
        self.assertTrue(dic['status'])

    @login_user('Bob')
    def test_get_comment_modal_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.get('/account/Bob/get-comment-modal.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        body = json.loads(res.body)
        self.assertEqual(len(body), 1)
        self.assertTrue('<div class="modal ' in body['content'])
