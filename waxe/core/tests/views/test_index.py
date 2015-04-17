import json
from pyramid import testing
import pyramid.httpexceptions as exc
from ..testing import WaxeTestCase, login_user, BaseTestCase
from waxe.core import security
from waxe.core.models import (
    DBSession,
    User,
    UserConfig,
)

from waxe.core.views.index import (
    IndexView,
)


class C(object):
    pass


class TestIndexView(BaseTestCase):

    def setUp(self):
        super(TestIndexView, self).setUp()
        self.config.registry.settings.update({
            'waxe.versioning': True,
            'pyramid_auth.no_routes': 'true',
            'pyramid_auth.cookie.secret': 'scrt',
            'pyramid_auth.cookie.callback': ('waxe.core.security.'
                                             'get_user_permissions'),
            'pyramid_auth.cookie.validate_function': (
                'waxe.core.security.validate_password'),
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
        self.assertEqual(res.location, '/explore_json/Bob')

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
        except exc.HTTPBadRequest, e:
            self.assertEqual(str(e), 'root path not defined')


class FunctionalTestIndexView(WaxeTestCase):

    def test_redirect_forbidden(self):
        self.testapp.get('/', status=401)

    @login_user('Admin')
    def test_redirect(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/account/Admin/explore.json')


class FunctionalTestIndexView2(WaxeTestCase):

    def test_forbidden(self):
        self.testapp.get('/profile.json', status=401)

    @login_user('Admin')
    def test_profile(self):
        res = self.testapp.get('/profile.json', status=200)
        dic = json.loads(res.body)
        self.assertTrue('login' in dic)
