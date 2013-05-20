import os
import logging
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.renderers import render
from ..models import User
from .. import browser
import xmltool
from urllib2 import HTTPError

log = logging.getLogger(__name__)


class JSONHTTPBadRequest(HTTPBadRequest): pass


@view_defaults(renderer='index.mak')
class Views(object):

    def __init__(self, request):
        self.request = request
        if (not request.root_path
            and request.matched_route.name != 'login_selection'):
            if self._is_json():
                raise JSONHTTPBadRequest('root path not defined')
            raise HTTPBadRequest('root path not defined')

    def _is_json(self):
        return self.request.matched_route.name.endswith('_json')

    def _response(self, dic):
        if self._is_json():
            return dic

        editor_login = None
        if self.request.session.get('editor_login'):
            editor_login = self.request.session.get('editor_login')
        elif self.request.root_path:
            editor_login = self.request.user.login

        if self.request.user.multiple_account():
            dic['logins'] = self.request.user.get_editable_logins(editor_login)
        dic['editor_login'] = editor_login or 'Account'
        return dic

    def _get_navigation(self):

        def get_data_href(path, key):
            return self.request.route_path(
                'home_json', _query=[(key, path)])

        def get_href(path, key):
            return self.request.route_path(
                'home', _query=[(key, path)])

        def get_file_data_href(path, key):
            return self.request.route_path(
                'edit_json', _query=[(key, path)])

        def get_file_href(path, key):
            return self.request.route_path(
                'edit', _query=[(key, path)])

        relpath = self.request.GET.get('path') or ''
        root_path = self.request.root_path
        abspath = browser.absolute_path(relpath, root_path)
        folders, filenames = browser.get_files(abspath)
        data = []
        if root_path != abspath:
            data += [(
                'previous',
                '..',
                get_data_href(os.path.dirname(relpath), 'path'),
                get_href(os.path.dirname(relpath), 'path')
            )]

        for folder in folders:
            data += [(
                'folder',
                folder,
                get_data_href(os.path.join(relpath, folder), 'path'),
                get_href(os.path.join(relpath, folder), 'path')
            )]

        for filename in filenames:
            data += [(
                'file',
                filename,
                get_file_data_href(os.path.join(relpath, filename),
                                   'filename'),
                get_file_href(os.path.join(relpath, filename), 'filename')
            )]

        return render('blocks/file_navigation.mak',
                      {'data': data, 'path': relpath},
                      self.request)

    def _get_breadcrumb(self, relpath, force_link=False):
        def get_data_href(path, key):
            return self.request.route_path(
                'home_json', _query=[(key, path)])

        def get_href(path, key):
            return self.request.route_path(
                'home', _query=[(key, path)])

        tple = []
        while relpath:
            name = os.path.basename(relpath)
            tple += [(name, relpath)]
            relpath = os.path.dirname(relpath)

        tple += [('root', '')]
        html = []
        for index, (name, relpath) in enumerate(reversed(tple)):
            if index == len(tple) - 1 and not force_link:
                html += ['<li class="active">%s</li>' % (name)]
            else:
                divider = ''
                if len(tple) > 1:
                    divider = '<span class="divider">/</span>'
                html += [(
                    '<li>'
                    '<a data-href="%s" href="%s">%s</a> '
                    '%s'
                    '</li>') % (
                        get_data_href(relpath, relpath),
                        get_href(relpath, relpath),
                        name,
                        divider
                    )]
        return ''.join(html)

    @view_config(route_name='home', renderer='index.mak', permission='edit')
    @view_config(route_name='home_json', renderer='json', permission='edit')
    def home(self):
        path = self.request.GET.get('path') or ''
        return self._response({
            'content': self._get_navigation(),
            'breadcrumb': self._get_breadcrumb(path)
        })

    @view_config(route_name='login_selection', renderer='index.mak',
                 permission='edit')
    def login_selection(self):
        logins = self.request.user.get_editable_logins()
        login = self.request.GET.get('login')
        if not login or login not in logins:
            raise HTTPBadRequest('Invalid login')

        user = User.query.filter_by(login=login).one()
        self.request.session['editor_login'] = user.login
        self.request.session['root_path'] = user.config.root_path
        return HTTPFound(location='/')

    @view_config(route_name='edit', renderer='index.mak', permission='edit')
    @view_config(route_name='edit_json', renderer='json', permission='edit')
    def edit(self):
        filename = self.request.GET.get('filename') or ''
        if not filename:
            return {
                'error_msg': 'A filename should be provided',
            }
        root_path = self.request.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            html = xmltool.generate_form(absfilename, form_filename=filename)
        except HTTPError, e:
            log.exception(e)
            return {
                'error_msg': 'The dtd of %s can\'t be loaded.' % filename
            }
        except Exception, e:
            log.exception(e)
            return {
                'error_msg': str(e)
            }
        breadcrumb = self._get_breadcrumb(filename)
        return {
            'content': html,
            'breadcrumb': breadcrumb
        }


@view_config(context=JSONHTTPBadRequest, renderer='json', route_name=None)
@view_config(context=HTTPBadRequest, renderer='index.mak', route_name=None)
def bad_request(request):
    if not request.user.multiple_account():
        return {'content': 'There is a problem with your configuration, '
                'please contact your administrator with '
                'the following message: Edit the user named \'%s\' '
                'and set the root_path in the config.' % request.user.login}

    logins = request.user.get_editable_logins()
    content = render('blocks/login_selection.mak', {'logins': logins}, request)
    return {'content': content}


def includeme(config):
    config.add_route('home', '/')
    config.add_route('home_json', '/home.json')
    config.add_route('login_selection', '/login-selection')
    config.add_route('edit', '/edit')
    config.add_route('edit_json', '/edit.json')
    config.scan(__name__)
