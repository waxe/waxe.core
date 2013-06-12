import os
import simplejson
from pyramid import testing
from ..testing import WaxeTestCase, WaxeTestCaseVersioning, login_user
from mock import patch, MagicMock
from ..models import (
    DBSession,
    UserConfig,
)

from ..views.versioning import (
    Views,
)
import pysvn


class TestViews(WaxeTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config = testing.setUp(settings=self.settings)

    def tearDown(self):
        testing.tearDown()
        super(TestViews, self).tearDown()

    def test_svn_status(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request).svn_status()
        expected = {'files_data': [
            (pysvn.wc_status_kind.modified, 'label-info', u'file1.xml', '/svn_diff/filepath'),
            (pysvn.wc_status_kind.unversioned, 'label-default', u'file3.xml', '/svn_diff/filepath'),
            (pysvn.wc_status_kind.added, None, u'file4.xml', '/svn_diff/filepath')
        ]}
        expected = {'content': (
            u'<div class="ui-layout-center">\n'
            u'  <ul>\n'
            u'    <li>\n'
            u'      <span class="label label-info">modified</span>\n'
            u'      <a href="/svn_diff/filepath" '
            u'data-href="/svn_diff_json/filepath">file1.xml</a>\n'
            u'    </li>\n'
            u'    <li>\n'
            u'      <span class="label label-default">unversioned</span>\n'
            u'      <a href="/svn_diff/filepath" '
            u'data-href="/svn_diff_json/filepath">file3.xml</a>\n'
            u'    </li>\n'
            u'    <li>\n'
            u'      <span class="label None">added</span>\n'
            u'      <a href="/svn_diff/filepath" '
            u'data-href="/svn_diff_json/filepath">file4.xml</a>\n'
            u'    </li>\n'
            u'  </ul>\n'
            u'</div>\n'
        )}
        self.assertEqual(res, expected)

    def test_svn_diff(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        res = Views(request).svn_diff()
        expected = {'error_msg': 'A filename should be provided'}
        self.assertEqual(res, expected)

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filename': 'file1.xml'})
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filename': 'file3.xml'})
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)

    def test_svn_update(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        res = Views(request).svn_update()
        expected = {'content': 'At revision 1.\n'}
        self.assertEqual(res, expected)

    def test_svn_commit_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        res = Views(request).svn_commit_json()
        expected = {"status": False, "error_msg": "Bad parameters!"}
        self.assertEqual(res, expected)

        mock = MagicMock()
        mock.status = MagicMock(return_value=[pysvn.wc_status_kind.normal])
        request = testing.DummyRequest(
            root_path=svn_path,
            params={'filename': 'test.xml',
                    'msg': 'my commit message'})
        with patch('waxe.views.versioning.Views.get_svn_client', return_value=mock):
            res = Views(request).svn_commit_json()
            mock.checkin.assert_called_once_with(
                os.path.join(svn_path, 'test.xml'),
                'my commit message')
            expected = {'status': True, 'content': 'Commit done'}
            self.assertEqual(res, expected)

        mock = MagicMock(side_effect=Exception('Error'))
        mock.checkin = MagicMock(side_effect=Exception('Error'))
        mock.status = MagicMock(return_value=[pysvn.wc_status_kind.normal])
        with patch('waxe.views.versioning.Views.get_svn_client',
                   return_value=mock):
            res = Views(request).svn_commit_json()
            expected = {'status': False, 'error_msg': 'Error'}
            self.assertEqual(res, expected)
            mock.checkin.assert_called_once_with(
                os.path.join(svn_path, 'test.xml'),
                'my commit message')

        mock.status = MagicMock(return_value=[pysvn.wc_status_kind.conflicted])
        with patch('waxe.views.versioning.Views.get_svn_client', return_value=mock):
            res = Views(request).svn_commit_json()
            expected = {
                'status': False,
                'error_msg': "Can't commit a conflicted file"
            }
            self.assertEqual(res, expected)

        mock = MagicMock()
        mock.status = MagicMock(return_value=[pysvn.wc_status_kind.unversioned])
        with patch('waxe.views.versioning.Views.get_svn_client', return_value=mock):
            res = Views(request).svn_commit_json()
            mock.add.assert_called_once_with(
                os.path.join(svn_path, 'test.xml'))
            mock.checkin.assert_called_once_with(
                os.path.join(svn_path, 'test.xml'),
                'my commit message')
            expected = {'status': True, 'content': 'Commit done'}
            self.assertEqual(res, expected)


class FunctionalTestViewsNoVersioning(WaxeTestCase):

    def test_404(self):
        for url in [
            '/versioning/status',
            '/versioning/status.json',
            '/versioning/diff',
            '/versioning/diff.json',
            '/versioning/update',
            '/versioning/update.json',
            '/versioning/commit.json',
        ]:
            self.testapp.get('/versioning/status', status=404)


class FunctionalTestViews(WaxeTestCaseVersioning):

    def test_svn_status_forbidden(self):
        res = self.testapp.get('/versioning/status', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fstatus')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_status(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/status', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)

    def test_svn_status_json_forbidden(self):
        res = self.testapp.get('/versioning/status.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fstatus.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_status_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/status.json', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    def test_svn_diff_forbidden(self):
        res = self.testapp.get('/versioning/diff', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fdiff')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_diff(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/diff', status=200)
        self.assertTrue('Error: A filename should be provided' in res.body)

        res = self.testapp.get('/versioning/diff', status=200,
                               params={'filename': 'file1.xml'})
        self.assertTrue('diff' in res.body)

    def test_svn_diff_json_forbidden(self):
        res = self.testapp.get('/versioning/diff.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fdiff.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_diff_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/diff.json', status=200)
        self.assertTrue('A filename should be provided' in res.body)

        res = self.testapp.get('/versioning/diff.json', status=200,
                               params={'filename': 'file1.xml'})
        self.assertTrue('diff' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    def test_svn_update_forbidden(self):
        res = self.testapp.get('/versioning/update', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fupdate')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_update(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/update', status=200)
        self.assertTrue('At revision 1.' in res.body)

    def test_svn_update_json_forbidden(self):
        res = self.testapp.get('/versioning/update.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fupdate.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_update_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/update.json', status=200)
        self.assertTrue('At revision 1.' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    def test_svn_commit_json_forbidden(self):
        res = self.testapp.get('/versioning/commit.json', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Fversioning%2Fcommit.json')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_svn_commit_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        DBSession.add(self.user_bob)
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/versioning/commit.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Bad parameters!"}
        self.assertEqual(simplejson.loads(res.body), expected)
