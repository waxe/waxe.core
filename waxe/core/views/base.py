from pyramid.security import has_permission
from pyramid.view import view_defaults
import pyramid.httpexceptions as exc
from .. import security, models, browser
import sqla_taskq.models as taskqm
from waxe.search import elastic


@view_defaults(renderer='json')
class JSONView(object):

    def __init__(self, request):
        self.request = request

    @property
    def req_get(self):
        return self.request.GET

    @property
    def req_post(self):
        if self.request.POST:
            return self.request.POST
        if self.request.body:
            # Angular post the data as body
            return self.request.json_body
        return {}

    def req_post_getall(self, key):
        if self.request.POST:
            return self.request.POST.getall(key)
        if self.request.body:
            # Angular post the data as body
            # The value as json should already be a list
            return self.request.json_body.get(key)
        return {}


class BaseView(JSONView):
    """All the Waxe views should inherit from this one. It doesn't make any
    validation, it can be used anywhere
    """

    def __init__(self, request):
        super(BaseView, self).__init__(request)
        self.logged_user_login = security.get_userid_from_request(self.request)
        self.logged_user = security.get_user(self.logged_user_login)
        if not self.logged_user_login:
            # We should always be logged
            raise exc.HTTPUnauthorized()

        if not self.logged_user:
            # Insert a new user
            self.logged_user = models.User(login=self.logged_user_login)
            models.DBSession.add(self.logged_user)

        if not self.logged_user.config:
            # Also create the user config
            self.logged_user.config = models.UserConfig()
            models.DBSession.add(self.logged_user.config)

        self.current_user = self.logged_user
        self.root_path = None
        if self.current_user and self.current_user.config:
            self.root_path = self.current_user.config.root_path
        self.extensions = self.request.registry.settings['waxe.extensions']

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

    def user_is_supervisor(self):
        """Check if the logged user is supervisor.

        :return: True if the logged user is supervisor
        :rtype: bool
        """
        return has_permission('supervisor',
                              self.request.context,
                              self.request)

    def get_editable_logins(self):
        """Get the editable login by the logged user.

        :return: list of login
        :rtype: list of str
        """
        lis = []
        if self.logged_user.config.root_path:
            lis += [self.logged_user.login]

        if self.user_is_admin() or self.user_is_supervisor():
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
        if self.request.registry.settings.get('waxe.versioning') == 'true':
            if (self.current_user and
               self.current_user.config and
               self.current_user.config.use_versioning):
                return True
        return False

    def logged_user_profile(self):
        """Get the profile of the logged user
        """
        has_file = bool(self.logged_user.config.root_path)
        dic = {
            'login': self.logged_user_login,
            'has_file': has_file,
            'logins': [],
        }

        logins = self.get_editable_logins()
        if logins:
            dic['logins'] = logins

        return dic


@view_defaults(renderer='json', permission='edit')
class BaseUserView(BaseView):
    """Base view which check that the current user has a root path. It's to
    check he has some files to edit!
    """
    # TODO: improve the error messages
    def __init__(self, request):
        super(BaseUserView, self).__init__(request)

        login = self.request.matchdict.get('login')
        if self.logged_user_login != login:
            logins = self.get_editable_logins()
            if login:
                if login not in logins:
                    raise exc.HTTPClientError("The user doesn't exist")
                user = models.User.query.filter_by(login=login).one()
                self.current_user = user

        self.root_path = None
        if self.current_user and self.current_user.config:
            self.root_path = self.current_user.config.root_path

        if not self.root_path:
            raise exc.HTTPClientError("root path not defined")

    def get_versioning_obj(self, commit=False):
        """Get the versioning object. For now only svn is supported.
        """
        if self.has_versioning():
            from waxe.core.views.versioning import helper
            return helper.PysvnVersioning(self.request,
                                          self.extensions,
                                          self.current_user,
                                          self.logged_user,
                                          self.root_path,
                                          commit)
        return None

    def get_search_dirname(self):
        settings = self.request.registry.settings
        if 'waxe.search.index_name_prefix' not in settings:
            return None

        return self.current_user.get_search_dirname()

    def add_opened_file(self, path):
        iduser_owner = None
        if self.logged_user != self.current_user:
            iduser_owner = self.current_user.iduser

        self.logged_user.add_opened_file(path, iduser_owner=iduser_owner)

    def add_commited_file(self, path):
        iduser_commit = None
        if self.logged_user != self.current_user:
            iduser_commit = self.current_user.iduser

        self.logged_user.add_commited_file(path, iduser_commit=iduser_commit)

    # TODO: Move the search logic in waxe.search
    def _get_search_index(self):
        user_index_name = self.get_search_dirname()
        if not user_index_name:
            raise exc.HTTPInternalServerError('The search is not available')

        settings = self.request.registry.settings
        index_name_prefix = settings.get('waxe.search.index_name_prefix')
        return index_name_prefix + user_index_name

    def _get_search_url(self):
        settings = self.request.registry.settings
        if 'waxe.search.url' not in settings:
            raise exc.HTTPInternalServerError('The search is not available')

        return settings['waxe.search.url']

    def add_indexation_task(self, paths=None):
        # TODO: put paths required, we should always have it
        dirname = self.get_search_dirname()
        if not dirname:
            return None
        uc = self.current_user.config
        if not uc.root_path:
            return None

        if not paths:
            paths = browser.get_all_files(self.extensions, uc.root_path, uc.root_path)[1]
        url = self._get_search_url()
        index_name = self._get_search_index()

        taskqm.Task.create(
            elastic.partial_index,
            [url, index_name, paths, uc.root_path],
            owner=str(uc.user.iduser),
            unique_key='search_%i' % uc.user.iduser)

        # Since we commit the task we need to re-bound the user to the session
        # to make sure we can reuse self.logged_user
        # For example if we use ldap authentication, self.logged_user can
        # be None if the user is not in the DB.
        models.DBSession.add(self.logged_user)
