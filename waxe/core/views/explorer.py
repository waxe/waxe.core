import os
from pyramid.view import view_config
import pyramid.httpexceptions as exc
from base import JSONBaseUserView
from .. import browser, search as mod_search


class ExplorerView(JSONBaseUserView):

    @view_config(route_name='explore_json', permission='edit')
    def explore(self):
        """Get the files and the folders for the given path
        """
        path = self.req_get.get('path') or ''
        root_path = self.root_path
        abspath = browser.absolute_path(path, root_path)
        try:
            folders, filenames = browser.get_files(self.extensions, abspath,
                                                   root_path, relative=True)
        except IOError, e:
            # TODO: make sure we don't have absolute url in the error message.
            raise exc.HTTPNotFound(str(e))

        lis = []

        for folder in folders:
            lis += [{
                'name': os.path.basename(folder),
                'type': 'folder',
                'link': folder,
                # status will be updated in js
                'status': None,
            }]
        for filename in filenames:
            lis += [{
                'name': os.path.basename(filename),
                'type': 'file',
                'link': filename,
                # status will be updated in js
                'status': None,
            }]
        return lis

    @view_config(route_name='create_folder_json', permission='edit')
    def create_folder(self):
        path = self.req_post.get('path', '')
        name = self.req_post.get('name', None)

        if not name:
            raise exc.HTTPClientError('No name given')

        relpath = os.path.join(path, name)
        root_path = self.root_path
        abspath = browser.absolute_path(relpath, root_path)
        try:
            os.mkdir(abspath)
        except Exception, e:
            # TODO: make sure we don't have abolute url in the message
            raise exc.HTTPInternalServerError(str(e))

        # Return same data as in explore to insert this item in angular list
        # directly
        return {
            'name': name,
            'type': 'folder',
            'link': relpath
        }

    @view_config(route_name='search_json', permission='edit')
    def search(self):
        dirname = self.get_search_dirname()
        if not dirname or not os.path.exists(dirname):
            raise exc.HTTPInternalServerError('The search is not available')

        search = self.req_get.get('search')
        if not search:
            raise exc.HTTPClientError('Nothing to search')

        path = self.req_get.get('path', '')
        page_num = self.req_get.get('page') or 1
        try:
            page_num = int(page_num)
        except ValueError:
            page_num = 1

        abspath = None
        if path:
            abspath = browser.absolute_path(path, self.root_path)
        res, nb_hits = mod_search.do_search(
            dirname, search, abspath=abspath, page=page_num)
        lis = []
        if res:
            for path, excerpt in res:
                path = browser.relative_path(path, self.root_path)
                lis += [(path, excerpt)]
        return {
            'results': lis,
            'nb_items': nb_hits,
            'items_per_page': mod_search.HITS_PER_PAGE,
        }

    @view_config(route_name='remove_json', permission='edit')
    def remove(self):
        # TODO: use DELETE method
        filenames = self.req_post_getall('paths')
        if not filenames:
            raise exc.HTTPClientError('No filename given')

        absfilenames = []
        errors = []
        for filename in filenames:
            absfilename = browser.absolute_path(filename, self.root_path)
            if not os.path.isfile(absfilename):
                errors += [filename]
            absfilenames += [absfilename]

        if errors:
            raise exc.HTTPClientError(
                "The following filenames don't exist: %s" % ', '.join(errors))

        for absfilename in absfilenames:
            os.remove(absfilename)
            self.add_indexation_task([absfilename])

        return True


def includeme(config):
    config.add_route('explore_json', '/explore.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.add_route('search_json', '/search.json')
    config.add_route('remove_json', '/remove.json')
    config.scan(__name__)
