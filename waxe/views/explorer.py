import os
from subprocess import Popen, PIPE
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from base import BaseUserView
from .. import browser
from .. import search


class ExplorerView(BaseUserView):

    def _get_navigation_data(self, add_previous=False, folder_route='explore',
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
        folders, filenames = browser.get_files(abspath, root_path,
                                               relative=True)
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
                'data_relpath': folder,
                'name': os.path.basename(folder),
                'data_href': get_data_href(folder, 'path'),
            }
            if not only_json:
                dic['href'] = get_href(os.path.join(relpath, folder), 'path')
            data['folders'] += [dic]

        for filename in filenames:
            dic = {
                'data_relpath': filename,
                'name': os.path.basename(filename),
                'data_href': get_file_data_href(filename, 'path'),
            }
            if not only_json:
                dic['href'] = get_file_href(filename,
                                            'path')
            data['filenames'] += [dic]
        return data

    def _get_navigation(self):
        data = self._get_navigation_data(add_previous=True)
        versioning_status_url = None
        if self.has_versioning():
            versioning_status_url = self.request.custom_route_path(
                'versioning_short_status_json',
                _query=[('path', data['path'])])
        return render('blocks/file_navigation.mak',
                      {'data': data,
                       'versioning_status_url': versioning_status_url},
                      self.request)

    @view_config(route_name='home', renderer='index.mak', permission='edit')
    @view_config(route_name='home_json', renderer='json', permission='edit')
    def home(self):
        path = self.request.GET.get('path') or ''
        abspath = browser.absolute_path(path, self.root_path)
        if os.path.isfile(abspath):
            location = self.request.custom_route_path('edit')
            location += '?path=%s' % path
            return HTTPFound(location=location)
        return self.explore()

    @view_config(route_name='explore', renderer='index.mak', permission='edit')
    @view_config(route_name='explore_json', renderer='json', permission='edit')
    def explore(self):
        path = self.request.GET.get('path') or ''
        try:
            content = self._get_navigation()
        except IOError, e:
            return self._response({
                'error_msg': str(e),
            })
        return self._response({
            'content': content,
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

    @view_config(route_name='search', renderer='index.mak', permission='edit')
    @view_config(route_name='search_json', renderer='json', permission='edit')
    def search(self):
        s = self.request.POST.get('search')
        if not s:
            return {'error_msg': 'Nothing to search'}

        dirname = self.get_search_dirname()
        if not dirname or not os.path.exists(dirname):
            return {'error_msg': 'The search is not available'}

        res = search.do_search(dirname, s)
        if not res:
            return {'content': 'No result!'}
        lis = []
        for path, excerpt in res:
            path = browser.relative_path(path, self.root_path)
            href = self.request.custom_route_path('edit',
                                                  _query=[('path', path)])
            data_href = self.request.custom_route_path('edit_json',
                                                       _query=[('path', path)])
            lis += [(path, href, data_href, excerpt)]
        content = render('blocks/search.mak',
                         {'data': lis},
                         self.request)
        return {'content': content}


def includeme(config):
    config.add_route('home', '/')
    config.add_route('home_json', '/home.json')
    config.add_route('explore', '/explore')
    config.add_route('explore_json', '/explore.json')
    config.add_route('open_json', '/open.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.add_route('search', '/search')
    config.add_route('search_json', '/search.json')
    config.scan(__name__)
