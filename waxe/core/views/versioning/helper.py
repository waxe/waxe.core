import os
import locale
import pysvn
from waxe.core import browser, utils
import tempfile
import importlib


STATUS_NORMAL = 'normal'
STATUS_ADDED = 'added'
STATUS_DELETED = 'deleted'
STATUS_MODIFED = 'modified'
STATUS_CONFLICTED = 'conflicted'
STATUS_UNVERSIONED = 'unversioned'
STATUS_MISSING = 'missing'
STATUS_OTHER = 'other'

PYSVN_STATUS_MAPPING = {
    # does not exist
    pysvn.wc_status_kind.none: STATUS_OTHER,
    # is not a versioned thing in this wc
    pysvn.wc_status_kind.unversioned: STATUS_UNVERSIONED,
    # exists, but uninteresting.
    pysvn.wc_status_kind.normal: STATUS_NORMAL,
    # is scheduled for addition
    pysvn.wc_status_kind.added: STATUS_ADDED,
    # under v.c., but is missing
    pysvn.wc_status_kind.missing: STATUS_MISSING,
    # scheduled for deletion
    pysvn.wc_status_kind.deleted: STATUS_DELETED,
    # was deleted and then re-added
    pysvn.wc_status_kind.replaced: STATUS_OTHER,
    # text or props have been modified
    pysvn.wc_status_kind.modified: STATUS_MODIFED,
    # local mods received repos mods
    pysvn.wc_status_kind.merged: STATUS_OTHER,
    # local mods received conflicting repos mods
    pysvn.wc_status_kind.conflicted: STATUS_CONFLICTED,
    # a resource marked as ignored
    pysvn.wc_status_kind.ignored: STATUS_OTHER,
    # an unversioned resource is in the way of the versioned resource
    pysvn.wc_status_kind.obstructed: STATUS_OTHER,
    # an unversioned path populated by an svn:external property
    pysvn.wc_status_kind.external: STATUS_OTHER,
    # a directory doesn't contain a complete entries list
    pysvn.wc_status_kind.incomplete: STATUS_OTHER,
}


def is_conflicted(so, lis):
    """
    :param so: the StatusObject to check
    :type so: StatusObject
    :param lis: list of absolute path of conflicted files
    :type lis: list of str

    Check that the given so is not generated by a conflicted file.
    """
    for abspath in lis:
        if so.abspath.startswith('%s.mine' % abspath):
            return True
        if so.abspath.startswith('%s.r' % abspath):
            return True
    return False


def svn_ssl_server_trust_prompt(trust_dict):
    return True, trust_dict['failures'], False


def get_svn_username(request, current_user, logged_user, commit):
    if 'waxe.versioning.get_svn_username' in request.registry.settings:
        func = request.registry.settings['waxe.versioning.get_svn_username']
        mod, func = func.rsplit('.', 1)
        func = getattr(importlib.import_module(mod), func)
        return func(request, current_user, logged_user, commit)
    return current_user.login


def get_svn_login(request, current_user, logged_user, commit):
    auth = False
    if 'waxe.versioning.auth.active' in request.registry.settings:
        auth = True

    editor_login = get_svn_username(request, current_user, logged_user, commit)
    if not auth:
        # No auth, no need to find a password
        return False, str(editor_login), None, False

    pwd = request.registry.settings.get('waxe.versioning.auth.pwd')
    if not pwd:
        pwd = current_user.config.versioning_password

    if not pwd:
        # TODO: a good idea should be to ask the password to the user
        raise Exception('No versioning password set for %s' % editor_login)

    return auth, str(editor_login), pwd, False


def get_svn_client(request, current_user, logged_user, commit):
    client = pysvn.Client()
    # Set the username in case there is no authentication
    client.set_default_username(str(current_user.login))
    client.callback_get_login = lambda *args, **kw: get_svn_login(request,
                                                                  current_user,
                                                                  logged_user,
                                                                  commit)
    if request.registry.settings.get('waxe.versioning.auth.https'):
        client.callback_ssl_server_trust_prompt = svn_ssl_server_trust_prompt
    return client


class StatusObject(object):

    def __init__(self, abspath, relpath, status, type_=None):
        self.abspath = abspath
        self.relpath = relpath
        self.status = status
        self.type = type_
        if not self.type:
            self.type = 'folder' if os.path.isdir(self.abspath) else 'file'

    def __repr__(self):
        return '<%s: %s>' % (self.relpath.encode('utf-8'), self.status)

    def __eq__(self, other):
        for p in ['abspath', 'relpath', 'status']:
            if getattr(self, p) != getattr(other, p):
                return False
        return True

    def to_dict(self):
        return {
            # Alias in waiting we remove relpath
            'path': self.relpath,
            'relpath': self.relpath,
            'status': self.status,
            'type': self.type,
        }


