import os.path
from base import BaseView
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.exceptions import Forbidden
from .. import browser
from .. import diff
from .. import models
from ..utils import unflatten_params
import logging

from subprocess import Popen, PIPE
import pysvn
import locale

log = logging.getLogger(__name__)

# Use to defined the color we will display the status
labels_mapping = {
    pysvn.wc_status_kind.unversioned: 'label-default',
    pysvn.wc_status_kind.modified: 'label-info',
    pysvn.wc_status_kind.conflicted: 'label-important',
}


def svn_ssl_server_trust_prompt(trust_dict):
    return True, trust_dict['failures'], False


class Views(BaseView):

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

    def svn_cmd(self, cmd):
        lis = ['svn', cmd, '--non-interactive']
        auth, login, pwd, keep = self.get_svn_login()
        if auth:
            lis += ['--username', login, '--password', pwd]
        return ' '.join(lis)

    def get_svn_login(self):
        auth = False
        if 'versioning.auth.active' in self.request.registry.settings:
            auth = True

        editor_login = self.current_user.login
        pwd = self.request.registry.settings.get('versioning.auth.pwd')
        if not pwd:
            pwd = self.current_user.config.versioning_password

        if not pwd:
            # TODO: a good idea should be to ask the password to the user
            raise Exception('No versioning password set for %s' % editor_login)

        return auth, str(editor_login), pwd, False

    def get_svn_client(self):
        client = pysvn.Client()
        client.callback_get_login = lambda *args, **kw: self.get_svn_login()
        if self.request.registry.settings.get('versioning.auth.https'):
            client.callback_ssl_server_trust_prompt = svn_ssl_server_trust_prompt
        return client

    @view_config(route_name='svn_status', renderer='index.mak', permission='edit')
    @view_config(route_name='svn_status_json', renderer='json', permission='edit')
    def svn_status(self):
        root_path = self.root_path
        relpath = self.request.GET.get('path', '')
        abspath = browser.absolute_path(relpath, root_path)
        client = self.get_svn_client()
        changes = client.status(abspath)
        lis = []
        for f in reversed(changes):
            if os.path.isdir(f.path.encode(locale.getpreferredencoding())):
                continue
            if f.text_status == pysvn.wc_status_kind.normal:
                continue
            p = browser.relative_path(f.path, root_path)
            label_class = labels_mapping.get(f.text_status) or None
            link = self.request.route_path(
                'svn_diff', _query=[('filenames', p)])
            json_link = self.request.route_path(
                'svn_diff_json', _query=[('filenames', p)])
            lis += [(f.text_status, label_class, p, link, json_link)]

        content = render('blocks/versioning.mak', {
            'files_data': lis,
        }, self.request)
        return {
            'content': content,
        }

    def _svn_diff(self, filename, client, index=0, editable=False):
        root_path = self.root_path
        absfilename = browser.absolute_path(filename, root_path)
        info = client.info(root_path)
        old_rev = pysvn.Revision(pysvn.opt_revision_kind.number,
                                 info.revision.number)

        new_content = open(absfilename, 'r').read()
        status = client.status(absfilename)
        assert len(status) == 1
        if status[0].text_status != pysvn.wc_status_kind.unversioned:
            old_content = client.cat(absfilename, old_rev)
        else:
            old_content = ''

        d = diff.HtmlDiff()
        link = self.request.route_path('edit', _query=[('filename', filename)])
        json_link = self.request.route_path('edit_json', _query=[('filename', filename)])
        html = '<h3><a data-href="%s" href="%s">%s</a></h3>' % (json_link, link, filename)
        if editable:
            html += '<input type="text" name="data:%i:filename" value="%s" />' % (
                index,
                filename
            )
            # The content of this textarea will we filled in javascript
            html += '<textarea name="data:%i:filecontent"></textarea>' % index
        html += d.make_table(
            old_content.decode('utf-8').splitlines(),
            new_content.decode('utf-8').splitlines())
        return html

    @view_config(route_name='svn_diff', renderer='index.mak', permission='edit')
    @view_config(route_name='svn_diff_json', renderer='json', permission='edit')
    def svn_diff(self):
        filenames = self.request.GET.getall('filenames') or ''
        if not filenames:
            return {
                'error_msg': 'You should provide at least one filename.',
            }

        client = self.get_svn_client()
        html = ''
        can_commit = True
        root_path = self.root_path

        for index, filename in enumerate(filenames):
            absfilename = browser.absolute_path(filename, root_path)
            if not self.can_commit(absfilename):
                can_commit = False
            html += self._svn_diff(filename, client, index=index,
                                   editable=can_commit)

        if can_commit:
            html = (
                '<form data-action="/update-texts.json" '
                'class="multiple-diff-submit">'
                '%s'
                '<input data-filename="%s" type="submit" '
                'class="diff-submit" value="Save and commit" />'
                '</form') % (''.join(html), filename)
        return {'content': html}

    @view_config(route_name='svn_update', renderer='index.mak', permission='edit')
    @view_config(route_name='svn_update_json', renderer='json', permission='edit')
    def svn_update(self):
        # We don't use pysvn to make the repository update since it's very slow
        # on big repo. Also the output is better from the command line.
        p = Popen(self.svn_cmd("update  %s" % self.root_path),
                  shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  close_fds=True)
        (child_stdout, child_stdin) = (p.stdout, p.stdin)
        error = p.stderr.read()
        if error:
            return {'error_msg': error}

        res = p.stdout.read()
        # We want to display relative urls
        res = res.replace(self.root_path + '/', '')
        return {'content': '<pre>%s</pre>' % res}

    @view_config(route_name='svn_commit_json', renderer='json', permission='edit')
    def svn_commit_json(self):
        msg = self.request.POST.get('msg')
        params = unflatten_params(self.request.POST)

        if 'data' not in params or not params['data'] or not msg:
            return {'status': False, 'error_msg': 'Bad parameters!'}

        filenames = []
        for dic in params['data']:
            filenames += [dic['filename']]

        root_path = self.root_path

        error_msg = []
        ok_filenames = []

        for filename in filenames:
            absfilename = browser.absolute_path(filename, root_path)
            if not self.can_commit(absfilename):
                error_msg += ['Can\'t commit: %s' % filename]
                continue

            client = self.get_svn_client()
            status = client.status(absfilename)
            assert len(status) == 1, status
            status = status[0]
            if status.text_status == pysvn.wc_status_kind.conflicted:
                error_msg += ['Can\'t commit conflicted file: %s' % filename]
                continue

            if status.text_status == pysvn.wc_status_kind.unversioned:
                try:
                    client.add(absfilename)
                except Exception, e:
                    log.exception(e)
                    error_msg += ['Can\'t add %s' % filename]
                    continue

            ok_filenames += [absfilename]

        if ok_filenames:
            try:
                client.checkin(ok_filenames, msg)
            except Exception, e:
                log.exception(e)
                error_msg += ['Can\'t commit %s' % filename]

        if error_msg:
            return {'status': False, 'error_msg': '<br />'.join(error_msg)}
        # TODO: return the content of the status.
        # We should make a redirect!
        return {'status': True, 'content': 'Commit done'}


def includeme(config):
    config.add_route('svn_status', '/versioning/status')
    config.add_route('svn_status_json', '/versioning/status.json')
    config.add_route('svn_diff', '/versioning/diff')
    config.add_route('svn_diff_json', '/versioning/diff.json')
    config.add_route('svn_update', '/versioning/update')
    config.add_route('svn_update_json', '/versioning/update.json')
    config.add_route('svn_commit_json', '/versioning/commit.json')
    config.scan(__name__)
