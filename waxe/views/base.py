from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import has_permission
from .. import security


class JSONHTTPBadRequest(HTTPBadRequest):
    pass


class BaseViews(object):
    """All the Waxe views should inherit from this one. It doesn't make any
    validation, it can be used anywhere
    """

    def __init__(self, request):
        self.request = request
        self.logged_user = security.get_user_from_request(self.request)
        self.current_user = self._get_current_user()
        self.root_path = None
        if self.current_user and self.current_user.config:
            self.root_path = self.current_user.config.root_path

    def _get_current_user(self):
        """Get the user where are editing
        """
        user = None
        if 'editor_login' in self.request.session:
            user = security.get_user(self.request.session['editor_login'])
            if user:
                return user
        return self.logged_user

    def user_is_admin(self):
        """Check if the logged user is admin.

        :return: True if the logged user is admin
        :rtype: bool
        """
        return has_permission('admin',
                              self.request.context,
                              self.request)

    def _is_json(self):
        """Check the current request is a json one.

        :return: True if it's a json request
        :rtype: bool

        .. note:: We assume the json route names always end with '_json'
        """
        return self.request.matched_route.name.endswith('_json')


class BaseUserViews(BaseViews):
    """Base view which check that the current user has a root path. It's to
    check he has some files to edit!
    """
    def __init__(self, request):
        super(BaseUserViews, self).__init__(request)
        if (not self.root_path and
                request.matched_route.name != 'login_selection'):
            if self._is_json():
                raise JSONHTTPBadRequest('root path not defined')
            raise HTTPBadRequest('root path not defined')
