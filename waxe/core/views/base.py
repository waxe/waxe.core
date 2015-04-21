import os
import importlib
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import has_permission
from pyramid.renderers import render
from pyramid.view import view_defaults, view_config
from pyramid.httpexceptions import HTTPException
import pyramid.httpexceptions as exc
from .. import security, models, search, browser
from taskq.models import Task


NAV_EDIT = 'edit'
NAV_EDIT_TEXT = 'edit_text'
NAV_DIFF = 'diff'


class JSONHTTPBadRequest(HTTPBadRequest):
    pass


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

    def _get_last_files(self):
        """This function should be defined here since we need use it for the
        user without config or config.root_path.
        """
        if not self.current_user:
            # User is authenticated but not in the DB
            return ''
        opened_files = self.current_user.opened_files[::-1]
        commited_files = self.current_user.commited_files[::-1]
        html = render('blocks/last_files.mak',
                      {'opened_files': opened_files,
                       'commited_files': commited_files},
                      self.request)
        return html

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
        if self.request.registry.settings.get('waxe.versioning') == 'true':
            if (self.current_user and
               self.current_user.config and
               self.current_user.config.use_versioning):
                return True
        return False

    def _get_xmltool_transform(self):
        """Before writing XML, we can call a function to transform it.
        """
        if 'waxe.xml.xmltool.transform' not in self.request.registry.settings:
            return None
        func = self.request.registry.settings['waxe.xml.xmltool.transform']
        mod, func = func.rsplit('.', 1)
        return getattr(importlib.import_module(mod), func)

    def _profile(self):
        """Get the profile of the user
        """
        dic = {
            'login': self.logged_user_login,
            'editor_login': self.logged_user_login,
            'base_path': '/account/%s' % self.logged_user_login,
            'root_path': self.root_path,
            'root_template_path': None,
            'extenstions': self.extensions,
            'versioning': self.has_versioning(),
            'search': ('whoosh.path' in self.request.registry.settings),
            'xml_renderer': ('waxe.renderers' in
                             self.request.registry.settings),
            'dtd_urls': self.request.registry.settings['dtd_urls'].split(),
            'layout_tree_position': models.LAYOUT_DEFAULTS['tree_position'],
            'layout_readonly_position': models.LAYOUT_DEFAULTS[
                'readonly_position'],
            'logins': [],
        }

        if self.current_user:
            dic['editor_login'] = self.current_user.login
            dic['base_path'] = '/account/%s' % self.current_user.login
            config = self.current_user.config
            if config:
                dic['root_template_path'] = config.root_template_path

        if self.logged_user and self.logged_user.config:
            config = self.logged_user.config
            dic['layout_tree_position'] = config.tree_position
            dic['layout_readonly_position'] = config.readonly_position

        logins = self.get_editable_logins()
        if logins:
            dic['logins'] = logins

        return dic


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

        if self.current_user and self.current_user.config:
            self.root_path = self.current_user.config.root_path

        if (not self.root_path and
           request.matched_route.name not in ['profile']):
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
        if 'whoosh.path' not in settings:
            return None

        return self.current_user.get_search_dirname(settings['whoosh.path'])

    def add_opened_file(self, path):
        if not self.logged_user:
            # User is authenticated but not in the DB
            return False
        iduser_owner = None
        if self.logged_user != self.current_user:
            if self.logged_user.config and self.logged_user.config.root_path:
                # Don't store the last edited files from another account if
                # there is an account for the logged user.
                return False
            iduser_owner = self.current_user.iduser

        self.logged_user.add_opened_file(path, iduser_owner=iduser_owner)

    def add_indexation_task(self, paths=None):
        dirname = self.get_search_dirname()
        if not dirname:
            return None
        uc = self.current_user.config
        if not uc or not uc.root_path:
            return None
        if not paths:
            paths = browser.get_all_files(self.extensions, uc.root_path, uc.root_path)[1]
        Task.create(search.do_index, [dirname, paths],
                    owner=str(self.current_user.iduser),
                    unique_key='search_%i' % self.current_user.iduser)

        # Since we commit the task we need to re-bound the user to the session
        # to make sure we can reuse self.logged_user
        if self.logged_user:
            # For example if we use ldap authentication, self.logged_user can
            # be None if the user is not in the DB.
            models.DBSession.add(self.logged_user)


class JSONBaseUserView(JSONView, BaseUserView):

    def __init__(self, request):
        JSONView.__init__(self, request)
        BaseUserView.__init__(self, request)
