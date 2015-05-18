import os.path
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


class VersioningView(BaseUserView):

    def can_commit(self, path):
        """It's possible path didn't exist since we can commit deleted file
        """
        if self.user_is_admin():
            return True

        if self.user_is_editor():
            return True

        assert self.user_is_contributor(), 'You are not a contributor'

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
            if os.path.isdir(so.abspath):
                # For now don't allow action on folder
                continue
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
        content = ''
        if not lis:
            content = '<br />The file is not modified!'

        for l in lis:
            l = escape_entities(l)
            content += '<pre>%s</pre>' % l
            if vobj.status(relpath)[0].status == helper.STATUS_MODIFED:
                content += (
                    '<a data-confirm="Are you sure you want to revert '
                    'the modification applied to this file?" '
                    'class="btn btn-danger" '
                    'data-href="%s">Revert</a>'
                ) % self.request.custom_route_path(
                    'versioning_revert_json',
                    _query=[('path', relpath)])
            if self.can_commit(absfilename):
                content += (
                    '<a  class="btn btn-success" '
                    'style="margin-right: 10px;" '
                    'data-href="%s">Commit</a>'
                ) % self.request.custom_route_path(
                    'versioning_prepare_commit_json',
                    _query=[('path', relpath)])
        return content

    @view_config(route_name='versioning_full_diff_json')
    def full_diff(self):
        """Editable diff of all the files
        """
        filenames = self.request.GET.getall('paths')
        if not filenames:
            raise exc.HTTPClientError('No filename given')

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

        content = render('blocks/versioning_full_diff.mak', {
            'files': lis,
            'can_commit': can_commit,
        }, self.request)
        return content

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

        iduser_commit = None
        if self.logged_user.iduser != self.current_user.iduser:
            iduser_commit = self.logged_user.iduser
        for filename in filenames:
            self.current_user.add_commited_file(filename,
                                                iduser_commit=iduser_commit)
        return 'Files commited'

    @view_config(route_name='versioning_update_texts_json')
    def update_texts(self):
        params = xmltool.utils.unflatten_params(self.req_post)
        if 'data' not in params or not params['data']:
            raise exc.HTTPClientError('Missing parameters!')

        root_path = self.root_path
        status = True
        error_msgs = []
        files = []
        absfilenames = []
        for dic in params['data']:
            filecontent = dic['filecontent']
            filename = dic['filename']
            absfilename = browser.absolute_path(filename, root_path)
            try:
                obj = xmltool.load_string(filecontent)
                obj.write(absfilename,
                          transform=self.request.xmltool_transform)
                files += [filename]
                absfilenames += [absfilename]
            except Exception, e:
                status = False
                error_msgs += ['%s: %s' % (filename, str(e))]

        if not status:
            raise exc.HTTPClientError('<br />'.join(error_msgs))

        events.trigger('updated', view=self, paths=files)
        return 'Files updated'

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
        for filename in filenames:
            absfilename = browser.absolute_path(filename, self.root_path)
            if not os.path.isfile(absfilename):
                # TODO: concat error message and return it
                errors += ['File %s doesn\'t exist' % filename]

        if errors:
            raise exc.HTTPClientError('<br />'.join(errors))

        for filename in filenames:
            # TODO: also check the file is versioned
            # If not versioned, remove it!
            absfilename = browser.absolute_path(filename, self.root_path)
            so = vobj.status(filename)[0]
            if so.status == helper.STATUS_UNVERSIONED:
                os.remove(absfilename)
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
    config.add_route('versioning_update_texts_json', '/update-texts.json')
    config.add_route('versioning_edit_conflict_json', 'edit-conflict.json')
    config.add_route('versioning_update_conflict_json', 'update-conflict.json')
    config.add_route('versioning_revert_json', '/revert.json')
    config.scan(__name__)

    events.on('updated_conflicted.txt', on_updated_conflicted)