class PysvnVersioning(object):

    def __init__(self, request, extensions, current_user, logged_user,
                 root_path, commit):
        self.extensions = extensions
        self.client = get_svn_client(request, current_user, logged_user,
                                     commit)
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
                if status == STATUS_UNVERSIONED:
                    # The root path is unversioned so all children are
                    # unversioned
                    for sf in sum(browser.get_files(self.extensions, f.path,
                                                    abspath,
                                                    relative=False), []):
                        relpath = browser.relative_path(sf, self.root_path)
                        lis += [StatusObject(sf, relpath, STATUS_UNVERSIONED)]
                continue

            if short and status == STATUS_NORMAL and isdir:
                # For short status we just want to know if a normal folder has
                # some updates
                res = self.client.status(f.path, recurse=True, get_all=False)
                if res:
                    relpath = browser.relative_path(f.path, self.root_path)
                    lis += [StatusObject(f.path, relpath, STATUS_MODIFED)]
                continue

            if not short and status == STATUS_UNVERSIONED and isdir:
                # For full status we want to get all the files under an
                # unversioned folder
                # Add the folder: the user should be able to commit empty file
                # to be able to move files in.
                if f.path != self.root_path:
                    relpath = browser.relative_path(f.path, self.root_path)
                    lis += [StatusObject(f.path, relpath, STATUS_UNVERSIONED)]
                for sf in sum(browser.get_all_files(self.extensions,
                                                    f.path,
                                                    abspath,
                                                    relative=False), []):
                    relpath = browser.relative_path(sf, self.root_path)
                    lis += [StatusObject(sf, relpath, STATUS_UNVERSIONED)]
                continue

            if status == STATUS_NORMAL:
                continue

            relpath = browser.relative_path(f.path, self.root_path)
            lis += [StatusObject(f.path, relpath, status)]

        return lis

    def empty_status(self, abspath):
        """Get the status of the given abspath. We don't care of any child if
        it is a folder
        """
        try:
            changes = self.client.status(abspath,
                                         depth=pysvn.depth.empty,
                                         get_all=False)
            if not changes:
                status = STATUS_NORMAL
            else:
                assert(len(changes) == 1)
                status = PYSVN_STATUS_MAPPING[changes[0].text_status]
        except pysvn.ClientError, e:
            if (str(e).endswith('is not a working copy') or
               str(e).endswith('was not found.')):
                # 2 conditions since we support old and new svn version
                status = STATUS_UNVERSIONED
            else:
                raise

        relpath = browser.relative_path(abspath, self.root_path)
        return StatusObject(abspath, relpath, status)

    def status(self, path=None):
        abspath = self.root_path
        if path:
            abspath = browser.absolute_path(path, self.root_path)
        try:
            changes = self.client.status(abspath, recurse=False, get_all=True)
            return self._status(abspath, changes)
        except pysvn.ClientError, e:
            if not (str(e).endswith('is not a working copy') or
               str(e).endswith('was not found.')):
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
            if not (str(e).endswith('is not a working copy') or
               str(e).endswith('was not found.')):
                raise
            # The file/folder is not in working copy so we force the status to
            # unversioned
            return [
                StatusObject(abspath, path, STATUS_UNVERSIONED)
            ]

    def update(self, path=None):
        abspath = self.root_path
        if path:
            abspath = browser.absolute_path(path, self.root_path)

        filenames = []

        def notify(event_dict, filenames):

            if event_dict['kind'] == pysvn.node_kind.file:
                status = STATUS_OTHER
                if event_dict['action'] == pysvn.wc_notify_action.update_delete:
                    status = STATUS_DELETED
                elif event_dict['action'] == pysvn.wc_notify_action.update_update:
                    status = STATUS_MODIFED
                elif event_dict['action'] == pysvn.wc_notify_action.update_add:
                    status = STATUS_ADDED
                filenames += [(status, event_dict['path'])]
        self.client.callback_notify = lambda dic: notify(dic, filenames)

        # NOTE: use pysvn.depth.unknown to follow the client repo depths
        self.client.update(abspath, depth=pysvn.depth.unknown)
        return filenames

    def diff(self, path=None):
        diffs = []
        lis = self.full_status(path)
        tmp = tempfile.mkdtemp()
        for so in lis:
            if so.status == STATUS_CONFLICTED:
                continue
            if so.status in [STATUS_UNVERSIONED, STATUS_ADDED]:
                content = open(so.abspath, 'r').read()
                content = content.decode('utf-8')
                diffs += [u'New file %s\n\n%s' % (so.relpath, content)]
            elif so.status in [STATUS_DELETED, STATUS_MISSING]:
                diffs += [u'Deleted file %s' % so.relpath]
            else:
                s = self.client.diff(tmp, so.abspath)
                s = s.decode('utf-8')
                s = s.replace(self.root_path + '/', '')
                diffs += [s]
        return diffs


    def full_diff_content(self, path=None):
        diffs = []
        contents = []
        lis = self.full_status(path)
        for so in lis:
            if so.status == STATUS_CONFLICTED:
                continue
            if so.status in [STATUS_DELETED, STATUS_MISSING]:
                new_content = ''
            else:
                new_content = open(so.abspath, 'r').read()
            if so.status in [STATUS_UNVERSIONED, STATUS_ADDED]:
                old_content = ''
            else:
                # old_content = self.client.cat(so.abspath)
                info = self.client.info(so.abspath)
                old_rev = pysvn.Revision(pysvn.opt_revision_kind.number,
                                         info.revision.number)
                old_content = self.client.cat(so.abspath, old_rev)

            contents.append({
                'left': utils.safe_str(old_content),
                'right': utils.safe_str(new_content),
                'relpath': so.relpath,
            })
        return contents

    def get_commitable_files(self, path=None):
        lis = self.full_status(path)
        # For now we just skip the conflicted file.
        conflicteds = []
        tmps = []
        for so in lis:
            if so.status == STATUS_CONFLICTED:
                conflicteds += [so.abspath]
            else:
                tmps += [so]
        return [so for so in tmps if not is_conflicted(so, conflicteds)]

    def unversioned_parents(self, abspath):
        lis = []
        if abspath == self.root_path:
            return lis
        dirpath = os.path.dirname(abspath)
        while dirpath != self.root_path:
            so = self.empty_status(dirpath)
            if so.status == STATUS_UNVERSIONED:
                lis += [dirpath]
                dirpath = os.path.dirname(dirpath)
            else:
                return reversed(lis)
        return reversed(lis)

    def add(self, paths):
        """Add the file(s) to be commited

        :param paths: path of the file(s) to commit
        :param paths: str or list
        """
        if not isinstance(paths, list):
            paths = [paths]

        abspaths = []
        for path in paths:
            abspath = browser.absolute_path(path, self.root_path)
            if self.empty_status(abspath).status != STATUS_UNVERSIONED:
                continue

            for dirpath in self.unversioned_parents(abspath):
                # add the unversioned directory
                self.client.add(dirpath, depth=pysvn.depth.empty)
                abspaths += [dirpath]

            if os.path.isdir(abspath):
                self.client.add(abspath, depth=pysvn.depth.empty)
            else:
                self.client.add(abspath)
            abspaths += [abspath]
        return abspaths

    def commit(self, paths, msg):
        """Commit file(s)

        :param paths: path of the file(s) to commit
        :type paths: str or list
        :param msg: the commit message
        :type msg: str
        """
        if not isinstance(paths, list):
            paths = [paths]

        errors = []
        abspaths = []
        for path in paths:
            abspath = browser.absolute_path(path, self.root_path)
            abspaths += [abspath]
            if self.empty_status(abspath).status == STATUS_CONFLICTED:
                errors += ['Can\'t commit conflicted file: %s' % path]

        if errors:
            # TODO: create a custom expection?
            raise Exception('\n'.join(errors))

        # Add all the files
        # TODO: we should make a cache of the versioning status
        rpaths = self.add(paths)
        for rpath in rpaths:
            if rpath not in abspaths:
                abspaths += [rpath]
        self.client.checkin(abspaths, msg)

    def resolve(self, path):
        """Resolve the conflict on the given path (filename)
        """
        abspath = browser.absolute_path(path, self.root_path)
        # NOTE: we don't check abspath is conflicted since self.client.resolved
        # don't raise exception
        self.client.resolved(abspath)

    def revert(self, path):
        """Revert the modification on the given path (filename)
        """
        abspath = browser.absolute_path(path, self.root_path)
        self.client.revert(abspath)

    def remove(self, path):
        """Remove the given path
        """
        abspath = browser.absolute_path(path, self.root_path)
        # force=True, also delete local file
        self.client.remove(abspath, force=True)

    def move(self, path, newpath):
        """Revert the modification on the given path (filename)

        .. note:: path and newpath should be absolute path
        """
        newpath = os.path.join(newpath, os.path.basename(path))
        # force=True, also move modified files
        self.client.move(path, newpath, force=True)

    def has_conflict(self, path=None):
        lis = self.full_status(path)
        for so in lis:
            if so.status == STATUS_CONFLICTED:
                return True
        return False
