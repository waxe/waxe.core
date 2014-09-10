from .testing import WaxeTestCase, DBSession
from ..models import (
    get_editors,
    get_contributors,
    User,
    Role,
    UserConfig,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
    VersioningPath,
    VERSIONING_PATH_STATUS_ALLOWED,
    VERSIONING_PATH_STATUS_FORBIDDEN
)
from mock import patch


class TestFunctions(WaxeTestCase):

    def test_get_editors(self):
        result = get_editors()
        self.assertEqual(result, [])

        user = User(login='user1', password='pass1')
        user.roles = [Role.query.filter_by(name=ROLE_EDITOR).one()]
        DBSession.add(user)
        result = get_editors()
        self.assertEqual(result, [])

        user.config = UserConfig(root_path='/path')
        DBSession.add(user)
        result = get_editors()
        self.assertEqual(result, [user])

    def test_get_contributor(self):
        result = get_contributors()
        self.assertEqual(result, [])

        user = User(login='user1', password='pass1')
        user.roles = [Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()]
        DBSession.add(user)
        result = get_contributors()
        self.assertEqual(result, [])

        user.config = UserConfig(root_path='/path')
        DBSession.add(user)
        result = get_contributors()
        self.assertEqual(result, [user])


class TestGeneral(WaxeTestCase):

    def test_get_tws_view_html(self):
        DBSession.add(self.user_fred)
        self.assertTrue(self.user_fred.config.get_tws_view_html())

    def test___unicode__(self):
        DBSession.add(self.user_fred)
        role = Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()
        self.assertTrue(unicode(role))
        self.assertTrue(unicode(self.user_fred))
        vp = VersioningPath(
            status=VERSIONING_PATH_STATUS_ALLOWED,
            path='/home/test/')
        self.assertTrue(unicode(vp))


class TestUser(WaxeTestCase):

    def test_has_role(self):
        DBSession.add(self.user_bob)
        self.assertTrue(self.user_bob.has_role('admin'))
        self.assertFalse(self.user_bob.has_role('unexisting'))

    def test_is_admin(self):
        DBSession.add(self.user_bob)
        DBSession.add(self.user_fred)
        self.assertTrue(self.user_bob.is_admin())
        self.assertFalse(self.user_fred.is_admin())

    def test_get_search_dirname(self):
        res = self.user_fred.get_search_dirname('/tmp/fake')
        self.assertEqual(res, '/tmp/fake/user-None')
        self.user_fred.config = None
        res = self.user_fred.get_search_dirname('/tmp/fake')
        self.assertEqual(res, None)

    def test_add_opened_file(self):
        self.user_bob.add_opened_file('/tmp')
        self.assertEqual(len(self.user_bob.opened_files), 1)
        self.assertEqual(self.user_bob.opened_files[0].path, '/tmp')

        for i in range(9):
            self.user_bob.add_opened_file('/tmp-%i' % i)

        expected = [
            '/tmp-8', '/tmp-7', '/tmp-6', '/tmp-5', '/tmp-4',
            '/tmp-3', '/tmp-2', '/tmp-1', '/tmp-0', '/tmp']

        paths = [o.path for o in self.user_bob.opened_files]
        self.assertEqual(paths, expected)

        self.user_bob.add_opened_file('/tmp-last',
                                      iduser_owner=self.user_fred.iduser)

        expected = [
            '/tmp-last', '/tmp-8', '/tmp-7', '/tmp-6', '/tmp-5',
            '/tmp-4', '/tmp-3', '/tmp-2', '/tmp-1', '/tmp-0']

        paths = [o.path for o in self.user_bob.opened_files]
        self.assertEqual(paths, expected)
        self.assertEqual(self.user_bob.opened_files[0].iduser_owner,
                         self.user_fred.iduser)

    def test_add_commited_file(self):
        self.user_bob.add_commited_file('/tmp')
        self.assertEqual(len(self.user_bob.commited_files), 1)
        self.assertEqual(self.user_bob.commited_files[0].path, '/tmp')

        for i in range(9):
            self.user_bob.add_commited_file('/tmp-%i' % i)

        expected = [
            '/tmp-8', '/tmp-7', '/tmp-6', '/tmp-5', '/tmp-4',
            '/tmp-3', '/tmp-2', '/tmp-1', '/tmp-0', '/tmp']

        paths = [o.path for o in self.user_bob.commited_files]
        self.assertEqual(paths, expected)

        self.user_bob.add_commited_file('/tmp-last',
                                        iduser_commit=self.user_fred.iduser)

        expected = [
            '/tmp-last', '/tmp-8', '/tmp-7', '/tmp-6', '/tmp-5',
            '/tmp-4', '/tmp-3', '/tmp-2', '/tmp-1', '/tmp-0']

        paths = [o.path for o in self.user_bob.commited_files]
        self.assertEqual(paths, expected)
        self.assertEqual(self.user_bob.commited_files[0].iduser_commit,
                         self.user_fred.iduser)
