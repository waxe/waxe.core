from pyramid import testing
from ..testing import WaxeTestCase, login_user, BaseTestCase
from waxe import security
from waxe.models import (
    DBSession,
    User,
    UserConfig,
)

from waxe.views.index import (
    IndexView,
    BadRequestView,
    HTTPBadRequest,
)


class C(object):
    pass


class TestIndexView(BaseTestCase):

    def setUp(self):
        super(TestIndexView, self).setUp()
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
    def test_redirect(self):
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: (
            ('/%s' % args[0])
            + '/%(login)s' % kw)
        res = IndexView(request).redirect()
        self.assertEqual(res.status, "302 Found")
        self.assertEqual(res.location, '/home/Bob')

    def test_redirect_not_logged(self):
        request = testing.DummyRequest()
        request.route_path = lambda *args, **kw: (
            ('/%s' % args[0])
            + '/%(login)s' % kw)
        request.matched_route = C()
        request.matched_route.name = 'route'
        try:
            IndexView(request).redirect()
            assert(False)
        except HTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')

    @login_user('Admin')
    def test_bad_request(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route_json'
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
        self.maxDiff = None
        expected = {
            'content': (u'Please select the account you want to use:'
                        '\n<br />\n<br />\n'
                        '<ul class="list-unstyled">'
                        '\n  <li>\n    '
                        '<a href="/editorpath">Bob</a>\n  '
                        '</li>\n  '
                        '<li>\n    '
                        '<a href="/editorpath">editor</a>\n  '
                        '</li>\n</ul>\n')}
        self.assertEqual(dic, expected)

    @login_user('Fred')
    def test_bad_request_not_admin(self):
        request = testing.DummyRequest()
        request.context = security.RootFactory(request)
        request.route_path = lambda *args, **kw: '/%s' % args[0]
        request.matched_route = C()
        request.matched_route.name = 'route_json'
        self.user_fred.config.root_path = ''
        dic = BadRequestView(request).bad_request()
        self.assertEqual(len(dic), 1)
        expected = 'There is a problem with your configuration'
        self.assertTrue(expected in dic['content'])


class FunctionalTestIndexView(WaxeTestCase):

    def test_redirect_forbidden(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2F')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Admin')
    def test_redirect(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/account/Admin/')
        res = res.follow()
        expected = ('Go to your <a href="/admin">'
                    'admin interface</a> to insert a new user')
        self.assertTrue(expected in res.body)
