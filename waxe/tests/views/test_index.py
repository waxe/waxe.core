from pyramid import testing
from ..testing import WaxeTestCase, login_user, BaseTestCase
from waxe import security
from waxe.models import (
    DBSession,
    User,
    UserConfig,
)

from waxe.views.index import (
    Views,
    BadRequestView,
    HTTPBadRequest,
)


class TestViews(BaseTestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        self.config.registry.settings.update({
            'versioning': True,
            'authentication.cookie.secret': 'scrt',
            'authentication.cookie.callback': ('waxe.security.'
                                               'get_user_permissions')
        })
        self.config.include('pyramid_auth')
        self.user_fred.config.use_versioning = True
        self.user_bob.config.use_versioning = True

    @login_user('Bob')
    def test_login_selection(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        try:
            res = Views(request).login_selection()
            assert(False)
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'Invalid login')

        request = testing.DummyRequest(params={'login': 'editor'})
        request.context = security.RootFactory(request)
        try:
            res = Views(request).login_selection()
            assert(False)
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'Invalid login')

        editor = User(login='editor', password='pass1')
        editor.roles = [self.role_editor]
        editor.config = UserConfig(root_path='/path')
        DBSession.add(editor)

        res = Views(request).login_selection()
        self.assertEqual(res.status, "302 Found")
        self.assertEqual(res.location, '/')
        expected = {'editor_login': 'editor', 'root_path': '/path'}
        self.assertEqual(request.session, expected)

    @login_user('Admin')
    def test_bad_request(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        dic = BadRequestView(request).bad_request()
        self.assertEqual(len(dic), 1)
        expected = ('Go to your <a href="/admin_home">'
                    'admin interface</a> to insert a new user')
        self.assertEqual(dic['content'], expected)

        editor = User(login='editor', password='pass1')
        editor.roles = [self.role_editor]
        editor.config = UserConfig(root_path='/path')
        DBSession.add(editor)

        self.user_bob.roles += [self.role_editor]
        request.route_path = lambda *args, **kw: '/editorpath'
        dic = BadRequestView(request).bad_request()
        expected = {'content': (u'  <a href="/editorpath">Bob</a>\n'
                                u'  <a href="/editorpath">editor</a>\n')}
        self.assertEqual(dic, expected)

    @login_user('Fred')
    def test_bad_request_not_admin(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        self.user_fred.config.root_path = ''
        dic = BadRequestView(request).bad_request()
        self.assertEqual(len(dic), 1)
        expected = 'There is a problem with your configuration'
        self.assertTrue(expected in dic['content'])


class FunctionalTestViews(WaxeTestCase):

    def test_login_selection_forbidden(self):
        res = self.testapp.get('/login-selection', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2Flogin-selection')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Admin')
    def test_login_selection(self):
        res = self.testapp.get('/login-selection', status=200)
        expected = ('Go to your <a href="/admin">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
