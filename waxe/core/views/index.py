import urlparse
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
import pyramid.httpexceptions as exc
from pyramid.renderers import render
from ..models import User
from .. import models
from base import (
    BaseView,
    BaseUserView,
)


class IndexView(BaseView):

    @view_config(route_name='profile', permission='authenticated')
    def profile(self):
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


def includeme(config):
    config.add_route('profile', '/profile.json')
    config.scan(__name__)
