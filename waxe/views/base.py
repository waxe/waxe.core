import os
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import has_permission
from .. import security, models


class JSONHTTPBadRequest(HTTPBadRequest):
    pass


class BaseView(object):
    """All the Waxe views should inherit from this one. It doesn't make any
    validation, it can be used anywhere
    """

    def __init__(self, request):
        self.request = request
        self.logged_user_login = security.get_userid_from_request(self.request)
        self.logged_user = security.get_user(self.logged_user_login)
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

    def user_is_editor(self):
        """Check if the logged user is editor.

        :return: True if the logged user is editor
        :rtype: bool
        """
        return has_permission('editor',
                              self.request.context,
                              self.request)

    def user_is_contributor(self):
        """Check if the logged user is contributor.

        :return: True if the logged user is contributor
        :rtype: bool
        """
        return has_permission('contributor',
                              self.request.context,
                              self.request)

    def _is_json(self):
        """Check the current request is a json one.

        :return: True if it's a json request
        :rtype: bool

        .. note:: We assume the json route names always end with '_json'
        """
        return self.request.matched_route.name.endswith('_json')

    def get_editable_logins(self):
        """Get the editable login by the logged user.

        :return: list of login
        :rtype: list of str
        """
        lis = []
        if (hasattr(self.logged_user, 'config') and
           self.logged_user.config and self.logged_user.config.root_path):
            lis += [self.logged_user.login]

        if self.user_is_admin():
            contributors = models.get_contributors()
            editors = models.get_editors()
            for user in (editors + contributors):
                lis += [user.login]
        elif self.user_is_editor():
            contributors = models.get_contributors()
            for user in contributors:
                lis += [user.login]

        return list(set(lis))

    def _response(self, dic):
        """Update the given dic for non json request with some data needed in
        the navbar.

        :param dic: a dict containing some data for the reponse
        :type dic: dict
        :return: the given dict updated if needed
        :rtype: dict
        """
        if self._is_json():
            return dic

        editor_login = self.logged_user_login
        if self.root_path:
            editor_login = self.current_user.login
        dic['editor_login'] = editor_login

        logins = [l for l in self.get_editable_logins() if l != editor_login]
        if logins:
            dic['logins'] = logins

        if editor_login and 'versioning' in self.request.registry.settings:
            editor = models.User.query.filter_by(login=editor_login).one()
            if editor.config and editor.config.use_versioning:
                dic['versioning'] = True

        return dic


class NavigationView(BaseView):

    def _get_breadcrumb_data(self, relpath):
        tple = []
        while relpath:
            name = os.path.basename(relpath)
            tple += [(name, relpath)]
            relpath = os.path.dirname(relpath)

        tple += [('root', '')]
        tple.reverse()
        return tple

    def _get_breadcrumb(self, relpath, force_link=False):
        def get_data_href(path, key):
            return self.request.route_path(
                'home_json', _query=[(key, path)])

        def get_href(path, key):
            return self.request.route_path(
                'home', _query=[(key, path)])

        tple = self._get_breadcrumb_data(relpath)
        html = []
        for index, (name, relpath) in enumerate(tple):
            if index == len(tple) - 1 and not force_link:
                html += ['<li class="active">%s</li>' % (name)]
            else:
                html += [(
                    '<li>'
                    '<a data-href="%s" href="%s">%s</a> '
                    '</li>') % (
                        get_data_href(relpath, 'path'),
                        get_href(relpath, 'path'),
                        name,
                    )]
        return ''.join(html)


class BaseUserView(NavigationView):
    """Base view which check that the current user has a root path. It's to
    check he has some files to edit!
    """
    def __init__(self, request):
        super(BaseUserView, self).__init__(request)
        if (not self.root_path and
                request.matched_route.name != 'login_selection'):
            if self._is_json():
                raise JSONHTTPBadRequest('root path not defined')
            raise HTTPBadRequest('root path not defined')
