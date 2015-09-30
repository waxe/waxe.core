import os
import math
from itertools import izip_longest
from pyramid.view import view_config
import pyramid.httpexceptions as exc
from base import BaseUserView
from .. import browser, events


class FileManagerView(BaseUserView):

    @view_config(route_name='explore_json')
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
        # We want to order alphabetically by columns
        n = int(math.ceil(len(lis) / 2.0))
        return list(sum(izip_longest(lis[:n], lis[n:]), ()))

    @view_config(route_name='create_folder_json')
    def create_folder(self):
        path = self.req_post.get('path') or ''
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

    @view_config(route_name='remove_json')
    def remove(self):
        # TODO: use DELETE method
        # And also support to delete folder
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

        events.trigger('deleted', view=self, paths=filenames)
        return True


def includeme(config):
    config.add_route('explore_json', '/explore.json')
    config.add_route('create_folder_json', '/create-folder.json')
    config.add_route('remove_json', '/remove.json')
    config.scan(__name__)
