import os.path
import shutil
import pyramid_logging
import xmltool
from pyramid.renderers import render
from pyramid.view import view_config
import pyramid.httpexceptions as exc
from waxe.core import browser, models, events
from waxe.core.utils import escape_entities
from ..base import BaseUserView
from . import helper


log = pyramid_logging.getLogger(__name__)


def on_updated_conflicted(view, path):
    vobj = view.get_versioning_obj()
    if not vobj:
        return

    try:
        vobj.resolve(path)
    except Exception, e:
        log.exception(e, request=view.request)
        raise exc.HTTPClientError(
            'Conflict\'s resolution failed: %s' % str(e))


def on_before_delete(view, paths):
    vobj = view.get_versioning_obj()
    if not vobj:
        return

    for path in paths:
        vobj.remove(path)

    return view, []


def on_before_move(view, paths, newpath):
    vobj = view.get_versioning_obj()
    if not vobj:
        return

    s = vobj.empty_status(newpath)
    if s.status not in [helper.STATUS_ADDED,
                        helper.STATUS_MODIFED,
                        helper.STATUS_NORMAL]:
        raise Exception(
            "Can't move file to destination. Please check destination status.")

    todo_paths = []
    for path in paths:
        if vobj.empty_status(path).status == helper.STATUS_UNVERSIONED:
            todo_paths += [path]
        else:
            vobj.move(path, newpath)

    return view, todo_paths, newpath


