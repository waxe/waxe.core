import os.path
import pyramid_logging
import xmltool
from pyramid.renderers import render
from pyramid.view import view_config
import pyramid.httpexceptions as exc
from waxe.core import browser
from waxe.core import models
from waxe.core.utils import escape_entities
from ..base import BaseUserView
from . import helper


log = pyramid_logging.getLogger(__name__)


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

    @view_config(route_name='versioning_short_status_json', permission='edit')
    def short_status(self):
        """Status of the given path without any depth.
        """
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        dic = {}
        for o in vobj.status(relpath):
            dic[o.relpath] = o.status
        return dic

    @view_config(route_name='versioning_status_json', permission='edit')
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

        conflicteds = [{
            'relpath': 'debug/dash.xml',
            'status': 'unversioned',
        }]
        dic = {
            'conflicteds': conflicteds,
            'uncommitables': uncommitables,
            'others': others
        }
        return dic

    @view_config(route_name='versioning_diff_json', permission='edit')
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

    @view_config(route_name='versioning_full_diff_json', permission='edit')
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
            lis += vobj.full_diff(filename)
            absfilename = browser.absolute_path(filename, self.root_path)
            if can_commit and not self.can_commit(absfilename):
                can_commit = False

        content = render('blocks/versioning_full_diff.mak', {
            'files': lis,
            'can_commit': can_commit,
        }, self.request)
        return content

    @view_config(route_name='versioning_update_json', permission='edit')
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

        absfilenames = [f for (status, f) in filenames]
        files = [(status, browser.relative_path(f, self.root_path))
                 for status, f in filenames]

        self.add_indexation_task(absfilenames)
        content = render('blocks/versioning_update.mak', {
            'files': files,
            'STATUS_ADDED': helper.STATUS_ADDED,
            'STATUS_MODIFED': helper.STATUS_MODIFED,
        }, self.request)
        return content

    @view_config(route_name='versioning_commit_json', permission='edit')
    def commit(self):
        msg = self.request.POST.get('msg')
        filenames = self.request.POST.getall('path')
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

    @view_config(route_name='versioning_update_texts_json', permission='edit')
    def update_texts(self):
        params = xmltool.utils.unflatten_params(self.request.POST)
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
                obj.write(absfilename, transform=self._get_xmltool_transform())
                files += [filename]
                absfilenames += [absfilename]
            except Exception, e:
                status = False
                error_msgs += ['%s: %s' % (filename, str(e))]

        if not status:
            raise exc.HTTPClientError('<br />'.join(error_msgs))

        self.add_indexation_task(absfilenames)
        return 'Files updated'

    @view_config(route_name='versioning_edit_conflict_json', permission='edit')
    def edit_conflict(self):
        """
        Basically it's the same function as editor.edit_text
        """
        filename = self.request.GET.get('path')
        if not filename:
            raise exc.HTTPClientError('No filename given')

        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            content = open(absfilename, 'r').read()
            content = content.decode('utf-8')
        except Exception, e:
            log.exception(e, request=self.request)
            raise exc.HTTPClientError(str(e))

        content = escape_entities(content)

        html = u'<form data-action="%s" action="%s" method="POST">' % (
            self.request.custom_route_path('versioning_update_conflict_json'),
            self.request.custom_route_path('versioning_update_conflict'),
        )
        html += u'<input type="hidden" id="_xml_filename" name="filename" value="%s" />' % filename
        html += u'<textarea class="codemirror" name="filecontent">%s</textarea>' % content
        html += u'<input type="submit" value="Save and resolve conflict" />'
        html += u'</form>'

        return html

    @view_config(route_name='versioning_update_conflict_json',
                 permission='edit')
    def update_conflict(self):
        # TODO: we should have an event 'save' to fix the conflict if okay
        filecontent = self.request.POST.get('filecontent')
        filename = self.request.POST.get('filename') or ''
        if not filecontent or not filename:
            raise exc.HTTPClientError('Missing parameters!')

        absfilename = browser.absolute_path(filename, self.root_path)
        try:
            obj = xmltool.load_string(filecontent)
            obj.write(absfilename, transform=self._get_xmltool_transform())
        except Exception, e:
            raise exc.HTTPClientError(
                'The conflict is not resolved: %s' % str(e))

        vobj = self.get_versioning_obj()
        try:
            vobj.resolve(filename)
        except Exception, e:
            log.exception(e, request=self.request)
            raise exc.HTTPClientError(
                'Conflict\'s resolution failed: %s' % str(e))
        self.add_indexation_task([absfilename])
        return 'Conflict fixed'

    @view_config(route_name='versioning_revert_json', permission='edit')
    def revert(self):
        filenames = self.request.POST.get('paths')
        if not filenames:
            filename = self.request.GET.get('path')
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
            vobj.revert(filename)
            absfilename = browser.absolute_path(filename, self.root_path)
            self.add_indexation_task([absfilename])

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
