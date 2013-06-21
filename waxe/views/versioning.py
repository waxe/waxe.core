from base import BaseViews
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.exceptions import Forbidden
from .. import browser
from .. import diff
from ..models import User

from subprocess import Popen, PIPE
import pysvn

# Use to defined the color we will display the status
labels_mapping = {
    pysvn.wc_status_kind.unversioned: 'label-default',
    pysvn.wc_status_kind.modified: 'label-info',
    pysvn.wc_status_kind.conflicted: 'label-important',
}


def svn_cmd(request, cmd):
    lis = ['svn', cmd, '--non-interactive']
    auth, login, pwd, keep = get_svn_login(request)
    if auth:
        lis += ['--username', login, '--password', pwd]
    return ' '.join(lis)


def svn_ssl_server_trust_prompt(trust_dict):
    return True, trust_dict['failures'], False


def get_svn_login(request):
    auth = False
    if 'versioning.auth.active' in request.registry.settings:
        auth = True

    pwd = request.registry.settings.get('versioning.auth.pwd')
    editor_login = request.session.get('editor_login')
    if not editor_login:
        editor_login = request.user.login
        if not pwd:
            pwd = request.user.password
    assert editor_login
    if not pwd:
        pwd = User.query.filter_by(login=editor_login).one().password
    assert pwd

    return auth, str(editor_login), pwd, False


class Views(BaseViews):

    def get_svn_client(self):
        client = pysvn.Client()
        client.callback_get_login = get_svn_login
        if self.request.registry.settings.get('versioning.auth.https'):
            client.callback_ssl_server_trust_prompt = svn_ssl_server_trust_prompt
        return client

    @view_config(route_name='svn_status', renderer='index.mak', permission='edit')
    @view_config(route_name='svn_status_json', renderer='json', permission='edit')
    def svn_status(self):
        root_path = self.request.root_path
        relpath = self.request.GET.get('path', '')
        abspath = browser.absolute_path(relpath, root_path)
        client = self.get_svn_client()
        changes = client.status(abspath)
        lis = []
        for f in reversed(changes):
            if f.text_status == pysvn.wc_status_kind.normal:
                continue
            p = browser.relative_path(f.path, root_path)
            label_class = labels_mapping.get(f.text_status) or None
            link = self.request.route_path(
                'svn_diff', _query=[('filename', p)])
            json_link = self.request.route_path(
                'svn_diff_json', _query=[('filename', p)])
            lis += [(f.text_status, label_class, p, link, json_link)]

        content = render('blocks/versioning.mak',
                         {'files_data': lis}, self.request)
        return {
            'content': content,
        }

    @view_config(route_name='svn_diff', renderer='index.mak', permission='edit')
    @view_config(route_name='svn_diff_json', renderer='json', permission='edit')
    def svn_diff(self):
        filename = self.request.GET.get('filename') or ''
        if not filename:
            return {
                'error_msg': 'A filename should be provided',
            }

        root_path = self.request.root_path
        absfilename = browser.absolute_path(filename, root_path)

        client = self.get_svn_client()
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
        html = d.make_table(
            old_content.decode('utf-8').splitlines(),
            new_content.decode('utf-8').splitlines())

        if self.request.user.can_commit(absfilename):
            html += u'<input data-filename="%s" type="submit" class="diff-submit" value="Save and commit" />' % filename
        return {'content': html}

    @view_config(route_name='svn_update', renderer='index.mak', permission='edit')
    @view_config(route_name='svn_update_json', renderer='json', permission='edit')
    def svn_update(self):
        # We don't use pysvn to make the repository update since it's very slow
        # on big repo. Also the output is better from the command line.
        p = Popen(svn_cmd(self.request, "update  %s" % self.request.root_path),
                  shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  close_fds=True)
        (child_stdout, child_stdin) = (p.stdout, p.stdin)
        error = p.stderr.read()
        if error:
            return {'error_msg': error}

        return {'content': '<pre>%s</pre>' % p.stdout.read()}

    @view_config(route_name='svn_commit_json', renderer='json', permission='edit')
    def svn_commit_json(self):
        filename = self.request.POST.get('filename')
        msg = self.request.POST.get('msg')
        if not filename or not msg:
            return {'status': False, 'error_msg': 'Bad parameters!'}
        root_path = self.request.root_path
        absfilename = browser.absolute_path(filename, root_path)
        if not self.request.user.can_commit(absfilename):
            raise Forbidden('Restricted area')

        client = self.get_svn_client()
        status = client.status(absfilename)
        assert len(status) == 1, status
        status = status[0]
        if status.text_status == pysvn.wc_status_kind.conflicted:
            return {
                'status': False,
                'error_msg': 'Can\'t commit a conflicted file'
            }

        if status.text_status == pysvn.wc_status_kind.unversioned:
            try:
                client.add(absfilename)
            except Exception, e:
                return {'status': False, 'error_msg': str(e)}

        try:
            client.checkin(absfilename, msg)
        except Exception, e:
            return {'status': False, 'error_msg': str(e)}

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
