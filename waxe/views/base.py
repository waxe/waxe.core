import os
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import has_permission
from .. import security, models, search, browser
from taskq.models import Task


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
        self.current_user = self.logged_user
        self.root_path = None

        def custom_route_path(request):
            def func(name, *args, **kw):
                if self.current_user:
                    kw['login'] = self.current_user.login
                else:
                    kw['login'] = self.logged_user_login
                return request.route_path(name, *args, **kw)
            return func
        request.set_property(custom_route_path,
                             'custom_route_path',
                             reify=True)

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

    def has_versioning(self):
        """Returns True if the current_user root path is versionned and he can
        use it!
        """
        if self.request.registry.settings.get('versioning') == 'true':
            if (self.current_user and
               self.current_user.config and
               self.current_user.config.use_versioning):
                return True
        return False

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
        if self.current_user:
            editor_login = self.current_user.login
        dic['editor_login'] = editor_login

        logins = [l for l in self.get_editable_logins() if l != editor_login]
        if logins:
            dic['logins'] = logins

        dic['versioning'] = self.has_versioning()
        dic['search'] = ('whoosh.path' in self.request.registry.settings)
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
            return self.request.custom_route_path(
                'explore_json', _query=[(key, path)])

        def get_href(path, key):
            return self.request.custom_route_path(
                'explore', _query=[(key, path)])

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

        login = self.request.matchdict.get('login')
        if self.logged_user_login != login:
            logins = self.get_editable_logins()
            if login:
                if login not in logins:
                    if self._is_json():
                        raise JSONHTTPBadRequest('The user doesn\'t exist')
                    raise HTTPBadRequest('The user doesn\'t exist')
                user = models.User.query.filter_by(login=login).one()
                self.current_user = user

        if self.current_user and self.current_user.config:
            self.root_path = self.current_user.config.root_path

        if (not self.root_path and
                request.matched_route.name != 'redirect'):
            if self._is_json():
                raise JSONHTTPBadRequest('root path not defined')
            raise HTTPBadRequest('root path not defined')

    def get_versioning_obj(self):
        """Get the versioning object. For now only svn is supported.
        """
        if self.has_versioning():
            from waxe.views.versioning import helper
            return helper.PysvnVersioning(self.request, self.current_user,
                                          self.root_path)
        return None

    def get_search_dirname(self):
        settings = self.request.registry.settings
        if 'whoosh.path' not in settings:
            return None
        return self.current_user.get_search_dirname(settings['whoosh.path'])

    def add_indexation_task(self, paths=None):
        # TODO: Use paths: the only files we want to udpate
        # It's not done for now since search didn't handle this case.
        dirname = self.get_search_dirname()
        if not dirname:
            return None
        uc = self.current_user.config
        if not uc or not uc.root_path:
            return None
        paths = browser.get_all_files(uc.root_path, uc.root_path)[1]
        Task.create(search.do_index, [dirname, paths],
                    owner=str(self.current_user.iduser))

        # Since we commit the task we need to re-bound the user to the session
        # to make sure we can reuse self.logged_user
        if self.logged_user:
            # For example if we use ldap authentication, self.logged_user can
            # be None if the user is not in the DB.
            models.DBSession.add(self.logged_user)