class VersioningView(BaseUserView):

    def can_commit(self, path):
        """It's possible path didn't exist since we can commit deleted file
        """
        if self.user_is_admin():
            return True

        if self.user_is_supervisor():
            return True

        if self.user_is_editor():
            if (self.logged_user.config.root_path and
                    path.startswith(self.logged_user.config.root_path)):
                # editor can whatever he wants in his account
                return True

        assert self.user_is_editor() or self.user_is_contributor()

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        path = os.path.normpath(path)

        paths = list(self.logged_user.versioning_paths)
        paths.sort(lambda a, b: cmp(len(a.path), len(b.path)))
        paths.reverse()
        for p in paths:
            if path.startswith(os.path.normpath(p.path)):
                if models.VERSIONING_PATH_STATUS_ALLOWED == p.status:
                    return True
                return False
        return False

    @view_config(route_name='versioning_short_status_json')
    def short_status(self):
        """Status of the given path without any depth.
        """
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        dic = {}
        for o in vobj.status(relpath):
            dic[o.relpath] = o.status
        return dic

    @view_config(route_name='versioning_status_json')
    def status(self, info_msg=None, error_msg=None):
        """Full status of the repo. We want to get all files
        """
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        lis = vobj.full_status(relpath)

        conflicteds = []
        conflicteds_abspath = []
        uncommitables = []
        tmps = []
        for so in lis:
            if so.status == helper.STATUS_CONFLICTED:
                conflicteds += [so.to_dict()]
                conflicteds_abspath += [so.abspath]
            elif self.can_commit(so.abspath):
                tmps += [so]
            else:
                uncommitables += [so]

        others = [so.to_dict() for so in tmps
                  if not helper.is_conflicted(so, conflicteds_abspath)]

        uncommitables = [so.to_dict() for so in uncommitables
                         if not helper.is_conflicted(so, conflicteds_abspath)]

        dic = {
            'conflicteds': conflicteds,
            'uncommitables': uncommitables,
            'others': others
        }
        return dic

    @view_config(route_name='versioning_diff_json')
    def diff(self):
        relpath = self.request.GET.get('path', '')
        if not relpath:
            raise exc.HTTPClientError('No filename given')

        absfilename = browser.absolute_path(relpath, self.root_path)
        if not os.path.isfile(absfilename):
            raise exc.HTTPClientError("File %s doesn't exist" % relpath)

        vobj = self.get_versioning_obj()
        lis = vobj.diff(relpath)
        if not lis:
            return {}

        content = ''
        for l in lis:
            content += escape_entities(l)

        return {
            'diff': content,
            'can_commit': self.can_commit(absfilename)
        }

    @view_config(route_name='versioning_full_diff_json')
    def full_diff(self):
        """Editable diff of all the files
        """
        req_filenames = self.request.GET.getall('paths')
        if not req_filenames:
            raise exc.HTTPClientError('No filename given')

        filenames = set()
        for f in req_filenames:
            absfilename = browser.absolute_path(f, self.root_path)
            if os.path.isdir(absfilename):
                folders, fnames = browser.get_files(
                    self.extensions, absfilename,
                    self.root_path, relative=True, root_only=False)
                filenames |= set(fnames)
            else:
                filenames.add(f)

        vobj = self.get_versioning_obj()
        lis = []
        can_commit = True
        for filename in filenames:
            lis += vobj.full_diff_content(filename)
            absfilename = browser.absolute_path(filename, self.root_path)
            if can_commit and not self.can_commit(absfilename):
                can_commit = False

        return {
            'diffs': lis,
            'can_commit': can_commit
        }

    @view_config(route_name='versioning_update_json')
    def update(self):
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        if vobj.has_conflict():
            raise exc.HTTPClientError(
                'You can\'t update the repository, '
                'you have to fix the conflicts first')

        try:
            # TODO: we should raise custom exception to handle it correctly
            filenames = vobj.update(relpath)
        except Exception, e:
            raise exc.HTTPClientError(
                'Fail to update the repository: %s.\n'
                'Please try again.' % str(e)
            )

        # TODO: we should add folder/file like in filemanager
        # TODO: don't know how to get type of deleted files/folders
        files = [
            {
                'status': status,
                'path': browser.relative_path(f, self.root_path),
                'addLink': status in [helper.STATUS_ADDED,
                                      helper.STATUS_MODIFED]
            } for status, f in filenames]

        events.trigger('updated',
                       view=self,
                       paths=[browser.relative_path(f, self.root_path)
                              for status, f in filenames])
        return files

    @view_config(route_name='versioning_commit_json')
    def commit(self):
        msg = self.req_post.get('msg')
        filenames = self.req_post_getall('paths')
        if not filenames:
            raise exc.HTTPClientError('No filename given')
        if not msg:
            raise exc.HTTPClientError('No commit message')

        errors = []
        for filename in filenames:
            absfilename = browser.absolute_path(filename, self.root_path)
            if not self.can_commit(absfilename):
                errors += [
                    'You don\'t have the permission to commit: %s' % filename]

        if errors:
            raise exc.HTTPClientError('<br />'.join(errors))

        vobj = self.get_versioning_obj(commit=True)
        try:
            # TODO: custom exception?
            vobj.commit(filenames, msg)
        except Exception, e:
            log.exception(e, request=self.request)
            raise exc.HTTPClientError(
                'Commit failed: %s' % str(e))

        for filename in filenames:
            self.add_commited_file(filename)
        return 'Files commited'

    @view_config(route_name='versioning_revert_json')
    def revert(self):
        filenames = self.req_post_getall('paths')
        if not filenames:
            filename = self.req_post.get('path')
            if filename:
                filenames = [filename]

        if not filenames:
            raise exc.HTTPClientError('No filename given')

        vobj = self.get_versioning_obj()
        errors = []
        versionings = {}
        for filename in filenames:
            absfilename = browser.absolute_path(filename, self.root_path)
            # Check if the file exists by doing a status since a file can be
            # deleted
            so = vobj.status(filename)
            if not so:
                errors += ['File %s doesn\'t exist' % filename]
            else:
                versionings[filename] = so[0]

        if errors:
            raise exc.HTTPClientError('<br />'.join(errors))

        for filename in filenames:
            absfilename = browser.absolute_path(filename, self.root_path)
            if versionings[filename].status == helper.STATUS_UNVERSIONED:
                if os.path.isdir(absfilename):
                    shutil.rmtree(absfilename)
                elif os.path.isfile(absfilename):
                    os.remove(absfilename)
                else:
                    # Since we don't check if a file is in a deleted directory
                    # we don't handle this case. (We already check later in
                    # this function if the file exists)
                    pass
            else:
                vobj.revert(filename)

        events.trigger('updated', view=self, paths=filenames)
        return 'Files reverted'


def includeme(config):
    config.add_route('versioning_short_status_json', '/short-status.json')
    config.add_route('versioning_status_json', '/status.json')
    config.add_route('versioning_diff_json', '/diff.json')
    config.add_route('versioning_status_post_json', '/status-post.json')
    config.add_route('versioning_full_diff_json', '/full-diff.json')
    config.add_route('versioning_update_json', '/update.json')
    config.add_route('versioning_commit_json', '/commit.json')
    config.add_route('versioning_prepare_commit_json', '/prepare-commit.json')
    config.add_route('versioning_edit_conflict_json', 'edit-conflict.json')
    config.add_route('versioning_update_conflict_json', 'update-conflict.json')
    config.add_route('versioning_revert_json', '/revert.json')
    config.scan(__name__)

    events.on('updated_conflicted.txt', on_updated_conflicted)
    events.on('before_delete', on_before_delete)
    events.on('before_move', on_before_move)
