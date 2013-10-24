import os
import json
from pyramid import testing
from pyramid.exceptions import Forbidden
from webob.multidict import MultiDict
from ..testing import (
    WaxeTestCase,
    WaxeTestCaseVersioning,
    login_user,
)
from .. import security
from mock import patch, MagicMock
from ..models import (
    DBSession,
    User,
    UserConfig,
    VersioningPath,
    Role,
    ROLE_CONTRIBUTOR,
    VERSIONING_PATH_STATUS_ALLOWED,
    VERSIONING_PATH_STATUS_FORBIDDEN,
)

from ..views.versioning import (
    Views,
)
import pysvn


class TestViews(WaxeTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config = testing.setUp(settings=self.settings)
        self.config.registry.settings.update({
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.security.'
                                               'get_user_permissions')
        })
        self.config.include('pyramid_auth')

        self.config.include('pyramid_mako')

    def tearDown(self):
        testing.tearDown()
        super(TestViews, self).tearDown()

    def test_svn_cmd(self):
        self.config.testing_securitypolicy(userid='Fred', permissive=True)
        request = testing.DummyRequest()
        res = Views(request).svn_cmd('update')
        expected = 'svn update --non-interactive'
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        res = Views(request).svn_cmd('update')
        expected = ('svn update --non-interactive '
                    '--username Fred --password secret_fred')
        self.assertEqual(res, expected)

    def test_svn_cmd_failed(self):
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        request = testing.DummyRequest()
        request.registry.settings['versioning.auth.active'] = True
        try:
            Views(request).svn_cmd('update')
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'No versioning password set for Bob')

    def test_get_svn_login(self):
        request = testing.DummyRequest()
        view = Views(request)
        view.current_user = self.user_bob
        try:
            view.get_svn_login()
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'No versioning password set for Bob')

        self.user_bob.config = UserConfig(
            root_path='',
            use_versioning=True,
            versioning_password='secret_bob',
        )
        res = view.get_svn_login()
        expected = (False, 'Bob', 'secret_bob', False)
        self.assertEqual(res, expected)

        view = Views(request)
        view.current_user = self.user_fred
        res = view.get_svn_login()
        expected = (False, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        view = Views(request)
        view.current_user = self.user_fred
        res = view.get_svn_login()
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.pwd'] = 'secret'
        view = Views(request)
        view.current_user = self.user_fred
        res = view.get_svn_login()
        expected = (True, 'Fred', 'secret', False)
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_svn_status(self):
        DBSession.add(self.user_bob)
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config.root_path = svn_path
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request).svn_status()
        self.assertEqual(len(res), 1)
        self.assertTrue('<form' in res['content'])
        self.assertTrue('file1.xml' in res['content'])
        self.assertTrue('file3.xml' in res['content'])
        self.assertTrue('file4.xml' in res['content'])

    @login_user('Bob')
    def test_svn_diff(self):
        DBSession.add(self.user_bob)
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config.root_path = svn_path
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.GET = MultiDict()
        res = Views(request).svn_diff()
        expected = {'error_msg': 'You should provide at least one filename.'}
        self.assertEqual(res, expected)

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file1.xml'})
        request.context = security.RootFactory(request)
        request.GET = MultiDict({'filenames': 'file1.xml'})
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file3.xml'})
        request.context = security.RootFactory(request)
        request.GET = MultiDict({'filenames': 'file3.xml'})
        request.route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = Views(request).svn_diff()
        self.assertEqual(len(res), 1)
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])

        request = testing.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file3.xml'})
        request.context = security.RootFactory(request)
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

    @login_user('Fred')
    def test_svn_update(self):
        DBSession.add(self.user_fred)
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_fred.config.root_path = svn_path
        request = testing.DummyRequest()
        res = Views(request).svn_update()
        expected = {'content': '<pre>At revision 1.\n</pre>'}
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_svn_commit_json(self):
        with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
            DBSession.add(self.user_bob)
            svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
            self.user_bob.config.root_path = svn_path
            request = testing.DummyRequest(root_path=svn_path)
            request.context = security.RootFactory(request)
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
            request.context = security.RootFactory(request)
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

    def test_can_commit(self):
        user = User(login='user1', password='pass1')
        DBSession.add(user)

        request = testing.DummyRequest()
        request.context = security.RootFactory(request)

        user.roles = [self.role_admin]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
                view = Views(request)
                res = view.can_commit('/home/test/myfile.xml')
                self.assertEqual(res, True)

        user.roles = [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
                view = Views(request)
                res = view.can_commit('/home/test/myfile.xml')
                self.assertEqual(res, True)

        user.roles = []
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            view = Views(request)
            try:
                res = view.can_commit('/home/test/folder1/myfile.xml')
                assert(False)
            except Exception, e:
                self.assertEqual(str(e),
                                 'Invalid path /home/test/folder1/myfile.xml')

            with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
                try:
                    res = view.can_commit('/home/test/folder1/myfile.xml')
                    assert(False)
                except AssertionError, e:
                    self.assertEqual(str(e), 'You are not a contributor')

                # By default a contributor can't commit
                user.roles = [self.role_contributor]
                res = view.can_commit('/home/test/folder1/myfile.xml')
                self.assertEqual(res, False)

                user.versioning_paths += [VersioningPath(
                    status=VERSIONING_PATH_STATUS_ALLOWED,
                    path='/home/test/')]
                res = view.can_commit('/home/test/folder1/myfile.xml')
                self.assertEqual(res, True)

                user.versioning_paths += [VersioningPath(
                    status=VERSIONING_PATH_STATUS_FORBIDDEN,
                    path='/home/test/folder1')]
                res = view.can_commit('/home/test/folder1/myfile.xml')
                self.assertEqual(res, False)
                res = view.can_commit('/home/test/myfile.xml')
                self.assertEqual(res, True)
                res = view.can_commit('/home/test/folder1.xml')
                self.assertEqual(res, True)


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
        self.user_bob.config = UserConfig(root_path=svn_path,
                                          versioning_password='secret_bob')
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
        self.user_bob.config = UserConfig(root_path=svn_path,
                                          versioning_password='secret_bob')
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
        self.assertEqual(json.loads(res.body), expected)

