import json
from ..testing import WaxeTestCase, login_user


class FunctionalTestIndexView2(WaxeTestCase):

    def test_forbidden(self):
        self.testapp.get('/profile.json', status=401)

    @login_user('Admin')
    def test_profile(self):
        res = self.testapp.get('/profile.json', status=200)
        dic = json.loads(res.body)
        self.assertTrue('login' in dic)
