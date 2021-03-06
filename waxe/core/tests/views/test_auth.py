from ..testing import WaxeTestCase


class FunctionalTestAuthView(WaxeTestCase):

    def test_login(self):
        # POST only
        self.testapp.get('/api/1/login.json', status=404)
        # No params
        self.testapp.post('/api/1/login.json', status=400)
        # Bad params
        self.testapp.post('/api/1/login.json', params={'hello': 'world'},
                          status=401)
        # Bad password
        self.testapp.post('/api/1/login.json',
                          params={
                              'login': 'Bob',
                              'password': 'XXX',
                          },
                          status=401)

        # OK
        res = self.testapp.post('/api/1/login.json',
                                params={
                                    'login': 'Bob',
                                    'password': 'secret_bob',
                                },
                                status=200)
        self.assertEqual(res.body, 'true')

        # It should work when posting as json
        res = self.testapp.post_json('/api/1/login.json',
                                     params={
                                         'login': 'Bob',
                                         'password': 'secret_bob',
                                     },
                                     status=200)
        self.assertEqual(res.body, 'true')

    def test_logout(self):
        # GET only
        self.testapp.post('/api/1/logout.json', status=404)
        # OK
        res = self.testapp.get('/api/1/logout.json', status=200)
        self.assertEqual(res.body, '"You are logged off"')
