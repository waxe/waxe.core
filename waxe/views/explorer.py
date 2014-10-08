import os
import math
from itertools import izip_longest
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from base import BaseUserView
import webhelpers.paginate as paginate
from webhelpers.html import HTML
from .. import browser, search as mod_search


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

    def _get_navigation_data(self, relpath, folder_route='explore',
                             file_route='edit',
                             file_data_href_name='data-href',
                             folder_data_href_name='data-href',
                             folder_only=False
                            ):

        root_path = self.root_path
        abspath = browser.absolute_path(relpath, root_path)
        folders, filenames = browser.get_files(abspath, root_path,
                                               relative=True)
        data = {
            'previous_tag': None,
            'tags': [],
        }
        if root_path != abspath:
            data['previous_tag'] = self._generate_link_tag(
                name='..',
                relpath=os.path.dirname(relpath),
                route_name=folder_route,
                data_href_name=folder_data_href_name,
            )

        tags = []
        for folder in folders:
            tag = self._generate_link_tag(
                name=os.path.basename(folder),
                relpath=folder,
                route_name=folder_route,
                data_href_name=folder_data_href_name,
                extra_attrs=[
                    ('data-relpath', folder),
                    ('class', 'folder'),
                ]
            )
            tags += [('folder', tag)]

        if not folder_only:
            for filename in filenames:
                tag = self._generate_link_tag(
                    name=os.path.basename(filename),
                    relpath=filename,
                    route_name=file_route,
                    data_href_name=file_data_href_name,
                    extra_attrs=[
                        ('data-relpath', filename),
                        ('class', 'file')
                    ])
                tags += [('file-excel', tag)]

        # Create 2 list: left and right columns
        n = int(math.ceil(len(tags) / 2.0))
        z = izip_longest(tags[:n], tags[n:])
        data['tags'] = z
        return data

    def _get_navigation(self):
        relpath = self.request.GET.get('path') or ''
        data = self._get_navigation_data(relpath)
        versioning_status_url = None
        if self.has_versioning():
            versioning_status_url = self.request.custom_route_path(
                'versioning_short_status_json',
                _query=[('path', relpath)])

        content = render(
            'blocks/folder-content.mak',
            data,
            self.request)
        return render('blocks/file_navigation.mak',
                      {'content': content,
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
    def folder_content(self, file_route='edit', folder_route='folder_content',
                       relpath=None, rootpath=None, folder_only=False):
        if relpath is None:
            relpath = self.request.GET.get('path') or ''
        data = self._get_navigation_data(
            file_route=file_route,
            folder_route=folder_route,
            folder_data_href_name='data-modal-href',
            file_data_href_name='data-href',
            relpath=relpath,
            folder_only=folder_only,
        )

        content = render(
            'blocks/folder-content.mak',
            data,
            self.request)
        return self._response({
            'content': content,
            'breadcrumb': self._get_breadcrumb(
                relpath,
                rootpath=rootpath,
                route_name=folder_route,
                data_href_name='data-modal-href'
            )
        })

    @view_config(route_name='open_json', renderer='json', permission='edit')
    def open(self):
        modal = render(
            'blocks/open_modal.mak',
            self.folder_content(),
            self.request)

        return self._response({'modal': modal})


    @view_config(route_name='open_template_content_json', renderer='json', permission='edit')
    def open_template_content(self, relpath=None):
        if relpath is None:
            relpath = self.request.GET.get('path', '')
        rootpath = browser.relative_path(
            self.current_user.config.root_template_path,
            self.root_path,
        )
        dic = self.folder_content(
            file_route='new',
            folder_route='open_template_content',
            relpath=relpath,
            rootpath=rootpath,
        )
        return self._response(dic)

    @view_config(route_name='open_template_json', renderer='json', permission='edit')
    def open_template(self):
        relpath = browser.relative_path(
            self.current_user.config.root_template_path,
            self.root_path,
        )
        modal = render(
            'blocks/open_modal.mak',
            self.open_template_content(relpath=relpath),
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
            os.mkdir(abspath)
        except Exception, e:
            return {'error_msg': str(e)}
        return self.saveas_content(relpath=relpath)

    @view_config(route_name='search_folder_content', renderer='index.mak', permission='edit')
    @view_config(route_name='search_folder_content_json', renderer='json', permission='edit')
    def search_folder_content(self, relpath=None):
        if relpath is None:
            relpath = self.request.GET.get('path', '')
        dic = self.folder_content(
            file_route=None,
            folder_route='search_folder_content',
            folder_only=True,
            relpath=relpath)

        dic['relpath'] = relpath
        return self._response(dic)

    @view_config(route_name='search_folder_json', renderer='json', permission='edit')
    def search_folder(self):
        modal = render('blocks/search_folder_modal.mak',
                       self.search_folder_content(),
                       self.request)
        return self._response({'modal': modal})

    @view_config(route_name='search', renderer='index.mak', permission='edit')
    @view_config(route_name='search_json', renderer='json', permission='edit')
    def search(self):

        def search_url(page, json=False):
            """Use for the BootstrapPage object
            """
            routename = 'search'
            if json:
                routename += '_json'
            return self.request.custom_route_path(
                routename,
                _query=[('search', search),
                        ('page', page)])

        dirname = self.get_search_dirname()
        if not dirname or not os.path.exists(dirname):
            return self._response({'error_msg': 'The search is not available'})

        dic = {
            'search': '',
            'relpath': '',
            'result': '',
        }
        if self.request.params.get('search'):
            search = self.request.params.get('search')
            path = self.request.params.get('path', '')
            p = self.request.params.get('page') or 1
            try:
                p = int(p)
            except ValueError:
                p = 1
            dic['search'] = search
            dic['relpath'] = path
            abspath = None
            if path:
                abspath = browser.absolute_path(path, self.root_path)
            res, nb_hits = mod_search.do_search(
                dirname, search, abspath=abspath, page=p)
            if not res:
                dic['result'] = 'No result!'
            else:
                lis = []
                for path, excerpt in res:
                    path = browser.relative_path(path, self.root_path)
                    lis += [(path, excerpt)]
                dic['data'] = lis
                dic['pageobj'] = BootstrapPage(
                    None, p, item_count=nb_hits, url=search_url,
                    items_per_page=mod_search.HITS_PER_PAGE)
        content = render('blocks/search.mak',
                         dic,
                         self.request)
        return self._response({'content': content})


def includeme(config):
    config.add_route('home', '/')
    config.add_route('home_json', '/home.json')
    config.add_route('explore', '/explore')
    config.add_route('explore_json', '/explore.json')
    config.add_route('folder_content', '/folder-content')
    config.add_route('folder_content_json', '/folder-content.json')
    config.add_route('open_json', '/open.json')
    config.add_route('open_template_json', '/open-template.json')
    config.add_route('open_template_content', '/open-template-content')
    config.add_route('open_template_content_json', '/open-template-content.json')
    config.add_route('saveas_content', '/saveas-content')
    config.add_route('saveas_content_json', '/saveas-content.json')
    config.add_route('saveas_json', '/saveas.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.add_route('search', '/search')
    config.add_route('search_json', '/search.json')
    config.add_route('search_folder_json', '/search-folder.json')
    config.add_route('search_folder_content', '/search-folder-content')
    config.add_route('search_folder_content_json', '/search-folder-content.json')
    config.scan(__name__)
