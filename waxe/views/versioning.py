from base import BaseViews
from pyramid.view import view_config
from pyramid.renderers import render
from .. import browser
from .. import diff

from subprocess import Popen, PIPE
import pysvn

# Use to defined the color we will display the status
labels_mapping = {
    pysvn.wc_status_kind.unversioned: 'label-default',
    pysvn.wc_status_kind.modified: 'label-info',
    pysvn.wc_status_kind.conflicted: 'label-important',
}


class Views(BaseViews):

    def get_svn_client(self):
        client = pysvn.Client()
        return client

    @view_config(route_name='svn_status_json', renderer='json', permission='edit')
    def svn_status_json(self):
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
                'svn_diff_json', _query=[('filename', p)])
            lis += [(f.text_status, label_class, p, link)]

        content = render('versioning.mak',
                         {'files_data': lis}, self.request)
        return {
            'content': content,
        }

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

        html += u'<input type="submit" class="diff-submit" value="Save and commit" />'
        return {'content': html}

    @view_config(route_name='svn_update_json', renderer='json', permission='edit')
    def svn_update(self):
        # We don't use pysvn to make the repository update since it's very slow
        # on big repo. Also the output is better from the command line.
        p = Popen("svn update --non-interactive %s" % self.request.root_path,
                  shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  close_fds=True)
        (child_stdout, child_stdin) = (p.stdout, p.stdin)
        error = p.stderr.read()
        if error:
            return {'error_msg': error}

        return {'content': p.stdout.read()}


def includeme(config):
    config.add_route('svn_status_json', '/versioning/status.json')
    config.add_route('svn_diff_json', '/versioning/diff.json')
    config.add_route('svn_update_json', '/versioning/update.json')
    config.scan(__name__)
