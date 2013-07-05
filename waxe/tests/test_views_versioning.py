import os
import simplejson
from pyramid import testing
from pyramid.exceptions import Forbidden
from webob.multidict import MultiDict
from ..testing import WaxeTestCase, WaxeTestCaseVersioning, login_user
from mock import patch, MagicMock
from ..models import (
    DBSession,
    UserConfig,
    Role,
    ROLE_CONTRIBUTOR,
)

from ..views.versioning import (
    Views,
    get_svn_login,
    svn_cmd,
)
import pysvn


class TestViews(WaxeTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config = testing.setUp(settings=self.settings)

    def tearDown(self):
        testing.tearDown()
        super(TestViews, self).tearDown()

    def test_svn_cmd(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        request.user = self.user_bob
        res = svn_cmd(request, 'update')
        expected = 'svn update --non-interactive'
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        res = svn_cmd(request, 'update')
        expected = ('svn update --non-interactive '
                    '--username Bob --password secret_bob')
        self.assertEqual(res, expected)

    def test_get_svn_login(self):
        DBSession.add(self.user_bob)
        request = testing.DummyRequest()
        request.user = self.user_bob
        res = get_svn_login(request)
        expected = (False, 'Bob', 'secret_bob', False)
        self.assertEqual(res, expected)

        request.session['editor_login'] = 'Fred'
        res = get_svn_login(request)
        expected = (False, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        res = get_svn_login(request)
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.pwd'] = 'secret'
        res = get_svn_login(request)
        expected = (True, 'Fred', 'secret', False)
        self.assertEqual(res, expected)

    def test_svn_status(self):
        DBSession.add(self.user_bob)
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        request.user = self.user_bob
        res = Views(request).svn_status()
        self.assertEqual(len(res), 1)
        self.assertTrue('<form' in res['content'])
        self.assertTrue('file1.xml' in res['content'])
        self.assertTrue('file3.xml' in res['content'])
        self.assertTrue('file4.xml' in res['content'])

    def test_svn_diff(self):
        DBSession.add(self.user_bob)
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        request.GET = MultiDict()
        res = Views(request).svn_diff()
        expected = {'error_msg': 'You should provide at least one filename.'}
        self.assertEqual(res, expected)

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file1.xml'})
        request.user = self.user_bob
        request.GET = MultiDict({'filenames': 'file1.xml'})
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file3.xml'})
        request.user = self.user_bob
        request.GET = MultiDict({'filenames': 'file3.xml'})
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file3.xml'})
        request.user = self.user_bob
        request.GET = MultiDict({'filenames': 'file3.xml'})
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        self.user_bob.roles = [Role(name=ROLE_CONTRIBUTOR)]
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' not in res['content'])

        request.GET = MultiDict([('filenames', 'file1.xml'),
                                 ('filenames', 'file3.xml')])
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 2)
        self.assertTrue('submit' not in res['content'])

    def test_svn_update(self):
        DBSession.add(self.user_bob)
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        request = testing.DummyRequest(root_path=svn_path)
        request.user = self.user_bob
        res = Views(request).svn_update()
        expected = {'content': '<pre>At revision 1.\n</pre>'}
        self.assertEqual(res, expected)

    def test_svn_commit_json(self):
        with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
            DBSession.add(self.user_bob)
            svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
            request = testing.DummyRequest(root_path=svn_path)
            request.user = self.user_bob
            res = Views(request).svn_commit_json()
            expected = {"status": False, "error_msg": "Bad parameters!"}
            self.assertEqual(res, expected)

            mock = MagicMock()
            status_mock = MagicMock()
            status_mock.text_status = pysvn.wc_status_kind.normal
            mock.status = MagicMock(return_value=[status_mock])
            request = testing.DummyRequest(
                root_path=svn_path,
                params={'data': [{'filename': 'test.xml'}],
                        'msg': 'my commit message'})
            request.user = self.user_bob
            with patch('waxe.views.versioning.Views.get_svn_client', return_value=mock):
                res = Views(request).svn_commit_json()
                mock.checkin.assert_called_once_with(
                    [os.path.join(svn_path, 'test.xml')],
                    'my commit message')
                expected = {'status': True, 'content': 'Commit done'}
                self.assertEqual(res, expected)

            mock = MagicMock(side_effect=Exception('Error'))
            mock.checkin = MagicMock(side_effect=Exception('Error'))
            status_mock = MagicMock()
            status_mock.text_status = pysvn.wc_status_kind.normal
            mock.status = MagicMock(return_value=[status_mock])
            with patch('waxe.views.versioning.Views.get_svn_client',
                       return_value=mock):
                res = Views(request).svn_commit_json()
                expected = {'status': False,
                            'error_msg': 'Can\'t commit test.xml'}
                self.assertEqual(res, expected)
                mock.checkin.assert_called_once_with(
                    [os.path.join(svn_path, 'test.xml')],
                    'my commit message')

            status_mock = MagicMock()
            status_mock.text_status = pysvn.wc_status_kind.conflicted
            mock.status = MagicMock(return_value=[status_mock])
            with patch('waxe.views.versioning.Views.get_svn_client', return_value=mock):
                res = Views(request).svn_commit_json()
                expected = {
                    'status': False,
                    'error_msg': "Can't commit conflicted file: test.xml"
                }
                self.assertEqual(res, expected)

            mock = MagicMock()
            status_mock = MagicMock()
            status_mock.text_status = pysvn.wc_status_kind.unversioned
            mock.status = MagicMock(return_value=[status_mock])
            with patch('waxe.views.versioning.Views.get_svn_client', return_value=mock):
                res = Views(request).svn_commit_json()
                mock.add.assert_called_once_with(
                    os.path.join(svn_path, 'test.xml'))
                mock.checkin.assert_called_once_with(
                    [os.path.join(svn_path, 'test.xml')],
                    'my commit message')
                expected = {'status': True, 'content': 'Commit done'}
                self.assertEqual(res, expected)

            # No permission
            self.user_bob.roles = []
            try:
                res = Views(request).svn_commit_json()
                assert 0
            except Exception, e:
                self.assertEqual(str(e), 'You are not a contributor')

            self.user_bob.roles = [Role(name=ROLE_CONTRIBUTOR)]
            try:
                res = Views(request).svn_commit_json()
            except Forbidden, e:
                self.assertEqual(str(e), 'Restricted area')


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
        self.assertTrue('Error: You should provide at least one filename' in res.body)

        res = self.testapp.get('/versioning/diff', status=200,
                               params={'filenames': 'file1.xml'})
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
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.get('/versioning/diff.json', status=200,
                               params={'filenames': 'file1.xml'})
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
