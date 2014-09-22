import os
from subprocess import Popen, PIPE
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from base import BaseUserView
import webhelpers.paginate as paginate
from webhelpers.html import HTML
from .. import browser, search


class BootstrapPage(paginate.Page):
    # TODO: support to have 'class="active"' on current <li>

    def pager(self, *args, **kw):
        kw['separator'] = '</li><li>'
        html = super(BootstrapPage, self).pager(*args, **kw)
        return '<ul class="pagination"><li>%s</li></ul>' % html

    def _pagerlink(self, page, text):
        """
        Same function as in webhelpers.paginate.Page: just simplify it and
        support data-href and assume url_generator is defined
        """
        link_params = {}
        link_params.update(self.kwargs)
        link_params.update(self.pager_kwargs)
        link_params[self.page_param] = page
        # Create the URL to load a certain page
        link_url = self._url_generator(**link_params)
        data_link_url = self._url_generator(json=True, **link_params)
        link_attr = self.link_attr.copy()
        link_attr['data-href'] = data_link_url
        return HTML.a(text, href=link_url, **link_attr)


class ExplorerView(BaseUserView):

    def _get_navigation_data(self, add_previous=False, folder_route='explore',
                             file_route='edit', data_href_name='data-href',
                             only_json=False, relpath=None):

        def get_data_href(path, key):
            if folder_route is None:
                return ''
            return self.request.custom_route_path(
                '%s_json' % folder_route, _query=[(key, path)])

        def get_href(path, key):
            if folder_route is None:
                return ''
            return self.request.custom_route_path(
                folder_route, _query=[(key, path)])

        def get_file_data_href(path, key):
            if file_route is None:
                return ''
            return self.request.custom_route_path(
                '%s_json' % file_route, _query=[(key, path)])

        def get_file_href(path, key):
            if file_route is None:
                return ''
            return self.request.custom_route_path(
                file_route, _query=[(key, path)])

        if relpath is None:
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
                'link_tag': self._generate_link_tag(
                    name='..',
                    relpath=os.path.dirname(relpath),
                    route_name=folder_route,
                    data_href_name=data_href_name,
                )
            }
            if not only_json:
                data['previous']['href'] = get_href(os.path.dirname(relpath), 'path')

        for folder in folders:
            dic = {
                'data_relpath': folder,
                'name': os.path.basename(folder),
                'data_href': get_data_href(folder, 'path'),
                'link_tag': self._generate_link_tag(
                    name=os.path.basename(folder),
                    relpath=folder,
                    route_name=folder_route,
                    data_href_name=data_href_name,
                    extra_attrs=[
                        ('data-relpath', folder),
                        ('class', 'folder'),
                    ]
                )
            }
            if not only_json:
                dic['href'] = get_href(folder, 'path')
            data['folders'] += [dic]

        for filename in filenames:
            dic = {
                'data_relpath': filename,
                'name': os.path.basename(filename),
                'data_href': get_file_data_href(filename, 'path'),
                'link_tag': self._generate_link_tag(
                    name=os.path.basename(filename),
                    relpath=filename,
                    route_name=file_route,
                    data_href_name=data_href_name,
                    extra_attrs=[
                        ('data-relpath', filename),
                        ('class', 'file')
                    ])
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
                       'last_files': self._get_last_files(),
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

    @view_config(route_name='folder_content', renderer='index.mak', permission='edit')
    @view_config(route_name='folder_content_json', renderer='json', permission='edit')
    def folder_content(self, file_route='edit', folder_route='folder_content', relpath=None):
        if relpath is None:
            relpath = self.request.GET.get('path') or ''
        data = self._get_navigation_data(
            add_previous=True,
            file_route=file_route,
            folder_route=folder_route,
            data_href_name='data-modal-href',
            relpath=relpath,
            only_json=True)

        content = render(
            'blocks/folder-content.mak',
            data,
            self.request)
        return self._response({
            'content': content,
            'breadcrumb': self._get_breadcrumb(
                relpath,
                route_name=folder_route,
                data_href_name='data-modal-href'
            )
        })

    @view_config(route_name='open_json', renderer='json', permission='edit')
    def open(self):
        modal = render('blocks/open_modal.mak',
                       self.folder_content(),
                       self.request)

        return self._response({'modal': modal})

    @view_config(route_name='saveas_content', renderer='index.mak', permission='edit')
    @view_config(route_name='saveas_content_json', renderer='json', permission='edit')
    def saveas_content(self, relpath=None):
        if relpath is None:
            relpath = self.request.GET.get('path', '')
        dic = self.folder_content(
            file_route=None,
            folder_route='saveas_content',
            relpath=relpath)

        # TODO: not really nice, we should put this in a template
        dic['content'] += (
            '<br />'
            '<br />'
            '<br />'
            '<form class="form-saveas form-inline">'
            '  <input type="hidden" name="path" value="%s" />'
            '<div class="form-group">'
            '  <label>Filename:</label><br />'
            '  <input type="text" class="form-control" name="name" required="required" style="width: auto;" />'
            '  <input type="submit" class="btn btn-primary" value="Save as" />'
            '</div>'
            '</form>'
            '<br />'
            '<hr />'
            '<br />'
            '<form data-modal-action="%s" class="form-inline">'
            '  <input type="hidden" name="path" value="%s" />'
            '  <div class="form-group">'
            '    <label>Create a new folder:</label><br />'
            '    <input type="text" name="name" class="form-control" required="required" style="width: auto;" />'
            '    <input type="submit" class="btn btn-default" value="Create" />'
            '  </div>'
            '</form>'
        ) % (
            relpath,
            self.request.custom_route_path('create_folder_json'),
            relpath
        )
        return self._response(dic)

    @view_config(route_name='saveas_json', renderer='json', permission='edit')
    def saveas(self):
        modal = render('blocks/saveas_modal.mak',
                       self.saveas_content(),
                       self.request)

        return self._response({'modal': modal})

    @view_config(route_name='create_folder_json', renderer='json', permission='edit')
    def create_folder(self):
        path = self.request.POST.get('path', '')
        name = self.request.POST.get('name', None)

        if not name:
            return {'error_msg': 'No name given'}

        relpath = os.path.join(path, name)
        root_path = self.root_path
        abspath = browser.absolute_path(relpath, root_path)
        try:
            error = None
            os.mkdir(abspath)
        except Exception, e:
            error = str(e)
        if error:
            return {'error_msg': error}
        return self.saveas_content(relpath=relpath)

    @view_config(route_name='search', renderer='index.mak', permission='edit')
    @view_config(route_name='search_json', renderer='json', permission='edit')
    def search(self):
        s = self.request.params.get('search')
        if not s:
            return self._response({'error_msg': 'Nothing to search'})

        dirname = self.get_search_dirname()
        if not dirname or not os.path.exists(dirname):
            return self._response({'error_msg': 'The search is not available'})

        p = self.request.params.get('page') or 1
        try:
            p = int(p)
        except ValueError:
            p = 1

        res, nb_hits = search.do_search(dirname, s, p)
        if not res:
            return self._response({'content': 'No result!'})
        lis = []
        for path, excerpt in res:
            path = browser.relative_path(path, self.root_path)
            href = self.request.custom_route_path('edit',
                                                  _query=[('path', path)])
            data_href = self.request.custom_route_path('edit_json',
                                                       _query=[('path', path)])
            lis += [(path, href, data_href, excerpt)]

        def search_url(page, json=False):
            routename = 'search'
            if json:
                routename += '_json'
            return self.request.custom_route_path(routename,
                                                  _query=[('search', s),
                                                          ('page', page)])

        pageobj = BootstrapPage(None, p, item_count=nb_hits, url=search_url,
                                items_per_page=search.HITS_PER_PAGE)
        content = render('blocks/search.mak',
                         {
                             'data': lis,
                             'pageobj': pageobj,
                             'search_url': search_url,
                         },
                         self.request)
        return self._response({'content': content})

    def _get_last_files(self):
        opened_files = self.current_user.opened_files[::-1]
        commited_files = self.current_user.commited_files[::-1]
        html = render('blocks/last_files.mak',
                      {'opened_files': opened_files,
                       'commited_files': commited_files},
                      self.request)
        return html


def includeme(config):
    config.add_route('home', '/')
    config.add_route('home_json', '/home.json')
    config.add_route('explore', '/explore')
    config.add_route('explore_json', '/explore.json')
    config.add_route('folder_content', '/folder-content')
    config.add_route('folder_content_json', '/folder-content.json')
    config.add_route('open_json', '/open.json')
    config.add_route('saveas_content', '/saveas-content')
    config.add_route('saveas_content_json', '/saveas-content.json')
    config.add_route('saveas_json', '/saveas.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.add_route('search', '/search')
    config.add_route('search_json', '/search.json')
    config.scan(__name__)
