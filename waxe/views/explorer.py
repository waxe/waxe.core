import os
import logging
from subprocess import Popen, PIPE
from pyramid.view import view_config
from pyramid.renderers import render
from base import BaseUserView
from .. import browser

log = logging.getLogger(__name__)


class ExplorerView(BaseUserView):

    def _get_navigation_data(self, add_previous=False, folder_route='home',
                             file_route='edit', only_json=False):

        def get_data_href(path, key):
            return self.request.custom_route_path(
                '%s_json' % folder_route, _query=[(key, path)])

        def get_href(path, key):
            return self.request.custom_route_path(
                folder_route, _query=[(key, path)])

        def get_file_data_href(path, key):
            return self.request.custom_route_path(
                '%s_json' % file_route, _query=[(key, path)])

        def get_file_href(path, key):
            return self.request.custom_route_path(
                file_route, _query=[(key, path)])

        relpath = self.request.GET.get('path') or ''
        root_path = self.root_path
        abspath = browser.absolute_path(relpath, root_path)
        folders, filenames = browser.get_files(abspath, root_path)
        data = {
            'folders': [],
            'filenames': [],
            'previous': None,
            'path': relpath,
        }
        if add_previous and root_path != abspath:
            data['previous'] = {
                'name': '..',
                'data_href': get_data_href(os.path.dirname(relpath), 'path'),
            }
            if not only_json:
                data['previous']['href'] = get_href(os.path.dirname(relpath), 'path')

        for folder in folders:
            dic = {
                'name': folder,
                'data_href': get_data_href(os.path.join(relpath, folder), 'path'),
            }
            if not only_json:
                dic['href'] = get_href(os.path.join(relpath, folder), 'path')
            data['folders'] += [dic]

        for filename in filenames:
            dic = {
                'name': filename,
                'data_href': get_file_data_href(os.path.join(relpath, filename),
                                                'filename'),
            }
            if not only_json:
                dic['href'] = get_file_href(os.path.join(relpath, filename), 'filename')
            data['filenames'] += [dic]
        return data

    def _get_navigation(self):
        data = self._get_navigation_data(add_previous=True)
        return render('blocks/file_navigation.mak',
                      {'data': data}, self.request)

    @view_config(route_name='home', renderer='index.mak', permission='edit')
    @view_config(route_name='home_json', renderer='json', permission='edit')
    def home(self):
        path = self.request.GET.get('path') or ''
        return self._response({
            'content': self._get_navigation(),
            'breadcrumb': self._get_breadcrumb(path)
        })

    @view_config(route_name='open_json', renderer='json', permission='edit')
    def open(self):
        data = self._get_navigation_data(folder_route='open', only_json=True)
        relpath = self.request.GET.get('path') or ''
        bdata = self._get_breadcrumb_data(relpath)
        lis = []

        def get_data_href(path, key):
            return self.request.custom_route_path(
                'open_json', _query=[(key, path)])
        for name, path in bdata:
            lis += [{
                'name': name,
                'data_href': get_data_href(path, 'path')
            }]
        data['nav_btns'] = lis
        return data

    @view_config(route_name='create_folder_json', renderer='json', permission='edit')
    def create_folder(self):
        path = self.request.GET.get('path', None)

        if not path:
            return {'status': False, 'error_msg': 'No path given'}

        root_path = self.root_path
        abspath = browser.absolute_path(path, root_path)
        process = Popen(['mkdir', abspath], stdout=PIPE, stderr=PIPE)
        error = process.stderr.read()
        if error:
            return {'status': False, 'error_msg': error}
        return {'status': True}


def includeme(config):
    config.add_route('home', '/')
    config.add_route('home_json', '/home.json')
    config.add_route('open_json', '/open.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.scan(__name__)
