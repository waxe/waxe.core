from ..testing import WaxeTestCase, DBSession
from ..models import (
    get_editors,
    get_contributors,
    User,
    Role,
    UserConfig,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR
)


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


class TestUser(WaxeTestCase):

    def test_has_role(self):
        DBSession.add(self.user_bob)
        self.assertTrue(self.user_bob.has_role('admin'))
        self.assertFalse(self.user_bob.has_role('unexisting'))

    def test_multiple_account(self):
        user = User(login='user1', password='pass1')
        DBSession.add(user)
        DBSession.add(self.user_bob)
        self.assertFalse(user.multiple_account())
        self.assertFalse(self.user_bob.multiple_account())

        user = User(login='contributor', password='pass1')
        user.roles = [Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()]
        user.config = UserConfig(root_path='/path')
        DBSession.add(user)
        self.assertTrue(self.user_bob.multiple_account())

        DBSession.remove()
        self.assertFalse(self.user_bob.multiple_account())

        user = User(login='editor', password='pass1')
        user.roles = [Role.query.filter_by(name=ROLE_EDITOR).one()]
        user.config = UserConfig(root_path='/path')
        DBSession.add(user)
        self.assertTrue(self.user_bob.multiple_account())
        self.assertFalse(user.multiple_account())

        contributor = User(login='contributor', password='pass1')
        contributor.roles = [Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()]
        contributor.config = UserConfig(root_path='/path')
        DBSession.add(contributor)
        self.assertTrue(user.multiple_account())

    def test_get_editable_logins(self):
        user = User(login='user1', password='pass1')
        DBSession.add(user)
        DBSession.add(self.user_bob)
        self.assertEqual(user.get_editable_logins(), [])
        self.assertEqual(self.user_bob.get_editable_logins(), [])

        contributor = User(login='contributor', password='pass1')
        contributor.roles = [Role.query.filter_by(name=ROLE_CONTRIBUTOR).one()]
        contributor.config = UserConfig(root_path='/path')
        DBSession.add(contributor)

        editor = User(login='editor', password='pass1')
        editor.roles = [Role.query.filter_by(name=ROLE_EDITOR).one()]
        editor.config = UserConfig(root_path='/path')
        DBSession.add(editor)

        result = self.user_bob.get_editable_logins()
        expected = [editor.login, contributor.login]
        self.assertEqual(result, expected)

        self.user_bob.config = UserConfig(root_path='/path')
        result = self.user_bob.get_editable_logins()
        expected = [self.user_bob.login, editor.login, contributor.login]
        self.assertEqual(result, expected)

        result = editor.get_editable_logins()
        expected = [editor.login, contributor.login]
        self.assertEqual(result, expected)

        editor.config = None
        result = editor.get_editable_logins()
        expected = [contributor.login]
        self.assertEqual(result, expected)






