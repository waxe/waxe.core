import os
import locale
import pysvn
from waxe import browser


STATUS_NORMAL = 'normal'
STATUS_ADDED = 'added'
STATUS_DELETED = 'deleted'
STATUS_MODIFED = 'modified'
STATUS_CONFLICTED = 'conflited'
STATUS_UNVERSIONED = 'unversioned'
STATUS_MISSING = 'missing'

PYSVN_STATUS_MAPPING = {
    pysvn.wc_status_kind.normal: STATUS_NORMAL,
    pysvn.wc_status_kind.added: STATUS_ADDED,
    pysvn.wc_status_kind.deleted: STATUS_DELETED,
    pysvn.wc_status_kind.modified: STATUS_MODIFED,
    pysvn.wc_status_kind.conflicted: STATUS_CONFLICTED,
    pysvn.wc_status_kind.unversioned: STATUS_UNVERSIONED,
    pysvn.wc_status_kind.missing: STATUS_MISSING,
}


class StatusObject(object):

    def __init__(self, abspath, relpath, status):
        self.abspath = abspath
        self.relpath = relpath
        self.status = status

    def __repr__(self):
        return '<%s: %s>' % (self.relpath.encode('utf-8'), self.status)

    def __eq__(self, other):
        for p in ['abspath', 'relpath', 'status']:
            if getattr(self, p) != getattr(other, p):
                return False
        return True


class PysvnVersioning(object):

    def __init__(self, client, root_path):
        self.client = client
        self.root_path = root_path

    def status(self, path=None):
        abspath = self.root_path
        if path:
            abspath = browser.absolute_path(path, self.root_path)
        changes = self.client.status(abspath, recurse=False, get_all=True)
        lis = []
        for f in reversed(changes):
            status = PYSVN_STATUS_MAPPING[f.text_status]
            if f.path == abspath:
                continue
            abspath = f.path.encode(locale.getpreferredencoding())
            if status == STATUS_NORMAL and os.path.isdir(abspath):
                res = self.client.status(f.path, recurse=False, get_all=False)
                if res:
                    relpath = browser.relative_path(f.path, self.root_path)
                    lis += [StatusObject(f.path, relpath, STATUS_MODIFED)]
                    continue
            if status == STATUS_NORMAL:
                continue

            relpath = browser.relative_path(f.path, self.root_path)
            lis += [StatusObject(f.path, relpath, status)]

        return lis
