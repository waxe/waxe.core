import os
import sys
import json
import unittest
import shutil
import difflib
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

from waxe.views.versioning.views import VersioningView
from waxe.views.versioning import helper


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
        self.patcher1 = patch('waxe.views.versioning.helper.get_svn_client',
                              return_value=self.client)
        self.patcher1.start()
        self.patcher_versioning = patch(
            'waxe.views.base.BaseView.has_versioning', return_value=True)
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
            'waxe.views.base.BaseView.has_versioning', return_value=True)
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

    get_svn_client_str = ('waxe.views.versioning.'
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
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.security.'
                                               'get_user_permissions')
        })
        self.config.include('pyramid_auth')

    @login_user('Bob')
    def test_get_svn_login(self):
        request = self.DummyRequest()
        self.user_bob.config = UserConfig(
            root_path='/root_path',
            use_versioning=True,
        )
        view = self.ClassView(request)

        res = helper.get_svn_login(request, self.user_bob)
        expected = (False, 'Bob', None, False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.active'] = True
        try:
            helper.get_svn_login(request, self.user_bob)
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'No versioning password set for Bob')

        self.user_bob.config.versioning_password = 'secret_bob'
        res = helper.get_svn_login(request, self.user_bob)
        expected = (True, 'Bob', 'secret_bob', False)
        self.assertEqual(res, expected)

        view = self.ClassView(request)
        view.current_user = self.user_fred
        res = helper.get_svn_login(request, self.user_fred)
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        view = self.ClassView(request)
        view.current_user = self.user_fred
        res = helper.get_svn_login(request, self.user_fred)
        expected = (True, 'Fred', 'secret_fred', False)
        self.assertEqual(res, expected)

        request.registry.settings['versioning.auth.pwd'] = 'secret'
        view = self.ClassView(request)
        view.current_user = self.user_fred
        res = helper.get_svn_login(request, self.user_fred)
        expected = (True, 'Fred', 'secret', False)
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
        self.assertTrue('file1.xml' in res['content'])
        self.assertTrue('file3.xml' in res['content'])
        self.assertTrue('file4.xml' in res['content'])
        self.assertTrue('value="Generate diff"' in res['content'])
        self.assertTrue('value="Commit"' in res['content'])

    @login_user('Bob')
    def test_diff(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        res = self.ClassView(request).diff()
        expected = 'No filename given'
        self.assertEqual(res['error_msg'], expected)

        request = self.DummyRequest(params={'path': 'unexisting.xml'})
        res = self.ClassView(request).diff()
        expected = 'File unexisting.xml doesn\'t exist'
        self.assertEqual(res['error_msg'], expected)

        request = self.DummyRequest(params={'path': 'file1.xml'})
        res = self.ClassView(request).diff()
        content = res['content']
        expected = (
            '<pre>Index: file1.xml\n'
            '===================================='
            '===============================\n'
            '--- file1.xml\t(revision 1)\n'
            '+++ file1.xml\t(working copy)\n'
            '@@ -1 +1 @@\n'
            '-Hello\n'
            '\ No newline at end of file\n'
            '+Hello world\n'
            '\ No newline at end of file\n'
            '</pre>'
        )
        self.assertTrue(expected in content)
        self.assertTrue('data-href="/versioning_prepare_commit_json"'
                        in content)
        self.assertTrue('data-href="/versioning_revert_json"'
                        in content)

        with patch('waxe.views.versioning.views.VersioningView.can_commit', return_value=False):
            res = self.ClassView(request).diff()
            content = res['content']
            self.assertTrue(expected in content)
            self.assertFalse('data-href="/versioning_prepare_commit_json"'
                             in content)
            self.assertTrue('data-href="/versioning_revert_json"'
                            in content)

        with patch('waxe.views.versioning.helper.PysvnVersioning.diff',
                   return_value=[]):
            res = self.ClassView(request).diff()
            self.assertTrue('The file is not modified!' in res['content'])

    @login_user('Bob')
    def test_revert(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        res = self.ClassView(request).revert()
        expected = {'error_msg': 'No filename given'}
        self.assertEqual(res, expected)

        request = self.DummyRequest(params={'path': 'nonexisting.xml'})
        res = self.ClassView(request).revert()
        expected = 'File nonexisting.xml doesn\'t exist'
        self.assertEqual(res['error_msg'], expected)

        request = self.DummyRequest(params={'path': 'file1.xml'})
        res = self.ClassView(request).revert()
        expected = {
            'info_msg': 'The modification has been reverted!',
            'redirect_url': '/edit_json',
        }
        self.assertEqual(res, expected)

    @login_user('Bob')
    def test_full_diff(self):
        self.user_bob.config.root_path = self.client_dir
        request = self.DummyRequest()
        request.POST = MultiDict()
        res = self.ClassView(request).full_diff()
        expected = 'You should provide at least one filename.'
        self.assertEqual(res['error_msg'], expected)

        request = self.DummyRequest(root_path=self.client_dir,
                                    params={'filenames': 'file1.xml'})
        request.POST = MultiDict({'filenames': 'file1.xml'})
        res = self.ClassView(request).full_diff()
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])
        self.assertTrue('name="commit" ' in res['content'])

        request = self.DummyRequest(root_path=self.client_dir,
                                    params={'filenames': 'file3.xml'})
        request.POST = MultiDict({'filenames': 'file3.xml'})
        res = self.ClassView(request).full_diff()
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])
        self.assertTrue('name="commit" ' in res['content'])

        request = self.DummyRequest(root_path=self.client_dir,
                                    params={'filenames': 'file3.xml'})
        request.POST = MultiDict({'filenames': 'file3.xml'})
        self.user_bob.roles = [self.role_contributor]
        res = self.ClassView(request).full_diff()
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 1)
        self.assertTrue('submit' in res['content'])
        self.assertTrue('name="commit" ' not in res['content'])

        request.POST = MultiDict([('filenames', 'file1.xml'),
                                 ('filenames', 'file3.xml')])
        res = self.ClassView(request).full_diff()
        self.assertTrue('class="diff"' in res['content'])
        self.assertEqual(res['content'].count('diff_from'), 2)
        self.assertTrue('submit' in res['content'])
        self.assertTrue('name="commit" ' not in res['content'])

        # We should call prepare_commit
        request.POST = MultiDict([('filenames', 'file1.xml'),
                                 ('filenames', 'file3.xml'),
                                 ('submit', 'Commit')])
        res = self.ClassView(request).full_diff()
        self.assertTrue('Choose the files you want to commit' in res['modal'])

    @login_user('Bob')
    def test_commit(self):
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                self.user_bob.config.root_path = self.client_dir
                request = self.DummyRequest(root_path=self.client_dir)
                request.POST = MultiDict()
                res = self.ClassView(request).commit()
                expected = "No file selected!"
                self.assertEqual(res['error_msg'], expected)

                request = self.DummyRequest(root_path=self.client_dir)
                request.POST = MultiDict(path='test.xml')
                res = self.ClassView(request).commit()
                expected = "No commit message!"
                self.assertEqual(res['error_msg'], expected)
                request.POST = MultiDict(path='test.xml',
                                         msg='my commit message')

                with patch('waxe.views.versioning.helper.PysvnVersioning.commit', return_value=True):
                    self.assertEqual(len(self.user_bob.commited_files), 0)
                    res = self.ClassView(request).commit()
                    self.assertEqual(res, self.ClassView(request).status())
                    self.assertEqual(len(self.user_bob.commited_files), 1)
                    iduser_commit = self.user_bob.commited_files[0].iduser_commit
                    self.assertEqual(iduser_commit, None)

                with patch('waxe.views.versioning.helper.PysvnVersioning.commit', return_value=True):
                    view = self.ClassView(request)
                    view.current_user = self.user_fred
                    self.assertEqual(len(self.user_fred.commited_files), 0)
                    res = view.commit()
                    self.assertEqual(res, view.status())
                    self.assertEqual(len(self.user_fred.commited_files), 1)
                    iduser_commit = self.user_fred.commited_files[0].iduser_commit
                    self.assertEqual(iduser_commit, self.user_bob.iduser)

                with patch('waxe.views.versioning.helper.PysvnVersioning.commit', side_effect=Exception('Error')):
                    res = self.ClassView(request).commit()
                    expected = 'Error during the commit Error'
                    self.assertEqual(res['error_msg'], expected)

                with patch('waxe.views.versioning.views.VersioningView.can_commit', return_value=False):
                    res = self.ClassView(request).commit()
                    expected = (
                        'You don\'t have the permission '
                        'to commit: test.xml')
                    self.assertEqual(res['error_msg'], expected)

                # No permission
                self.user_bob.roles = []
                try:
                    res = self.ClassView(request).commit()
                    assert(False)
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
                                 'Invalid path /home/test/folder1/myfile.xml')

            with patch('os.path.exists', return_value=True):
                with patch('os.path.isfile', return_value=True):
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

    @login_user('Bob')
    def test_prepare_commit(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = self.DummyRequest(params={})
        res = self.ClassView(request).prepare_commit()
        expected = 'No file to commit in /'
        self.assertEqual(res['info_msg'], expected)

        self.user_bob.config.root_path = self.client_dir
        res = self.ClassView(request).prepare_commit()
        self.assertTrue('data-action="/versioning_commit_json"'
                        in res['modal'])
        expected = (
            '<label>'
            '<input type="checkbox" checked="checked" '
            'name="path" value="file1.xml"/>file1.xml</label>')
        self.assertTrue(expected in res['modal'])

    @login_user('Bob')
    def test_update_texts(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        request = self.DummyRequest(params={})
        res = self.ClassView(request).update_texts()
        expected = 'Missing parameters!'
        self.assertEqual(res['error_msg'], expected)

        request = self.DummyRequest(
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
            res = self.ClassView(request).update_texts()
            expected = (
                'thefilename1.xml: My error<br />'
                'thefilename2.xml: My error')
            self.assertEqual(res['error_msg'],  expected)

        filecontent = open(os.path.join(path, 'file1.xml'), 'r').read()
        filecontent = filecontent.replace('exercise.dtd',
                                          os.path.join(path, 'exercise.dtd'))
        request = self.DummyRequest(
            params={'data:0:filecontent': filecontent,
                    'data:0:filename': 'thefilename.xml'})
        request.custom_route_path = lambda *args, **kw: '/filepath'

        with patch('xmltool.elements.Element.write', return_value=None):
            res = self.ClassView(request).update_texts()
            expected = 'Files updated'
            self.assertEqual(res['content'],  expected)

            request.params['commit'] = True
            res = self.ClassView(request).update_texts()
            self.assertTrue('breadcrumb' in res)
            self.assertEqual(res['versioning'], True)
            self.assertEqual(res['editor_login'], 'Bob')
            self.assertTrue('class="modal' in res['modal'])
            self.assertTrue('commit message' in res['modal'])


class TestVersioningViewFakeRepo(BaseTestCase, CreateRepo):

    def setUp(self):
        super(TestVersioningViewFakeRepo, self).setUp()
        self.config.registry.settings.update({
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.security.'
                                               'get_user_permissions')
        })
        self.config.include('pyramid_auth')

    @login_user('Bob')
    def test_edit_conflict(self):
        class C(object): pass
        self.user_bob.config.root_path = self.client_dir
        file1 = os.path.join(self.client_dir, 'file1.xml')
        open(file1, 'w').write('Hello')
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.matched_route = C()
        request.matched_route.name = 'route'
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        expected = 'A filename should be provided'
        res = VersioningView(request).edit_conflict()
        self.assertEqual(res['error_msg'], expected)

        request = testing.DummyRequest(params={'path': 'file1.xml'})
        request.matched_route = C()
        request.matched_route.name = 'route'
        request.custom_route_path = lambda *args, **kw: '/%s/filepath' % args[0]
        res = VersioningView(request).edit_conflict()
        expected = '<form data-action="/versioning_update_conflict_json/filepath'
        self.assertTrue(expected in res['content'])
        expected = '<textarea class="codemirror" name="filecontent">'
        self.assertTrue(expected in res['content'])
        expected = ('<input type="hidden" id="_xml_filename" '
                    'name="filename" value="file1.xml" />')
        self.assertTrue(expected in res['content'])

    @login_user('Bob')
    def test_update_conflict(self):
        class C(object): pass
        self.user_bob.config.root_path = self.client_dir
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
        s = o.empty_status(file1)
        self.assertEqual(s.status, helper.STATUS_CONFLICTED)

        request = testing.DummyRequest(params={})
        request.context = security.RootFactory(request)
        request.matched_route = C()
        request.matched_route.name = 'route'
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        res = VersioningView(request).update_conflict()
        expected = 'Missing parameters!'
        self.assertEqual(res['error_msg'], expected)

        request = testing.DummyRequest(
            params={'filecontent': 'content of the file',
                    'filename': 'file1.xml'})
        request.context = security.RootFactory(request)
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.matched_route = C()
        request.matched_route.name = 'route'
        request.route_path = lambda *args, **kw: '/%s' % args[0]

        def raise_func(*args, **kw):
            raise Exception('My error')

        with patch('xmltool.load_string') as m:
            m.side_effect = raise_func
            res = VersioningView(request).update_conflict()
            expected = 'The conflict is not resolved: My error'
            self.assertEqual(res['error_msg'],  expected)

        filecontent = open(file1, 'r').read()
        request = testing.DummyRequest(
            params={'filecontent': filecontent,
                    'filename': 'file1.xml'})
        request.context = security.RootFactory(request)
        request.custom_route_path = lambda *args, **kw: '/filepath'
        request.matched_route = C()
        request.matched_route.name = 'route'
        request.route_path = lambda *args, **kw: '/%s' % args[0]

        m = MagicMock()
        with patch('xmltool.load_string', return_value=m):
            res = VersioningView(request).update_conflict()
            s = o.empty_status(file1)
            self.assertEqual(s.status, helper.STATUS_MODIFED)
            expected = 'List of commitable files'
            self.assertTrue(expected in res['content'])

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
        self.assertEqual(res['info_msg'], 'The repository has been updated!')
        self.assertTrue('List of updated files:' in res['content'])

        # Create a conflict
        self.client.checkout('file://%s' % self.repo, 'svn_waxe_client1')
        open(os.path.join('svn_waxe_client1', 'file1.xml'), 'w').write('Hello Bob')
        self.client.checkin([os.path.join('svn_waxe_client1', 'file1.xml')],
                            'create conflict')
        self.client.update(self.client_dir)

        res = VersioningView(request).update()
        expected_error_msg = ('You can\'t update the repository, '
                              'you have to fix the conflicts first')
        self.assertEqual(res['error_msg'], expected_error_msg)
        expected_content = 'List of conflicted files that should be resolved:'
        self.assertTrue(expected_content in res['content'])


class FunctionalTestViewsNoVersioning(WaxeTestCase):

    def test_404(self):
        for url in [
            '/account/Bob/versioning/status',
            '/account/Bob/versioning/status.json',
            '/account/Bob/versioning/full-diff',
            '/account/Bob/versioning/full-diff.json',
            '/account/Bob/versioning/update',
            '/account/Bob/versioning/update.json',
            '/account/Bob/versioning/commit.json',
            '/account/Bob/versioning/update-texts.json',
        ]:
            self.testapp.get(url, status=404)


class FunctionalPysvnTestViews(WaxeTestCaseVersioning, CreateRepo2):
    ClassView = VersioningView

    def test_forbidden(self):
        for url in [
            '/account/Bob/versioning/status',
            '/account/Bob/versioning/status.json',
            '/account/Bob/versioning/full-diff',
            '/account/Bob/versioning/full-diff.json',
            '/account/Bob/versioning/update',
            '/account/Bob/versioning/update.json',
            '/account/Bob/versioning/commit.json',
            '/account/Bob/versioning/update-texts.json',
        ]:
            res = self.testapp.get(url, status=302)
            self.assertTrue('http://localhost/login?next=' in res.location)
            res = res.follow()
            self.assertEqual(res.status, "200 OK")
            self.assertTrue('<form' in res.body)
            self.assertTrue('Login' in res.body)

    @login_user('Bob')
    def test_short_status(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/account/Bob/versioning/short-status.json',
                               status=200)
        expected = {
            'file3.xml': helper.STATUS_UNVERSIONED,
            'file4.xml': helper.STATUS_ADDED,
            'file1.xml': helper.STATUS_MODIFED
        }
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_status(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/account/Bob/versioning/status', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)

    @login_user('Bob')
    def test_status_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/account/Bob/versioning/status.json', status=200)
        self.assertTrue(res.body)
        self.assertTrue('file1.xml' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test__full_diff(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/account/Bob/versioning/full-diff', status=200)
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.post('/account/Bob/versioning/full-diff', status=200)
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.post('/account/Bob/versioning/full-diff', status=200,
                                params={'filenames': 'file1.xml'})
        self.assertTrue('diff' in res.body)

    @login_user('Bob')
    def test_full_diff_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.get('/account/Bob/versioning/full-diff.json', status=200)
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.post('/account/Bob/versioning/full-diff.json', status=200)
        self.assertTrue('You should provide at least one filename' in res.body)

        res = self.testapp.post('/account/Bob/versioning/full-diff.json', status=200,
                                params={'filenames': 'file1.xml'})
        self.assertTrue('diff' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_commit_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir)
        res = self.testapp.post('/account/Bob/versioning/commit.json',
                                status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {
            "error_msg": "No file selected!",
            'breadcrumb': ('<li><a data-href="/account/Bob/explore.json?path=" '
                           'href="/account/Bob/explore?path=">root</a></li>')
        }
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_update(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir,
                                          versioning_password='secret_bob')
        res = self.testapp.get('/account/Bob/versioning/update', status=200)
        self.assertTrue('The repository has been updated!' in res.body)

    @login_user('Bob')
    def test_update_json(self):
        self.user_bob.config = UserConfig(root_path=self.client_dir,
                                          versioning_password='secret_bob')
        res = self.testapp.get('/account/Bob/versioning/update.json', status=200)
        self.assertTrue('The repository has been updated!' in res.body)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)

    @login_user('Bob')
    def test_update_texts(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/versioning/update-texts', status=200)
        self.assertTrue("Missing parameters!" in res.body)

    @login_user('Bob')
    def test_update_texts_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/versioning/update-texts.json', status=200)
        self.assertTrue(('Content-Type', 'application/json; charset=UTF-8') in
                        res._headerlist)
        expected = {
            "error_msg": "Missing parameters!",
            'breadcrumb': ('<li><a data-href="/account/Bob/explore.json?path=" '
                           'href="/account/Bob/explore?path=">root</a></li>')
        }
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_edit_conflict(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/versioning/edit-conflict',
                                status=200)
        self.assertTrue("A filename should be provided" in res.body)

    @login_user('Bob')
    def test_edit_conflict_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/versioning/edit-conflict.json',
                                status=200)
        expected = {
            "error_msg": "A filename should be provided",
            'breadcrumb': ('<li><a data-href="/account/Bob/explore.json?path=" '
                           'href="/account/Bob/explore?path=">root</a></li>')
        }
        self.assertEqual(json.loads(res.body), expected)

    @login_user('Bob')
    def test_update_conflict(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/versioning/update-conflict',
                                status=200)
        self.assertTrue("Missing parameters!" in res.body)

    @login_user('Bob')
    def test_update_conflict_json(self):
        path = os.path.join(os.getcwd(), 'waxe/tests/files')
        self.user_bob.config.root_path = path
        res = self.testapp.post('/account/Bob/versioning/update-conflict.json',
                                status=200)
        expected = {
            "error_msg": "Missing parameters!",
            'breadcrumb': ('<li><a data-href="/account/Bob/explore.json?path=" '
                           'href="/account/Bob/explore?path=">root</a></li>')
        }
        self.assertEqual(json.loads(res.body), expected)


class TestHelper(CreateRepo):

    def test_empty_status(self):
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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

    def test_full_diff(self):
        difflib.HtmlDiff._default_prefix = 0
        o = helper.PysvnVersioning(None, None, self.client_dir)
        self.assertEqual(o.full_diff(), [])
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
        res = o.full_diff('folder1/file1.xml')
        self.assertEqual(len(res), 1)
        relpath, html = res[0]
        self.assertEqual(relpath, 'folder1/file1.xml')
        self.assertTrue('<span class="diff_sub">Hello</span>' in html)
        self.assertTrue('<span class="diff_add">Hello World</span>' in html)

        difflib.HtmlDiff._default_prefix = 0
        res1 = o.full_diff()
        self.assertEqual(res, res1)

        # Unversioned files are not taken into account
        open(file2, 'w').write('Hello')
        difflib.HtmlDiff._default_prefix = 0
        res2 = o.full_diff()
        self.assertEqual(res[0], res2[0])
        relpath, html = res2[1]
        self.assertEqual(relpath, 'folder1/folder2/file2.xml')
        self.assertTrue('<span class="diff_add">Hello</span>' in html)

        difflib.HtmlDiff._default_prefix = 0
        res3 = o.full_diff('folder1/folder2/file2.xml')
        self.assertEqual(len(res3), 1)
        relpath, html = res3[0]
        self.assertEqual(relpath, 'folder1/folder2/file2.xml')
        self.assertTrue('<span class="diff_add">Hello</span>' in html)

        self.client.add(file2)
        difflib.HtmlDiff._default_prefix = 0
        res = o.full_diff()
        self.assertEqual(len(res), 2)
        relpath, html = res[0]
        self.assertEqual(relpath, 'folder1/file1.xml')
        self.assertTrue('<span class="diff_sub">Hello</span>' in html)
        self.assertTrue('<span class="diff_add">Hello World</span>' in html)

        relpath, html = res[1]
        self.assertEqual(relpath, 'folder1/folder2/file2.xml')
        self.assertTrue('<span class="diff_add">Hello</span>' in html)

        self.client.revert(file1)
        self.client.remove(file1)
        difflib.HtmlDiff._default_prefix = 0
        res = o.full_diff()
        self.assertEqual(len(res), 2)
        relpath, html = res[0]
        self.assertEqual(relpath, 'folder1/file1.xml')
        self.assertTrue('<span class="diff_sub">Hello</span>' in html)

        relpath, html = res[1]
        self.assertEqual(relpath, 'folder1/folder2/file2.xml')
        self.assertTrue('<span class="diff_add">Hello</span>' in html)

    def test_get_commitable_files(self):
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        o = helper.PysvnVersioning(None, None, self.client_dir)
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
        self.patcher1 = patch('waxe.views.versioning.helper.get_svn_client',
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

        o = helper.PysvnVersioning(None, None, self.client_dir)
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

        o = helper.PysvnVersioning(None, None, self.client_dir)
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

        o = helper.PysvnVersioning(None, None, self.client_dir)
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
