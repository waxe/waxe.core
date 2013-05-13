import unittest
from pyramid import testing
from ..testing import WaxeTestCase, login_user

class TestViews(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from ..views.index import Views
        request = testing.DummyRequest()
        response = Views(request).home()
        self.assertEqual(response, {'content': 'home content'})


class FunctionalTestViews(WaxeTestCase):

    def test_home_forbidden(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(
            res.location,
            'http://localhost/login?next=http%3A%2F%2Flocalhost%2F')
        res = res.follow()
        self.assertEqual(res.status, "200 OK")
        self.assertTrue('<form' in res.body)
        self.assertTrue('Login' in res.body)

    @login_user('Fred')
    def test_home_bad_login(self):
        res = self.testapp.get('/', status=302)
        self.assertEqual(res.location,
                         'http://localhost/forbidden')

    @login_user('Bob')
    def test_home(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue('home content' in res.body)
