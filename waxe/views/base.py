from pyramid.httpexceptions import HTTPBadRequest
from .. import security


class JSONHTTPBadRequest(HTTPBadRequest):
    pass


class BaseViews(object):

    def __init__(self, request):
        self.request = request
        self.logged_user = security.get_user_from_request(self.request)
        self.current_user = self.get_current_user()
        self.root_path = None
        if self.current_user and self.current_user.config:
            self.root_path = self.current_user.config.root_path

    def get_current_user(self):
        user = None
        if 'editor_login' in self.request.session:
            user = security.get_user(self.request.session['editor_login'])
            if user:
                return user
        return self.logged_user

    def _is_json(self):
        return self.request.matched_route.name.endswith('_json')


class BaseUserViews(BaseViews):

    def __init__(self, request):
        super(BaseUserViews, self).__init__(request)
        if (not self.root_path and
                request.matched_route.name != 'login_selection'):
            if self._is_json():
                raise JSONHTTPBadRequest('root path not defined')
            raise HTTPBadRequest('root path not defined')
