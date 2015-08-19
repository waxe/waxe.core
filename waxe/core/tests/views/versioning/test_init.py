import os
import sys
import json
import unittest
import shutil
import difflib
from subprocess import Popen, PIPE
from pyramid import testing
from pyramid.exceptions import Forbidden
import pyramid.httpexceptions as exc
from webob.multidict import MultiDict
from mock import patch, MagicMock
import pysvn
from waxe.core.tests.testing import (
    WaxeTestCase,
    WaxeTestCaseVersioning,
    login_user,
    BaseTestCase,
)
from waxe.core import security
from waxe.core.models import (
    DBSession,
    User,
    UserConfig,
    VersioningPath,
    VERSIONING_PATH_STATUS_ALLOWED,
    VERSIONING_PATH_STATUS_FORBIDDEN,
)

from waxe.core.views.versioning.views import VersioningView
from waxe.core.views.versioning import helper


def fake_get_svn_username(*args, **kw):
    return 'my username'


class CreateRepo(unittest.TestCase):

    def setUp(self):
        super(CreateRepo, self).setUp()
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
        self.patcher1 = patch('waxe.core.views.versioning.helper.get_svn_client',
                              return_value=self.client)
        self.patcher1.start()
        self.patcher_versioning = patch(
            'waxe.core.views.base.BaseView.has_versioning', return_value=True)
        self.patcher_versioning.start()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher_versioning.stop()
        if os.path.isdir(self.repo):
            shutil.rmtree(self.repo)
        if os.path.isdir(self.client_dir):
            shutil.rmtree(self.client_dir)
        if os.path.isdir('svn_waxe_client1'):
            shutil.rmtree('svn_waxe_client1')
        super(CreateRepo, self).tearDown()


class FakeSvnStatus(object):

    def __init__(self, path, status):
        self.path = path
        self.text_status = getattr(pysvn.wc_status_kind, status)


class EmptyClass(object):
    pass


class CreateRepo2(unittest.TestCase):

    def setUp(self):
        super(CreateRepo2, self).setUp()
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

        file1 = os.path.join(self.client_dir, 'file1.xml')
        file2 = os.path.join(self.client_dir, 'file2.xml')
        file3 = os.path.join(self.client_dir, 'file3.xml')
        file4 = os.path.join(self.client_dir, 'file4.xml')
        folder1 = os.path.join(self.client_dir, 'folder1')
        os.mkdir(folder1)
        open(file1, 'w').write('Hello')
        open(file2, 'w').write('Hello')
        open(file3, 'w').write('Hello')
        open(file4, 'w').write('Hello')
        self.client.add(file1)
        self.client.add(file2)
        self.client.add(file4)
        self.client.add(folder1)
        self.client.checkin([file1, file2, folder1], 'Initial commit')
        open(file1, 'w').write('Hello world')
        self.patcher_versioning = patch(
            'waxe.core.views.base.BaseView.has_versioning', return_value=True)
        self.patcher_versioning.start()

    def tearDown(self):
        self.patcher_versioning.stop()
        if os.path.isdir(self.repo):
            shutil.rmtree(self.repo)
        if os.path.isdir(self.client_dir):
            shutil.rmtree(self.client_dir)
        super(CreateRepo2, self).tearDown()


