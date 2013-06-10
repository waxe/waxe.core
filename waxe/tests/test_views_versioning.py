import os
import simplejson
from pyramid import testing
from subprocess import Popen
from ..testing import WaxeTestCase, login_user
from mock import patch, MagicMock, Mock
from ..models import (
    DBSession,
    User,
    UserConfig,
    Role,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR
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


class FunctionalTestViews(WaxeTestCase):

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
