import os.path
import logging
import pysvn
import xmltool
from pyramid.renderers import render
from waxe import browser
from waxe import diff
from waxe import models
from waxe.utils import unflatten_params
from ..base import BaseUserView
from . import helper


log = logging.getLogger(__name__)

# Use to defined the color we will display the status
labels_mapping = {
    pysvn.wc_status_kind.unversioned: 'label-default',
    pysvn.wc_status_kind.modified: 'label-info',
    pysvn.wc_status_kind.conflicted: 'label-danger',
}


def svn_ssl_server_trust_prompt(trust_dict):
    return True, trust_dict['failures'], False


class PysvnView(BaseUserView):

    def can_commit(self, path):
        if not os.path.exists(path):
            raise Exception('Invalid path %s' % path)

        if self.user_is_admin():
            return True

        if self.user_is_editor():
            return True

        assert self.user_is_contributor(), 'You are not a contributor'

        if os.path.isfile(path):
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

    def get_svn_login(self):
        auth = False
        if 'versioning.auth.active' in self.request.registry.settings:
            auth = True

        editor_login = self.current_user.login
        if not auth:
            # No auth, no need to find a password
            return False, str(editor_login), None, False

        pwd = self.request.registry.settings.get('versioning.auth.pwd')
        if not pwd:
            pwd = self.current_user.config.versioning_password

        if not pwd:
            # TODO: a good idea should be to ask the password to the user
            raise Exception('No versioning password set for %s' % editor_login)

        return auth, str(editor_login), pwd, False

    def get_svn_client(self):
        client = pysvn.Client()
        # Set the username in case there is no authentication
        client.set_default_username(str(self.current_user.login))
        client.callback_get_login = lambda *args, **kw: self.get_svn_login()
        if self.request.registry.settings.get('versioning.auth.https'):
            client.callback_ssl_server_trust_prompt = svn_ssl_server_trust_prompt
        return client

    def get_versioning_obj(self):
        client = self.get_svn_client()
        return helper.PysvnVersioning(client, self.root_path)

    def short_status(self):
        """Status of the given path without any depth.

        This function should only be called in json
        """
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        dic = {}
        for o in vobj.status(relpath):
            dic[o.relpath] = o.status
        return dic

    def status(self):
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
                conflicteds += [so]
                conflicteds_abspath += [so.abspath]
            elif self.can_commit(so.abspath):
                tmps += [so]
            else:
                uncommitables += [so]

        others = [so for so in tmps
                  if not helper.is_conflicted(so, conflicteds_abspath)]

        uncommitables = [so for so in uncommitables
                         if not helper.is_conflicted(so, conflicteds_abspath)]

        content = render('blocks/versioning_status.mak', {
            'conflicteds': conflicteds,
            'uncommitables': uncommitables,
            'others': others
        }, self.request)
        return self._response({
            'content': content,
        })

    def short_diff(self):
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        res = vobj.diff(relpath)
        res = res.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")
        return self._response({'content': '<pre>%s</pre>' % res})

    def diff(self):
        filenames = self.request.POST.getall('filenames') or ''
        if not filenames:
            return self._response({
                'error_msg': 'You should provide at least one filename.',
            })

        if self.request.POST.get('submit') == 'Commit':
            # We have clicked on the commit button
            return self.prepare_commit(filenames)

        vobj = self.get_versioning_obj()
        lis = []
        can_commit = True
        for filename in filenames:
            lis += vobj.full_diff(filename)
            absfilename = browser.absolute_path(filename, self.root_path)
            if can_commit and not self.can_commit(absfilename):
                can_commit = False

        content = render('blocks/versioning_diff.mak', {
            'files': lis,
            'can_commit': can_commit,
        }, self.request)
        return self._response({'content': content})

    def update(self):
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        try:
            vobj.update(relpath)
        except pysvn.ClientError, e:
            return self._response({
                'error_msg': str(e).replace(self.root_path + '/', ''),
            })
        return self._response({
            'content': 'The repository has been updated!',
        })

    def prepare_commit(self, files=None):
        relpath = self.request.GET.get('path', '')
        vobj = self.get_versioning_obj()
        if not files:
            files = [f.relpath for f in vobj.get_commitable_files(relpath)]
        if not files:
            return self._response({
                'info_msg': 'No file to commit in %s' % relpath,
            })
        modal = render('blocks/prepare_commit_modal.mak', {
            'files': files,
        }, self.request)
        return self._response({
            'modal': modal,
        })

    def commit(self):
        msg = self.request.POST.get('msg')
        filenames = self.request.POST.getall('path')
        if not filenames:
            return self._response({'error_msg': 'No file selected!'})
        if not msg:
            return self._response({'error_msg': 'No commit message!'})

        error_msg = []
        for filename in filenames:
            absfilename = browser.absolute_path(filename, self.root_path)
            if not self.can_commit(absfilename):
                error_msg += [
                    'You don\'t have the permission to commit: %s' % filename]

        if error_msg:
            return self._response({
                'error_msg': '<br />'.join(error_msg)
            })

        vobj = self.get_versioning_obj()
        try:
            vobj.commit(filenames, msg)
        except Exception, e:
            log.exception(e)
            error_msg += []
            return self._response({
                'error_msg': 'Error during the commit %s' % str(e)
            })

        return self.status()

    def update_texts(self):
        params = unflatten_params(self.request.POST)
        if 'data' not in params or not params['data']:
            return self._response({'error_msg': 'Missing parameters!'})

        root_path = self.root_path
        status = True
        error_msgs = []
        files = []
        for dic in params['data']:
            filecontent = dic['filecontent']
            filename = dic['filename']
            absfilename = browser.absolute_path(filename, root_path)
            try:
                obj = xmltool.load_string(filecontent)
                obj.write(absfilename)
                files += [filename]
            except Exception, e:
                status = False
                error_msgs += ['%s: %s' % (filename, str(e))]

        if not status:
            return self._response({
                'error_msg': '<br />'.join(error_msgs)
            })

        if self.request.POST.get('commit'):
            return self.prepare_commit(files)

        return self._response({
            'content': 'Files updated'
        })

    def edit_conflict(self):
        """
        Basically it's the same function as editor.edit_text
        """
        filename = self.request.GET.get('path')
        if not filename:
            return self._response({
                'error_msg': 'A filename should be provided',
            })
        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        try:
            content = open(absfilename, 'r').read()
        except Exception, e:
            log.exception(e)
            return self._response({
                'error_msg': str(e)
            })

        html = '<form data-action="%s" action="%s" method="POST">' % (
            self.request.custom_route_path('versioning_dispatcher_json',
                                           method='update_conflict'),
            self.request.custom_route_path('versioning_dispatcher',
                                           method='update_conflict'),
        )
        html += '<input type="hidden" id="_xml_filename" name="filename" value="%s" />' % filename
        html += '<textarea class="form-control" name="filecontent">%s</textarea>' % content
        html += '<input type="submit" value="Save and resolve conflict" />'
        html += '</form>'

        dic = {
            'content': html,
        }
        return self._response(dic)

    def update_conflict(self):
        filecontent = self.request.POST.get('filecontent')
        filename = self.request.POST.get('filename') or ''
        if not filecontent or not filename:
            return self._response({'error_msg': 'Missing parameters!'})

        absfilename = browser.absolute_path(filename, self.root_path)
        try:
            obj = xmltool.load_string(filecontent)
            obj.write(absfilename)
        except Exception, e:
            return self._response({
                'error_msg': 'The conflict is not resolved: %s' % str(e)})

        vobj = self.get_versioning_obj()
        try:
            vobj.resolve(filename)
        except Exception, e:
            log.exception(e)
            return self._response({
                'error_msg': ('Error during the conflict\'s resolution '
                              '%s' % str(e))
            })
        return self.status()
