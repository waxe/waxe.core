import os
import locale
import pysvn
from waxe import browser


STATUS_NORMAL = 'normal'
STATUS_ADDED = 'added'
STATUS_DELETED = 'deleted'
STATUS_MODIFED = 'modified'
STATUS_CONFLICTED = 'conflicted'
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

    def _status(self, abspath, changes, short=True):
        lis = []
        for f in reversed(changes):
            status = PYSVN_STATUS_MAPPING[f.text_status]
            fpath = f.path.encode(locale.getpreferredencoding())
            isdir = os.path.isdir(fpath)
            # Don't skip the root if it's a file, we want to get the file
            # status
            if f.path == abspath and short and isdir:
                continue
            if short and status == STATUS_NORMAL and isdir:
                # For short status we just want to know if a normal folder has
                # some updates
                res = self.client.status(f.path, recurse=False, get_all=False)
                if res:
                    relpath = browser.relative_path(f.path, self.root_path)
                    lis += [StatusObject(f.path, relpath, STATUS_MODIFED)]
                continue

            if not short and status == STATUS_UNVERSIONED and isdir:
                # For full status we want to get all the files under an
                # unversioned folder
                for sf in browser.get_all_files(f.path,
                                                abspath,
                                                relative=False)[1]:
                    relpath = browser.relative_path(sf, abspath)
                    lis += [StatusObject(sf, relpath, STATUS_UNVERSIONED)]
                continue

            if status == STATUS_NORMAL:
                continue

            relpath = browser.relative_path(f.path, self.root_path)
            lis += [StatusObject(f.path, relpath, status)]

        return lis

    def status(self, path=None):
        abspath = self.root_path
        if path:
            abspath = browser.absolute_path(path, self.root_path)
        try:
            changes = self.client.status(abspath, recurse=False, get_all=True)
            return self._status(abspath, changes)
        except pysvn.ClientError, e:
            if not str(e).endswith('is not a working copy'):
                raise
            # The file/folder is not in working copy so we force the status to
            # unversioned
            return [
                StatusObject(abspath, path, STATUS_UNVERSIONED)
            ]

    def full_status(self, path=None):
        abspath = self.root_path
        if path:
            abspath = browser.absolute_path(path, self.root_path)
        try:
            changes = self.client.status(abspath, recurse=True, get_all=False)
            return self._status(abspath, changes, short=False)
        except pysvn.ClientError, e:
            if not str(e).endswith('is not a working copy'):
                raise
            # The file/folder is not in working copy so we force the status to
            # unversioned
            return [
                StatusObject(abspath, path, STATUS_UNVERSIONED)
            ]