class TestVersioningView(BaseTestCase, CreateRepo2):
    ClassView = VersioningView

    get_svn_client_str = ('waxe.core.views.versioning.'
                          'views.VersioningView.get_svn_client')

    def DummyRequest(self, *args, **kw):
        request = testing.DummyRequest(*args, **kw)
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'
        return request

    def setUp(self):
        super(TestVersioningView, self).setUp()
        self.config.registry.settings.update({
            'pyramid_auth.cookie.secret': 'scrt',
            'pyramid_auth.cookie.callback': ('waxe.core.security.'
                                             'get_user_permissions'),
            'pyramid_auth.cookie.validate_function': (
                'waxe.core.security.validate_password'),
        })
        self.config.include('pyramid_auth')

    @login_user('Bob')
    def test_get_svn_username(self):
        request = self.DummyRequest()
        self.user_bob.config = UserConfig(
            root_path='/root_path',
            use_versioning=True,
        )
        res = helper.get_svn_username(request, self.user_bob, self.user_bob,
                                      False)
        self.assertEqual(res, self.user_bob.login)

        func_str = '%s.fake_get_svn_username' % (
            fake_get_svn_username.__module__)

        request.registry.settings['waxe.versioning.get_svn_username'] = func_str
        res = helper.get_svn_username(request, self.user_bob, self.user_bob,
                                      False)
        self.assertEqual(res, fake_get_svn_username())

    def test_get_svn_login(self):
        request = self.DummyRequest()
        self.user_bob.config = UserConfig(
            root_path='/root_path',
            use_versioning=True,
        )
        res = helper.get_svn_login(request, self.user_bob, self.user_bob,
                                   False)
        expected = (False, 'Bob', None, False)
        self.assertEqual(res, expected)

        request.registry.settings['waxe.versioning.auth.active'] = True
        try:
            helper.get_svn_login(request, self.user_bob, self.user_bob, False)
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'No versioning password set for Bob')

        self.user_bob.config.versioning_password = 'secret_bob'
        res = helper.get_svn_login(request, self.user_bob, self.user_bob,
                                   False)
        expected = (True, 'Bob', 'secret_bob', False)
        self.assertEqual(res, expected)

        res = helper.get_svn_login(request, self.user_fred, self.user_fred,
                                   False)
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        res = helper.get_svn_login(request, self.user_fred, self.user_fred,
                                   False)
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['waxe.versioning.auth.pwd'] = 'secret'
        res = helper.get_svn_login(request, self.user_fred, self.user_fred,
                                   False)
        expected = (True, 'Fred', 'secret', False)
        self.assertEqual(res, expected)

        func_str = '%s.fake_get_svn_username' % (
            fake_get_svn_username.__module__)

        request.registry.settings['waxe.versioning.get_svn_username'] = func_str
        res = helper.get_svn_login(request, self.user_fred, self.user_fred,
                                   False)
        expected = (True, fake_get_svn_username(), 'secret', False)
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_short_status(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        res = self.ClassView(request).short_status()
        expected = {
            'file3.xml': helper.STATUS_UNVERSIONED,
            'file4.xml': helper.STATUS_ADDED,
            'file1.xml': helper.STATUS_MODIFED
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_status(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        res = self.ClassView(request).status()
        expected = {
            'uncommitables': [],
            'conflicteds': [],
            'others': [
                {
                    'status': 'modified',
                    'relpath': u'file1.xml'
                },
                {
                    'status': 'unversioned',
                    'relpath': u'file3.xml'
                },
                {
                    'status': 'added',
                    'relpath': u'file4.xml'
                }
            ]
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_diff(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        try:
            self.ClassView(request).diff()
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'No filename given')

        request = self.DummyRequest(params={'path': 'unexisting.xml'})
        try:
            self.ClassView(request).diff()
            assert(False)
        except exc.HTTPClientError, e:
            self.assertEqual(str(e), 'File unexisting.xml doesn\'t exist')

        request = self.DummyRequest(params={'path': 'file1.xml'})
        res = self.ClassView(request).diff()
        expected = (
            'Index: file1.xml\n'
            '===================================='
            '===============================\n'
            '--- file1.xml\t(revision 1)\n'
            '+++ file1.xml\t(working copy)\n'
            '@@ -1 +1 @@\n'
            '-Hello\n'
            '\ No newline at end of file\n'
            '+Hello world\n'
            '\ No newline at end of file\n'
        )
        self.assertTrue(expected in res['diff'])
        self.assertEqual(res['can_commit'], True)

        with patch('waxe.core.views.versioning.views.VersioningView.can_commit', return_value=False):
            res = self.ClassView(request).diff()
            self.assertTrue(expected in res['diff'])
            self.assertEqual(res['can_commit'], False)

        with patch('waxe.core.views.versioning.helper.PysvnVersioning.diff',
                   return_value=[]):
            res = self.ClassView(request).diff()
            self.assertEqual(res, {})

    @login_user('Bob')
    def test_revert(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        try:
            self.ClassView(request).revert()
        except exc.HTTPClientError, e:
            expected = 'No filename given'
            self.assertEqual(str(e), expected)

        request = self.DummyRequest()
        request.POST = MultiDict(path='nonexisting.xml')
        try:
            self.ClassView(request).revert()
        except exc.HTTPClientError, e:
            expected = 'File nonexisting.xml doesn\'t exist'
            self.assertEqual(str(e), expected)

        request = self.DummyRequest()
        request.POST = MultiDict(path='file1.xml')
        res = self.ClassView(request).revert()
        self.assertEqual(res, 'Files reverted')

    @login_user('Bob')
    def test_full_diff(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        request.GET = MultiDict()
        try:
            self.ClassView(request).full_diff()
            assert(False)
        except exc.HTTPClientError, e:
            expected = 'No filename given'
            self.assertEqual(str(e), expected)

        request = self.DummyRequest(root_path=self.client_dir,
                                    params={'filenames': 'file1.xml'})
        request.GET = MultiDict({'paths': 'file1.xml'})
        res = self.ClassView(request).full_diff()
        expected = {
            'can_commit': True,
            'diffs': [
                {
                    'right': u'Hello world',
                    'relpath': u'file1.xml',
                    'left': u'Hello'
                }
            ]
        }
        self.assertEqual(res, expected)

        request = self.DummyRequest(root_path=self.client_dir,
                                    params={'filenames': 'file3.xml'})
        request.GET = MultiDict({'paths': 'file3.xml'})
        res = self.ClassView(request).full_diff()
        expected = {
            'can_commit': True,
            'diffs': [
                {
                    'right': u'Hello',
                    'relpath': u'file3.xml',
                    'left': ''
                }
            ]
        }
        self.assertEqual(res, expected)

        request = self.DummyRequest(root_path=self.client_dir,
                                    params={'filenames': 'file3.xml'})
        request.GET = MultiDict({'paths': 'file3.xml'})
        self.user_bob.roles = [self.role_contributor]
        res = self.ClassView(request).full_diff()
        expected = {
            'can_commit': False,
            'diffs': [
                {
                    'right': u'Hello',
                    'relpath': u'file3.xml',
                    'left': u''
                }
            ]
        }
        self.assertEqual(res, expected)

        request.GET = MultiDict([('paths', 'file1.xml'),
                                 ('paths', 'file3.xml')])
        res = self.ClassView(request).full_diff()
        expected = {
            'can_commit': False,
            'diffs': [
                {
                    'right': u'Hello world',
                    'relpath': u'file1.xml',
                    'left': u'Hello'
                },
                {
                    'right': u'Hello',
                    'relpath': u'file3.xml',
                    'left': u''
                }
            ]
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_commit(self):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                self.user_bob.config.root_path = self.client_dir
                request = self.DummyRequest(root_path=self.client_dir)
                request.POST = MultiDict()
                try:
                    self.ClassView(request).commit()
                    assert(False)
                except exc.HTTPClientError, e:
                    expected = "No filename given"
                    self.assertEqual(str(e), expected)

                request = self.DummyRequest(root_path=self.client_dir)
                request.POST = MultiDict(paths='test.xml')
                try:
                    self.ClassView(request).commit()
                    assert(False)
                except exc.HTTPClientError, e:
                    expected = "No commit message"
                    self.assertEqual(str(e), expected)
                request.POST = MultiDict(paths='test.xml',
                                         msg='my commit message')

                with patch('waxe.core.views.versioning.helper.PysvnVersioning.commit', return_value=True):
                    self.assertEqual(len(self.user_bob.commited_files), 0)
                    res = self.ClassView(request).commit()
                    self.assertEqual(res, 'Files commited')
                    self.assertEqual(len(self.user_bob.commited_files), 1)
                    iduser_commit = self.user_bob.commited_files[0].iduser_commit
                    self.assertEqual(iduser_commit, None)

                with patch('waxe.core.views.versioning.helper.PysvnVersioning.commit', return_value=True):
                    view = self.ClassView(request)
                    view.current_user = self.user_fred
                    self.assertEqual(len(self.user_fred.commited_files), 0)
                    res = view.commit()
                    self.assertEqual(res, 'Files commited')
                    self.assertEqual(len(self.user_fred.commited_files), 0)
                    self.assertEqual(len(self.user_bob.commited_files), 2)
                    # New file is inserted first
                    iduser_commit = self.user_bob.commited_files[0].iduser_commit
                    self.assertEqual(iduser_commit, self.user_fred.iduser)

                with patch('waxe.core.views.versioning.helper.PysvnVersioning.commit', side_effect=Exception('Error')):
                    try:
                        self.ClassView(request).commit()
                        assert(False)
                    except exc.HTTPClientError, e:
                        expected = 'Commit failed: Error'
                        self.assertEqual(str(e), expected)

                with patch('waxe.core.views.versioning.views.VersioningView.can_commit', return_value=False):
                    try:
                        self.ClassView(request).commit()
                        assert(False)
                    except exc.HTTPClientError, e:
                        expected = (
                            'You don\'t have the permission '
                            'to commit: test.xml')
                        self.assertEqual(str(e), expected)

                # No permission
                self.user_bob.roles = []
                try:
                    res = self.ClassView(request).commit()
                    assert(False)
                except AssertionError, e:
                    self.assertEqual(str(e), 'You are not a contributor')

                self.user_bob.roles = [self.role_contributor]
                try:
                    res = self.ClassView(request).commit()
                except exc.HTTPClientError, e:
                    expected = (
                        'You don\'t have the permission '
                        'to commit: test.xml')
                    self.assertEqual(str(e), expected)

    def test_can_commit(self):
        user = User(login='user1', password='pass1')
        user.config = UserConfig(root_path='/root_path')
        DBSession.add(user)

        request = self.DummyRequest()

        user.roles = [self.role_admin]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', return_value=True):
                    view = self.ClassView(request)
                    res = view.can_commit('/home/test/myfile.xml')
                    self.assertEqual(res, True)

        user.roles = [self.role_editor]
        with patch('pyramid.authentication.'
                   'AuthTktAuthenticationPolicy.unauthenticated_userid',
                   return_value=user.login):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', return_value=True):
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
                                 'You are not a contributor')

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


class TestVersioningViewFakeRepo(BaseTestCase, CreateRepo):

    def setUp(self):
        super(TestVersioningViewFakeRepo, self).setUp()
        self.config.registry.settings.update({
            'pyramid_auth.no_routes': 'true',
            'pyramid_auth.cookie.secret': 'scrt',
            'pyramid_auth.cookie.callback': ('waxe.core.security.'
                                             'get_user_permissions'),
            'pyramid_auth.cookie.validate_function': (
                'waxe.core.security.validate_password'),
        })
        self.config.include('pyramid_auth')

    @login_user('Fred')
    def test_update(self):
        self.user_bob.config.root_path = self.client_dir
        file1 = os.path.join(self.client_dir, 'file1.xml')
        open(file1, 'w').write('Hello')
        self.client.add(file1)
        self.client.checkin([file1], 'Initial commit')
        open(file1, 'w').write('Hello Fred')

        self.user_fred.config.root_path = self.client_dir
        self.user_fred.roles = [self.role_contributor]
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        request.matched_route = EmptyClass()
        request.matched_route.name = 'route'

        res = VersioningView(request).update()
        self.assertEqual(res, [])

        # Create a conflict
        self.client.checkout('file://%s' % self.repo, 'svn_waxe_client1')
        open(os.path.join('svn_waxe_client1', 'file1.xml'), 'w').write('Hello Bob')
        self.client.checkin([os.path.join('svn_waxe_client1', 'file1.xml')],
                            'create conflict')
        self.client.update(self.client_dir)

        try:
            VersioningView(request).update()
            assert(False)
        except exc.HTTPClientError, e:
            expected = ('You can\'t update the repository, '
                        'you have to fix the conflicts first')
            self.assertEqual(str(e), expected)

        self.client.revert(os.path.join(self.client_dir, 'file1.xml'))

        # Update add
        client1file = os.path.join('svn_waxe_client1', 'client1file.xml')
        open(client1file, 'w').write('Hello Bob')
        self.client.add(client1file)
        self.client.checkin([client1file], 'New file')
        res = VersioningView(request).update()
        expected = [
            {'status': 'added', 'path': 'client1file.xml', 'addLink': True}
        ]
        self.assertEqual(res, expected)

        # Update modify
        open(client1file, 'w').write('Hello Bob content')
        self.client.checkin([client1file], 'Update file')
        res = VersioningView(request).update()
        expected = [
            {'status': 'modified', 'path': 'client1file.xml', 'addLink': True}
        ]
        self.assertEqual(res, expected)

        # Update delete
        self.client.remove(client1file)
        self.client.checkin([client1file], 'Delete file')
        res = VersioningView(request).update()
        expected = [
            {'status': 'deleted', 'path': 'client1file.xml', 'addLink': False}
        ]
        self.assertEqual(res, expected)


class FunctionalTestViewsNoVersioning(WaxeTestCase):

    def test_404(self):
        for url in [
            '/api/1/account/Bob/versioning/status.json',
            '/api/1/account/Bob/versioning/full-diff.json',
            '/api/1/account/Bob/versioning/update.json',
            '/api/1/account/Bob/versioning/commit.json',
        ]:
            self.testapp.get(url, status=404)


class FunctionalPysvnTestViews(WaxeTestCaseVersioning, CreateRepo2):
    ClassView = VersioningView

    def test_forbidden(self):
        for url in [
            '/api/1/account/Bob/versioning/status.json',
            '/api/1/account/Bob/versioning/full-diff.json',
            '/api/1/account/Bob/versioning/update.json',
            '/api/1/account/Bob/versioning/commit.json',
        ]:
            self.testapp.get(url, status=401)

    @login_user('Bob')
    def test_short_status_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/api/1/account/Bob/versioning/short-status.json',
                               status=200)
        expected = {
            'file3.xml': helper.STATUS_UNVERSIONED,
            'file4.xml': helper.STATUS_ADDED,
            'file1.xml': helper.STATUS_MODIFED
        }
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_status_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/api/1/account/Bob/versioning/status.json', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_full_diff_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/api/1/account/Bob/versioning/full-diff.json',
                               status=400)
        self.assertEqual(res.body,
                         '"No filename given"')

        res = self.testapp.post('/api/1/account/Bob/versioning/full-diff.json',
                                status=400)
        self.assertEqual(res.body,
                         '"No filename given"')

        res = self.testapp.get('/api/1/account/Bob/versioning/full-diff.json', status=200,
                               params={'paths': 'file1.xml'})
        self.assertTrue('diff' in res.body)

    @login_user('Bob')
    def test_commit_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.post('/api/1/account/Bob/versioning/commit.json',
                                status=400)
        self.assertEqual(res.body, '"No filename given"')

    @login_user('Bob')
    def test_update_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir,
                                          versioning_password='secret_bob')
        res = self.testapp.get('/api/1/account/Bob/versioning/update.json', status=200)
        self.assertEqual(json.loads(res.body), [])


class TestHelper(CreateRepo):

    def test_empty_status(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                   False)
        expected = helper.StatusObject(self.client_dir, '.',
                                       helper.STATUS_NORMAL)
        self.assertEqual(o.empty_status(self.client_dir), expected)
        folder1 = os.path.join(self.client_dir, 'folder1')
        os.mkdir(folder1)
        file1 = os.path.join(folder1, 'file1.xml')
        open(file1, 'w').write('Hello')

        expected = helper.StatusObject(file1,
                                       'folder1/file1.xml',
                                       helper.STATUS_UNVERSIONED)
        self.assertEqual(o.empty_status(file1), expected)

        expected = helper.StatusObject(folder1,
                                       'folder1',
                                       helper.STATUS_UNVERSIONED)
        self.assertEqual(o.empty_status(folder1), expected)

        self.client.add(folder1, depth=pysvn.depth.empty)
        expected = helper.StatusObject(folder1,
                                       'folder1',
                                       helper.STATUS_ADDED)
        self.assertEqual(o.empty_status(folder1), expected)

        expected = helper.StatusObject(file1,
                                       'folder1/file1.xml',
                                       helper.STATUS_UNVERSIONED)
        self.assertEqual(o.empty_status(file1), expected)
        self.client.checkin(folder1, 'commit folder')
        self.client.update(self.client_dir)

        expected = helper.StatusObject(folder1,
                                       'folder1',
                                       helper.STATUS_NORMAL)
        self.assertEqual(o.empty_status(folder1), expected)

        expected = helper.StatusObject(file1,
                                       'folder1/file1.xml',
                                       helper.STATUS_UNVERSIONED)
        self.assertEqual(o.empty_status(file1), expected)

    def test_status(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None,
                                   self.client_dir, False)
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
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                   False)
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
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
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
                                'folder2/file2.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.full_status('folder2'), expected)

        expected = [
            helper.StatusObject('svn_waxe_client/folder2/file2.xml',
                                'folder2/file2.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.full_status('folder2/file2.xml'), expected)

    def test_update(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        file1 = os.path.join(self.client_dir, 'file1.xml')
        self.assertFalse(os.path.isfile(file1))
        self.client.checkout('file://%s' % self.repo, 'svn_waxe_client1')
        rfile1 = os.path.join('svn_waxe_client1', 'file1.xml')
        open(rfile1, 'w').write('Hello Bob')
        self.client.add(rfile1)
        self.client.checkin(rfile1, 'Commit file')
        o.update()
        self.assertTrue(os.path.isfile(file1))

    def test_diff(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.diff(), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(folder1, 'folder2')
        os.mkdir(folder1)
        os.mkdir(folder2)
        file1 = os.path.join(folder1, 'file1.xml')
        file2 = os.path.join(folder2, 'file2.xml')
        open(file1, 'w').write('Hello')
        self.client.add(folder1)
        self.client.checkin([folder1], 'Add folder')
        open(file1, 'w').write('Hello World')
        res = o.diff('folder1/file1.xml')
        self.assertEqual(len(res), 1)
        self.assertTrue('-Hello' in res[0])
        self.assertTrue('+Hello World' in res[0])

        res1 = o.diff()
        self.assertEqual(res, res1)

        # Unversioned files are not taken into account
        open(file2, 'w').write('Hello')
        res2 = o.diff()
        self.assertEqual(res[0], res2[0])
        self.assertTrue('New file folder1/folder2/file2.xml' in res2[1])

        res3 = o.diff('folder1/folder2/file2.xml')
        self.assertEqual(res3[0], res2[1])

        self.client.add(file2)
        res = o.diff()
        self.assertEqual(len(res), 2)
        self.assertTrue('-Hello' in res[0])
        self.assertTrue('+Hello World' in res[0])
        self.assertTrue('New file ' in res[1])

        self.client.revert(file1)
        self.client.remove(file1)
        res = o.diff()
        self.assertEqual(len(res), 2)
        self.assertTrue('Deleted file ' in res[0])
        self.assertTrue('New file ' in res[1])

    def test_full_diff_content(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.full_diff_content(), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(folder1, 'folder2')
        os.mkdir(folder1)
        os.mkdir(folder2)
        file1 = os.path.join(folder1, 'file1.xml')
        file2 = os.path.join(folder2, 'file2.xml')
        open(file1, 'w').write('Hello')
        self.client.add(folder1)
        self.client.checkin([folder1], 'Add folder')
        open(file1, 'w').write('Hello World')
        res = o.full_diff_content('folder1/file1.xml')
        self.assertEqual(len(res), 1)
        expected = [
            {
                'right': u'Hello World',
                'relpath': u'folder1/file1.xml',
                'left': u'Hello'
            }
        ]
        self.assertEqual(res, expected)

        # Unversioned files are not taken into account
        open(file2, 'w').write('Hello')
        res2 = o.full_diff_content()
        expected = [
            {
                'right': u'Hello World',
                'relpath': u'folder1/file1.xml',
                'left': u'Hello'
            },
            {
                'right': u'Hello',
                'relpath': u'folder1/folder2/file2.xml',
                'left': u''
            }
        ]
        self.assertEqual(res2, expected)

        res3 = o.full_diff_content('folder1/folder2/file2.xml')
        expected = [
            {
                'right': u'Hello',
                'relpath': u'folder1/folder2/file2.xml',
                'left': u''
            }
        ]
        self.assertEqual(res3, expected)

        self.client.add(file2)
        res = o.full_diff_content()
        expected = [
            {
                'right': u'Hello World',
                'relpath': u'folder1/file1.xml',
                'left': u'Hello'
            },
            {
                'right': u'Hello',
                'relpath': u'folder1/folder2/file2.xml',
                'left': u''
            }
        ]
        self.assertEqual(res, expected)

        self.client.revert(file1)
        self.client.remove(file1)
        res = o.full_diff_content()
        expected = [
            {
                'right': u'',
                'relpath': u'folder1/file1.xml',
                'left': u'Hello'
            },
            {
                'right': u'Hello',
                'relpath': u'folder1/folder2/file2.xml',
                'left': u''
            }
        ]
        self.assertEqual(res, expected)

    def test_get_commitable_files(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.get_commitable_files(), [])
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
            # NOTE: we don't have the conflicted files in the list
            # helper.StatusObject('svn_waxe_client/file5.xml',
            #                     'file5.xml',
            #                     helper.STATUS_CONFLICTED),
            # helper.StatusObject('svn_waxe_client/file5.xml.mine',
            #                     'file5.xml.mine',
            #                     helper.STATUS_UNVERSIONED),
            # helper.StatusObject('svn_waxe_client/file5.xml.r1',
            #                     'file5.xml.r1',
            #                     helper.STATUS_UNVERSIONED),
            # helper.StatusObject('svn_waxe_client/file5.xml.r2',
            #                     'file5.xml.r2',
            #                     helper.STATUS_UNVERSIONED),
            helper.StatusObject('svn_waxe_client/file6.xml',
                                'file6.xml',
                                helper.STATUS_ADDED),
            helper.StatusObject('svn_waxe_client/file7.xml',
                                'file7.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.get_commitable_files(), expected)

        expected = [
            helper.StatusObject('svn_waxe_client/file7.xml',
                                'file7.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(o.get_commitable_files('file7.xml'), expected)

    def test_unversioned_parents(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.unversioned_parents(self.client_dir), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(self.client_dir, 'folder2')
        subfolder21 = os.path.join(folder2, 'sub21')
        os.mkdir(folder1)
        os.mkdir(folder2)
        os.mkdir(subfolder21)
        file1 = os.path.join(folder1, 'file1.xml')
        file2 = os.path.join(subfolder21, 'file2.xml')
        file3 = os.path.join(self.client_dir, 'file3.xml')
        open(file1, 'w').write('Hello')
        open(file2, 'w').write('Hello')
        open(file3, 'w').write('Hello')
        self.assertEqual(list(o.unversioned_parents(file3)), [])

        self.assertEqual(list(o.unversioned_parents(file1)), [folder1])
        self.assertEqual(list(o.unversioned_parents(file2)), [folder2,
                                                              subfolder21])
        self.client.add(folder2, depth=pysvn.depth.empty)
        self.assertEqual(list(o.unversioned_parents(file2)), [subfolder21])

        self.client.add(subfolder21, depth=pysvn.depth.empty)
        self.assertEqual(list(o.unversioned_parents(file2)), [])

    def test_add(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.unversioned_parents(self.client_dir), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(self.client_dir, 'folder2')
        subfolder21 = os.path.join(folder2, 'sub21')
        os.mkdir(folder1)
        os.mkdir(folder2)
        os.mkdir(subfolder21)
        file1 = os.path.join(folder1, 'file1.xml')
        file2 = os.path.join(subfolder21, 'file2.xml')
        file3 = os.path.join(self.client_dir, 'file3.xml')
        open(file1, 'w').write('Hello')
        open(file2, 'w').write('Hello')
        open(file3, 'w').write('Hello')

        files = ['folder1/file1.xml',
                 'folder2/sub21/file2.xml',
                 'file3.xml']
        res = o.add(files)
        for f in [folder1, folder2, subfolder21, file1, file2, file3]:
            so = o.empty_status(f)
            self.assertEqual(so.status, helper.STATUS_ADDED)
        self.assertEqual(
            res, [folder1, file1, folder2, subfolder21, file2, file3])

        # Just to make sure we can call with one file and it will not fail if
        # the file is already added
        res = o.add('file3.xml')
        self.assertEqual(res, [])

        # Fail if file doesn't exist
        res = o.add('unexisting.xml')
        self.assertEqual(res, [])

    def test_commit(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.unversioned_parents(self.client_dir), [])
        folder1 = os.path.join(self.client_dir, 'folder1')
        folder2 = os.path.join(self.client_dir, 'folder2')
        subfolder21 = os.path.join(folder2, 'sub21')
        os.mkdir(folder1)
        os.mkdir(folder2)
        os.mkdir(subfolder21)
        file1 = os.path.join(folder1, 'file1.xml')
        file2 = os.path.join(subfolder21, 'file2.xml')
        file3 = os.path.join(self.client_dir, 'file3.xml')
        file4 = os.path.join(subfolder21, 'file4.xml')
        open(file1, 'w').write('Hello')
        open(file2, 'w').write('Hello')
        open(file3, 'w').write('Hello')
        open(file4, 'w').write('Hello')

        files = ['folder1/file1.xml',
                 'folder2/sub21/file2.xml',
                 'file3.xml']
        o.commit(files, 'Test commit')
        self.client.update(self.client_dir)
        for f in [folder1, folder2, subfolder21, file1, file2, file3]:
            so = o.empty_status(f)
            self.assertEqual(so.status, helper.STATUS_NORMAL)
        res = o.empty_status(file4)
        self.assertEqual(res.status, helper.STATUS_UNVERSIONED)

    def test_resolve(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                   False)
        self.assertEqual(o.get_commitable_files(), [])
        file1 = os.path.join(self.client_dir, 'file1.xml')
        open(file1, 'w').write('Hello')
        self.client.add(file1)
        self.client.checkin([file1], 'Initial commit')
        # Create a conflict
        self.client.checkout('file://%s' % self.repo, 'svn_waxe_client1')
        open(os.path.join('svn_waxe_client1', 'file1.xml'), 'w').write('Hello Bob')
        self.client.checkin([os.path.join('svn_waxe_client1', 'file1.xml')],
                            'create conflict')
        open(file1, 'w').write('Hello Fred')
        self.client.update(self.client_dir)
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_CONFLICTED)

        o.resolve('file1.xml')
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_MODIFED)

    def test_revert(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.get_commitable_files(), [])
        file1 = os.path.join(self.client_dir, 'file1.xml')
        open(file1, 'w').write('Hello')
        self.client.add(file1)
        self.client.checkin([file1], 'Initial commit')
        open(file1, 'w').write('Hello Fred')
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_MODIFED)
        o.revert('file1.xml')
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_NORMAL)

        # Revert not modified file
        o.revert('file1.xml')
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_NORMAL)

        # Revert not versionned file
        new_file = os.path.join(self.client_dir, 'new-file.xml')
        open(new_file, 'w').write('Hello')
        s = o.empty_status(new_file)
        self.assertEqual(s.status, helper.STATUS_UNVERSIONED)
        o.revert('new-file.xml')
        s = o.empty_status(new_file)
        self.assertEqual(s.status, helper.STATUS_UNVERSIONED)

        s = o.add('new-file.xml')
        s = o.empty_status(new_file)
        self.assertEqual(s.status, helper.STATUS_ADDED)
        o.revert('new-file.xml')
        s = o.empty_status(new_file)
        self.assertEqual(s.status, helper.STATUS_UNVERSIONED)

    def test_remove(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.get_commitable_files(), [])
        file1 = os.path.join(self.client_dir, 'file1.xml')
        open(file1, 'w').write('Hello')
        self.client.add(file1)
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_ADDED)

        o.remove('file1.xml')
        self.assertFalse(os.path.exists(file1))
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_NORMAL)

        open(file1, 'w').write('Hello')
        self.client.add(file1)
        self.client.checkin([file1], 'Initial commit')
        open(file1, 'w').write('Hello Fred')
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_MODIFED)
        o.remove('file1.xml')
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_DELETED)

        # Remove not modified file
        o.remove('file1.xml')
        s = o.empty_status(file1)
        self.assertFalse(os.path.exists(file1))
        self.assertEqual(s.status, helper.STATUS_DELETED)

        # Remove not versionned file
        new_file = os.path.join(self.client_dir, 'new-file.xml')
        open(new_file, 'w').write('Hello')
        s = o.empty_status(new_file)
        self.assertEqual(s.status, helper.STATUS_UNVERSIONED)
        o.remove('new-file.xml')
        s = o.empty_status(new_file)
        self.assertFalse(os.path.exists(file1))
        self.assertEqual(s.status, helper.STATUS_NORMAL)

    def test_has_conflict(self):
        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        self.assertEqual(o.get_commitable_files(), [])
        file1 = os.path.join(self.client_dir, 'file1.xml')
        open(file1, 'w').write('Hello')
        self.client.add(file1)
        self.client.checkin([file1], 'Initial commit')
        self.assertEqual(o.has_conflict(), False)

        # Create a conflict
        self.client.checkout('file://%s' % self.repo, 'svn_waxe_client1')
        open(os.path.join('svn_waxe_client1', 'file1.xml'), 'w').write('Hello Bob')
        self.client.checkin([os.path.join('svn_waxe_client1', 'file1.xml')],
                            'create conflict')
        open(file1, 'w').write('Hello Fred')
        self.client.update(self.client_dir)
        self.assertEqual(o.has_conflict(), True)


class TestHelperNoRepo(unittest.TestCase):

    def setUp(self):
        self.client = EmptyClass()
        self.patcher1 = patch('waxe.core.views.versioning.helper.get_svn_client',
                              return_value=self.client)
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()
        super(TestHelperNoRepo, self).tearDown()

    def test_is_conflicted(self):
        lis = []
        so = helper.StatusObject('svn_waxe_client/file5.xml.mine',
                                 'file5.xml.mine',
                                 helper.STATUS_UNVERSIONED)
        res = helper.is_conflicted(so, lis)
        self.assertEqual(res, False)

        lis = ['svn_waxe_client/file5.xml']
        res = helper.is_conflicted(so, lis)
        self.assertEqual(res, True)

        so = helper.StatusObject('svn_waxe_client/file5.xml.plop',
                                 'file5.xml.mine',
                                 helper.STATUS_UNVERSIONED)
        res = helper.is_conflicted(so, lis)
        self.assertEqual(res, False)

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

        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
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

        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
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
        sub11 = os.path.join(folder1, 'sub11')
        folder2 = os.path.join(self.client_dir, 'folder2')
        file211 = os.path.join(folder2,  'sub21', 'file211.xml')
        changes = [
            FakeSvnStatus(self.client_dir, 'unversioned'),
        ]

        o = helper.PysvnVersioning(None, ['.xml'], None, None, self.client_dir,
                                  False)
        res = o._status(abspath, changes)
        expected = [
            helper.StatusObject(folder1, 'folder1', helper.STATUS_UNVERSIONED),
            helper.StatusObject(folder2, 'folder2', helper.STATUS_UNVERSIONED),
            helper.StatusObject(file1, 'file1.xml', helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(res, expected)

        res = o._status(abspath, changes, short=False)
        expected = [
            helper.StatusObject(file1, 'file1.xml', helper.STATUS_UNVERSIONED),
            helper.StatusObject(file211, 'folder2/sub21/file211.xml',
                                helper.STATUS_UNVERSIONED),
        ]
        self.assertEqual(res, expected)

        changes = [
            FakeSvnStatus(folder1, 'unversioned'),
        ]
        res = o._status(folder1, changes, short=False)
        self.assertEqual(res, [])

        expected = [
            helper.StatusObject(sub11, 'folder1/sub11',
                                helper.STATUS_UNVERSIONED),
        ]
        res = o._status(folder1, changes, short=True)
        self.assertEqual(res, expected)
