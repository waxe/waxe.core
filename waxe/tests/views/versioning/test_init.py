import os
import sys
import json
import unittest
import shutil
from subprocess import Popen, PIPE
from pyramid import testing
from pyramid.exceptions import Forbidden
from webob.multidict import MultiDict
from mock import patch, MagicMock
import pysvn
from waxe.tests.testing import (
    WaxeTestCase,
    WaxeTestCaseVersioning,
    login_user,
    BaseTestCase,
)
from waxe import security
from waxe.models import (
    DBSession,
    User,
    UserConfig,
    VersioningPath,
    VERSIONING_PATH_STATUS_ALLOWED,
    VERSIONING_PATH_STATUS_FORBIDDEN,
)

from waxe.views.versioning.pysvn_backend import (
    PysvnView,
)

from waxe.views.versioning.python_svn_backend import (
    PythonSvnView,
)

from waxe.views.versioning import helper


class FakeSvnStatus(object):

    def __init__(self, path, status):
        self.path = path
        self.text_status = getattr(pysvn.wc_status_kind, status)


class EmptyClass(object):
    pass


class SvnViewTester(object):
    ClassView = None

    get_svn_client_str = ('waxe.views.versioning.'
                          'pysvn_backend.PysvnView.get_svn_client')

    def DummyRequest(self, *args, **kw):
        request = testing.DummyRequest(*args, **kw)
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'
        return request

    def setUp(self):
        super(SvnViewTester, self).setUp()
        self.config.registry.settings.update({
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.security.'
                                               'get_user_permissions')
        })
        self.config.include('pyramid_auth')

    def test_svn_cmd(self):
        self.config.testing_securitypolicy(userid='Fred', permissive=True)
        request = self.DummyRequest()
        res = self.ClassView(request).svn_cmd('update')
        expected = 'svn update --non-interactive'
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        res = self.ClassView(request).svn_cmd('update')
        expected = ('svn update --non-interactive '
                    '--username Fred --password secret_fred')
        self.assertEqual(res, expected)

    def test_svn_cmd_failed(self):
        self.config.testing_securitypolicy(userid='Bob', permissive=True)
        request = self.DummyRequest()
        request.registry.settings['versioning.auth.active'] = True
        try:
            self.ClassView(request).svn_cmd('update')
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'No versioning password set for Bob')

    @login_user('Bob')
    def test_get_svn_login(self):
        request = self.DummyRequest()
        self.user_bob.config = UserConfig(
            root_path='/root_path',
            use_versioning=True,
        )
        view = self.ClassView(request)

        res = view.get_svn_login()
        expected = (False, 'Bob', None, False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        try:
            view.get_svn_login()
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'No versioning password set for Bob')

        self.user_bob.config.versioning_password = 'secret_bob'
        res = view.get_svn_login()
        expected = (True, 'Bob', 'secret_bob', False)
        self.assertEqual(res, expected)

        view = self.ClassView(request)
        view.current_user = self.user_fred
        res = view.get_svn_login()
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        view = self.ClassView(request)
        view.current_user = self.user_fred
        res = view.get_svn_login()
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.pwd'] = 'secret'
        view = self.ClassView(request)
        view.current_user = self.user_fred
        res = view.get_svn_login()
        expected = (True, 'Fred', 'secret', False)
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_status(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config.root_path = svn_path
        request = self.DummyRequest()
        res = self.ClassView(request).status()
        self.assertEqual(len(res), 3)
        self.assertEqual(res.keys(), ['content', 'editor_login', 'versioning'])
        self.assertTrue('<form' in res['content'])
        self.assertTrue('file1.xml' in res['content'])
        self.assertTrue('file3.xml' in res['content'])
        self.assertTrue('file4.xml' in res['content'])

    @login_user('Bob')
    def test_diff(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config.root_path = svn_path
        request = self.DummyRequest()
        request.GET = MultiDict()
        res = self.ClassView(request).diff()
        expected = {
            'error_msg': 'You should provide at least one filename.',
            'editor_login': 'Bob',
            'versioning': False,
        }
        self.assertEqual(res, expected)

        request = self.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file1.xml'})
        request.GET = MultiDict({'filenames': 'file1.xml'})
        res = self.ClassView(request).diff()
        self.assertEqual(len(res), 3)
        self.assertEqual(res.keys(), ['content', 'editor_login', 'versioning'])
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])

        request = self.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file3.xml'})
        request.GET = MultiDict({'filenames': 'file3.xml'})
        res = self.ClassView(request).diff()
        self.assertEqual(len(res), 3)
        self.assertEqual(res.keys(), ['content', 'editor_login', 'versioning'])
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])

        request = self.DummyRequest(root_path=svn_path,
                                       params={'filenames': 'file3.xml'})
        request.GET = MultiDict({'filenames': 'file3.xml'})
        self.user_bob.roles = [self.role_contributor]
        res = self.ClassView(request).diff()
        self.assertEqual(len(res), 3)
        self.assertEqual(res.keys(), ['content', 'editor_login', 'versioning'])
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' not in res['content'])

        request.GET = MultiDict([('filenames', 'file1.xml'),
                                 ('filenames', 'file3.xml')])
        res = self.ClassView(request).diff()
        self.assertEqual(len(res), 3)
        self.assertEqual(res.keys(), ['content', 'editor_login', 'versioning'])
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 2)
        self.assertTrue('submit' not in res['content'])

    @login_user('Bob')
    def test_commit(self):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
                self.user_bob.config.root_path = svn_path
                request = self.DummyRequest(root_path=svn_path)
                res = self.ClassView(request).commit()
                expected = {"status": False,
                            "error_msg": "Bad parameters!",
                            'editor_login': 'Bob',
                            'versioning': False,
                           }
                self.assertEqual(res, expected)

                mock = MagicMock()
                status_mock = MagicMock()
                status_mock.text_status = pysvn.wc_status_kind.normal
                mock.status = MagicMock(return_value=[status_mock])
                request = self.DummyRequest(
                    root_path=svn_path,
                    params={'data': [{'filename': 'test.xml'}],
                            'msg': 'my commit message'})
                with patch(self.get_svn_client_str, return_value=mock):
                    res = self.ClassView(request).commit()
                    mock.checkin.assert_called_once_with(
                        [os.path.join(svn_path, 'test.xml')],
                        'my commit message')
                    expected = {'status': True,
                                'content': 'Commit done',
                                'editor_login': 'Bob',
                                'versioning': False
                               }
                    self.assertEqual(res, expected)

                mock = MagicMock(side_effect=Exception('Error'))
                mock.checkin = MagicMock(side_effect=Exception('Error'))
                status_mock = MagicMock()
                status_mock.text_status = pysvn.wc_status_kind.normal
                mock.status = MagicMock(return_value=[status_mock])
                with patch(self.get_svn_client_str, return_value=mock):
                    res = self.ClassView(request).commit()
                    expected = {'status': False,
                                'error_msg': 'Can\'t commit test.xml',
                                'editor_login': 'Bob',
                                'versioning': False,
                               }
                    self.assertEqual(res, expected)
                    mock.checkin.assert_called_once_with(
                        [os.path.join(svn_path, 'test.xml')],
                        'my commit message')

                status_mock = MagicMock()
                status_mock.text_status = pysvn.wc_status_kind.conflicted
                mock.status = MagicMock(return_value=[status_mock])
                with patch(self.get_svn_client_str, return_value=mock):
                    res = self.ClassView(request).commit()
                    expected = {
                        'status': False,
                        'error_msg': "Can't commit conflicted file: test.xml",
                        'editor_login': 'Bob',
                        'versioning': False,
                    }
                    self.assertEqual(res, expected)

                mock = MagicMock()
                status_mock = MagicMock()
                status_mock.text_status = pysvn.wc_status_kind.unversioned
                mock.status = MagicMock(return_value=[status_mock])
                with patch(self.get_svn_client_str, return_value=mock):
                    res = self.ClassView(request).commit()
                    mock.add.assert_called_once_with(
                        os.path.join(svn_path, 'test.xml'))
                    mock.checkin.assert_called_once_with(
                        [os.path.join(svn_path, 'test.xml')],
                        'my commit message')
                    expected = {'status': True,
                                'content': 'Commit done',
                                'editor_login': 'Bob',
                                'versioning': False,
                               }
                    self.assertEqual(res, expected)

                # No permission
                self.user_bob.roles = []
                try:
                    res = self.ClassView(request).commit()
                    assert 0
                except Exception, e:
                    self.assertEqual(str(e), 'You are not a contributor')

                self.user_bob.roles = [self.role_contributor]
                try:
                    res = self.ClassView(request).commit()
                except Forbidden, e:
                    self.assertEqual(str(e), 'Restricted area')

    def test_can_commit(self):
        user = User(login='user1', password='pass1')
        user.config = UserConfig(root_path='/root_path')
        DBSession.add(user)

        request = self.DummyRequest()

        user.roles = [self.role_admin]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
                view = self.ClassView(request)
                res = view.can_commit('/home/test/myfile.xml')
                self.assertEqual(res, True)

        user.roles = [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            with patch('os.path.exists', return_value=True), patch('os.path.isfile', return_value=True):
                view = self.ClassView(request)
                res = view.can_commit('/home/test/myfile.xml')
                self.assertEqual(res, True)

        user.roles = []
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            view = self.ClassView(request)
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


class TestPysvnView(SvnViewTester, BaseTestCase):
    ClassView = PysvnView

    @login_user('Fred')
    def test_update(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_fred.config.root_path = svn_path
        request = self.DummyRequest()
        res = self.ClassView(request).update()
        expected = {'content': 'The repository has been updated!',
                    'editor_login': 'Fred',
                    'versioning': False}
        self.assertEqual(res, expected)


class TestPythonSvnView(SvnViewTester, BaseTestCase):
    ClassView = PythonSvnView

    @login_user('Fred')
    def test_update(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_fred.config.root_path = svn_path
        request = self.DummyRequest()
        res = self.ClassView(request).update()
        expected = {'content': '<pre>At revision 1.\n</pre>',
                    'editor_login': 'Fred',
                    'versioning': False}
        self.assertEqual(res, expected)


class FunctionalTestViewsNoVersioning(WaxeTestCase):

    def test_404(self):
        for url in [
            '/account/Bob/versioning/status',
            '/account/Bob/versioning/status.json',
            '/account/Bob/versioning/diff',
            '/account/Bob/versioning/diff.json',
            '/account/Bob/versioning/update',
            '/account/Bob/versioning/update.json',
            '/account/Bob/versioning/commit.json',
        ]:
            self.testapp.get(url, status=404)


class FunctionalTestViews(object):

    def test_forbidden(self):
        for url in [
            '/account/Bob/versioning/status',
            '/account/Bob/versioning/status.json',
            '/account/Bob/versioning/diff',
            '/account/Bob/versioning/diff.json',
            '/account/Bob/versioning/update',
            '/account/Bob/versioning/update.json',
            '/account/Bob/versioning/commit.json',
        ]:
            res = self.testapp.get(url, status=302)
            self.assertTrue('http://localhost/login?next=' in res.location)
            res = res.follow()
            self.assertEqual(res.status, "200 OK")
            self.assertTrue('<form' in res.body)
            self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_status(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/account/Bob/versioning/status', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)

    @login_user('Bob')
    def test_status_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/account/Bob/versioning/status.json', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_diff(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/account/Bob/versioning/diff', status=200)
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.get('/account/Bob/versioning/diff', status=200,
                               params={'filenames': 'file1.xml'})
        self.assertTrue('diff' in res.body)

    @login_user('Bob')
    def test_diff_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/account/Bob/versioning/diff.json', status=200)
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.get('/account/Bob/versioning/diff.json', status=200,
                               params={'filenames': 'file1.xml'})
        self.assertTrue('diff' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_commit_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path)
        res = self.testapp.get('/account/Bob/versioning/commit.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {"status": False, "error_msg": "Bad parameters!"}
        self.assertEqual(json.loads(res.body), expected)


# Uncomment this test when we will be able to choose the versioning backend!
# class FunctionalPysvnTestViews(FunctionalTestViews, WaxeTestCaseVersioning):
#     ClassView = PysvnView
# 
#     @login_user('Bob')
#     def test_update(self):
#         svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
#         self.user_bob.config = UserConfig(root_path=svn_path,
#                                           versioning_password='secret_bob')
#         res = self.testapp.get('/account/Bob/versioning/update', status=200)
#         self.assertTrue('The repository has been updated!' in res.body)
# 
#     @login_user('Bob')
#     def test_update_json(self):
#         svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
#         self.user_bob.config = UserConfig(root_path=svn_path,
#                                           versioning_password='secret_bob')
#         res = self.testapp.get('/account/Bob/versioning/update.json', status=200)
#         self.assertTrue('The repository has been updated!' in res.body)
#         self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
#                         res._headerlist)


class FunctionalPythonSvnTestViews(FunctionalTestViews, WaxeTestCaseVersioning):
    ClassView = PythonSvnView

    @login_user('Bob')
    def test_update(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path,
                                          versioning_password='secret_bob')
        res = self.testapp.get('/account/Bob/versioning/update', status=200)
        self.assertTrue('At revision 1.' in res.body)

    @login_user('Bob')
    def test_update_json(self):
        svn_path = os.path.join(os.getcwd(), 'waxe/tests/svn_client')
        self.user_bob.config = UserConfig(root_path=svn_path,
                                          versioning_password='secret_bob')
        res = self.testapp.get('/account/Bob/versioning/update.json', status=200)
        self.assertTrue('At revision 1.' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)


class TestHelper(unittest.TestCase):

    def setUp(self):
        directory = os.path.dirname(__file__)
        self.repo = os.path.join(directory, 'svn_waxe_repo')
        p = Popen('svnadmin create %s' % self.repo,
                  shell=True,
                  stderr=PIPE,
                  close_fds=True)
        error = p.stderr.read()
        if error:
            print >> sys.stderr,  error

        self.client_dir = 'svn_waxe_client'
        self.client = pysvn.Client()
        self.client.checkout('file://%s' % self.repo, self.client_dir)

    def tearDown(self):
        if os.path.isdir(self.repo):
            shutil.rmtree(self.repo)
        if os.path.isdir(self.client_dir):
            shutil.rmtree(self.client_dir)
        if os.path.isdir('svn_waxe_client1'):
            shutil.rmtree('svn_waxe_client1')

    def test_status(self):
        o = helper.PysvnVersioning(self.client, self.client_dir)
        self.assertEqual(o.status(), [])
        # Add new file
        file1 = os.path.join(self.client_dir, 'file1.xml')
        file2 = os.path.join(self.client_dir, 'file2.xml')
        file3 = os.path.join(self.client_dir, 'file3.xml')
        file4 = os.path.join(self.client_dir, 'file4.xml')
        file5 = os.path.join(self.client_dir, 'file5.xml')
        file6 = os.path.join(self.client_dir, 'file6.xml')
        file7 = os.path.join(self.client_dir, 'file7.xml')
        open(file1, 'w').write('Hello')
        open(file2, 'w').write('Hello')
        open(file3, 'w').write('Hello')
        open(file4, 'w').write('Hello')
        open(file5, 'w').write('Hello')
        open(file6, 'w').write('Hello')
        open(file7, 'w').write('Hello')
        self.client.add(file1)
        self.client.add(file2)
        self.client.add(file3)
        self.client.add(file4)
        self.client.add(file5)
        self.client.add(file6)
        self.client.checkin([file1, file2, file3, file4, file5], 'Initial commit')
        self.client.remove(file3)
        open(file2, 'w').write('Hello world')
        open(file5, 'w').write('Hello world')
        # Create a conflict
        self.client.checkout('file://%s' % self.repo, 'svn_waxe_client1')
        open(os.path.join('svn_waxe_client1', 'file5.xml'), 'w').write('Hello Bob')
        self.client.checkin([os.path.join('svn_waxe_client1', 'file5.xml')],
                            'create conflict')
        self.client.update(self.client_dir)
        os.remove(file4)
        expected = [
            helper.StatusObject('svn_waxe_client/file2.xml',
                                'file2.xml',
                                helper.STATUS_MODIFED),
            helper.StatusObject('svn_waxe_client/file3.xml',
                                'file3.xml',
                                helper.STATUS_DELETED),
            helper.StatusObject('svn_waxe_client/file4.xml',
                                'file4.xml',
                                helper.STATUS_MISSING),
            helper.StatusObject('svn_waxe_client/file5.xml',
                                'file5.xml',
                                helper.STATUS_CONFLICTED),
            helper.StatusObject('svn_waxe_client/file5.xml.mine',
                                'file5.xml.mine',
                                helper.STATUS_UNVERSIONED),
            helper.StatusObject('svn_waxe_client/file5.xml.r1',
                                'file5.xml.r1',
                                helper.STATUS_UNVERSIONED),
            helper.StatusObject('svn_waxe_client/file5.xml.r2',
                                'file5.xml.r2',
                                helper.STATUS_UNVERSIONED),
            helper.StatusObject('svn_waxe_client/file6.xml',
                                'file6.xml',
                                helper.STATUS_ADDED),
            helper.StatusObject('svn_waxe_client/file7.xml',
                                'file7.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.status(), expected)

        expected = [
            helper.StatusObject('svn_waxe_client/file7.xml',
                                'file7.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.status('file7.xml'), expected)

    def test_status_subfolder(self):
        o = helper.PysvnVersioning(self.client, self.client_dir)
        self.assertEqual(o.status(), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(self.client_dir, 'folder2')
        folder3 = os.path.join(self.client_dir, 'folder3')
        os.mkdir(folder1)
        os.mkdir(folder2)
        os.mkdir(folder3)
        file1 = os.path.join(folder1, 'file1.xml')
        file2 = os.path.join(folder2, 'file2.xml')
        open(file1, 'w').write('Hello')
        self.client.add(folder1)
        self.client.add(folder2)
        self.client.checkin([folder1, folder2], 'Add folders')
        open(file2, 'w').write('Hello')
        self.client.update(self.client_dir)
        expected = [
            helper.StatusObject('svn_waxe_client/folder2',
                                'folder2',
                                helper.STATUS_MODIFED),
            helper.StatusObject('svn_waxe_client/folder3',
                                'folder3',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.status(), expected)

        expected = [
            helper.StatusObject('svn_waxe_client/folder2/file2.xml',
                                'folder2/file2.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.status('folder2'), expected)

    def test_full_status(self):
        o = helper.PysvnVersioning(self.client, self.client_dir)
        self.assertEqual(o.full_status(), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        os.mkdir(folder1)
        self.assertEqual(o.full_status(), [])

        folder2 = os.path.join(self.client_dir, 'folder2')
        os.mkdir(folder2)
        self.assertEqual(o.full_status(), [])

        file2 = os.path.join(folder2, 'file2.xml')
        open(file2, 'w').write('Hello')
        expected = [
            helper.StatusObject('svn_waxe_client/folder2/file2.xml',
                                'folder2/file2.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.full_status(), expected)
        expected = [
            helper.StatusObject('svn_waxe_client/folder2/file2.xml',
                                'file2.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.full_status('folder2'), expected)

        expected = [
            helper.StatusObject('svn_waxe_client/folder2/file2.xml',
                                'folder2/file2.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.full_status('folder2/file2.xml'), expected)


class TestHelperNoRepo(unittest.TestCase):

    def setUp(self):
        self.client = EmptyClass()

    def test__status_short(self):
        directory = os.path.dirname(__file__)
        self.client_dir = os.path.join(directory, 'fake_repo')
        abspath = self.client_dir
        file1 = os.path.join(self.client_dir, 'file1.xml')
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(self.client_dir, 'folder2')
        changes = [
            FakeSvnStatus(self.client_dir, 'modified'),
            FakeSvnStatus(file1, 'added'),
            FakeSvnStatus(folder1, 'unversioned'),
            FakeSvnStatus(folder2, 'normal')
        ]

        o = helper.PysvnVersioning(self.client, self.client_dir)
        self.client.status = lambda *args, **kw: []
        res = o._status(abspath, changes)

        expected = [
            helper.StatusObject(folder1, 'folder1', helper.STATUS_UNVERSIONED),
            helper.StatusObject(file1, 'file1.xml', helper.STATUS_ADDED),
        ]

        self.assertEqual(res, expected)

        subchanges = [
            FakeSvnStatus(
                os.path.join(self.client_dir, 'folder2', 'sub21'),
                'unversioned'),
        ]

        o = helper.PysvnVersioning(self.client, self.client_dir)
        self.client.status = lambda *args, **kw: subchanges
        res = o._status(abspath, changes)
        expected = [
            helper.StatusObject(folder2, 'folder2', helper.STATUS_MODIFED),
            helper.StatusObject(folder1, 'folder1', helper.STATUS_UNVERSIONED),
            helper.StatusObject(file1, 'file1.xml', helper.STATUS_ADDED),
        ]

    def test__status_unversioned(self):
        directory = os.path.dirname(__file__)
        self.client_dir = os.path.join(directory, 'fake_repo')
        abspath = self.client_dir
        file1 = os.path.join(self.client_dir, 'file1.xml')
        folder1 = os.path.join(self.client_dir, 'folder1')
        file211 = os.path.join(self.client_dir, 'folder2', 'sub21',
                               'file211.xml')
        changes = [
            FakeSvnStatus(self.client_dir, 'unversioned'),
        ]

        o = helper.PysvnVersioning(self.client, self.client_dir)
        res = o._status(abspath, changes)
        self.assertEqual(res, [])

        res = o._status(abspath, changes, short=False)
        expected = [
            helper.StatusObject(file1, 'file1.xml', helper.STATUS_UNVERSIONED),
            helper.StatusObject(file211, 'folder2/sub21/file211.xml', helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(res, expected)

        changes = [
            FakeSvnStatus(folder1, 'unversioned'),
        ]
        res = o._status(folder1, changes, short=False)
        self.assertEqual(res, [])

        res = o._status(folder1, changes, short=True)
        self.assertEqual(res, [])
