import urlparse
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
import pyramid.httpexceptions as exc
from pyramid.renderers import render
from ..models import User
from .. import browser
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
        return self.logged_user_profile()

    @view_config(route_name='last_files', permission='authenticated')
    def last_files(self):
        if not self.current_user:
            # User is authenticated but not in the DB
            return {}
        opened_files = self.current_user.opened_files[::-1]
        opened_files = [
            {'path': f.path,
             'user': f.user_owner and f.user_owner.login or ''}
            for f in opened_files]
        commited_files = self.current_user.commited_files[::-1]
        commited_files = [
            {'path': f.path,
             'user': f.user_owner and f.user_owner.login or ''}
            for f in commited_files]
        return {
            'opened_files': opened_files,
            'commited_files': commited_files
        }


class IndexUserView(BaseUserView):

    @view_config(route_name='account_profile', permission='edit')
    def account_profile(self):
        """Get the profile of the user
        """
        config = self.current_user.config
        if not config:
            return {}
        templates_path = None
        if config.root_template_path:
            templates_path = browser.relative_path(config.root_template_path,
                                                   self.root_path)

        editors = {}
        for exts, editor in self.request.registry.settings['waxe_editors']:
            for ext in exts:
                editors[ext] = editor.ROUTE_PREFIX

        renderers = {}
        for exts, waxe_render in self.request.registry.settings['waxe_renderers']:
            for ext in exts:
                renderers[ext] = waxe_render.ROUTE_PREFIX

        dic = {
            'login': self.current_user.login,
            'has_template_files': bool(config.root_template_path),
            'templates_path': templates_path,
            'has_versioning': self.has_versioning(),
            'has_search': ('whoosh.path' in self.request.registry.settings),
            'has_xml_renderer': ('waxe.renderers' in
                                 self.request.registry.settings),
            'dtd_urls': self.request.registry.settings['dtd_urls'].split(),
            'editors': editors,
            'renderers': renderers,
        }
        res = {'account_profile': dic}
        if self.req_get.get('full'):
            res['user_profile'] = self.logged_user_profile()
        return res


def includeme(config):
    config.add_route('profile', '/profile.json')
    config.add_route('last_files', '/last-files.json')
    # TODO: remove hardcoding path
    config.add_route('account_profile',
                     '/account/{login}/account-profile.json')
    config.scan(__name__)
