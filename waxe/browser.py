#!/usr/bin/env python

import os.path


def relative_path(path, root_path):
    """Make a relative path

    :param path: the path we want to transform as relative
    :type path: str
    :param root_path: the root path
    :type root_path: str

    ;return: the relative path from given path according to root_path
    :rtype: str
    ..note:: The path should be in root_path. If it's not the case it raises
    and IOError exception.
    """
    path = os.path.normpath(path)
    root_path = os.path.normpath(root_path)
    relpath = os.path.relpath(path, root_path)
    abspath = os.path.normpath(os.path.join(root_path, relpath))
    if not abspath.startswith(root_path):
        # Forbidden path
        raise IOError("%s doesn't exist" % path)
    return relpath


def absolute_path(relpath, root_path):
    """Make an absolute relpath

    :param relpath: the relative path we want to transform as absolute
    :type relpath: str
    :param root_path: the root path
    :type root_path: str

    ;return: the absolute path from given relpath according to root_path
    :rtype: str
    """
    relpath = os.path.normpath(relpath)
    root_path = os.path.normpath(root_path)
    abspath = os.path.normpath(os.path.join(root_path, relpath))
    if not abspath.startswith(root_path):
        # Forbidden path
        raise IOError("%s doesn't exist" % relpath)
    return abspath


def get_files(abspath, root_path=None, root_only=True):
    """Get the files and folder containing in abspath

    :param abspath: the absolute path we want to get the containing files and
                    folder.
    :type abspath: str
    :param root_path: If given we make a relative url of the files and folders
    :type root_path: str
    :param root_only: If True we only get the file and folder at the root.
    :type depth: bool

    ;return: the files and the folders containing in abspath
    :rtype: 2-tuple of list

    ..note:: we don't get the hidden files/folders and for the files, we only
             get the xml ones.
    """
    folders = []
    files = []
    for index, (dirpath, dirnames, filenames) in enumerate(os.walk(abspath)):
        filenames.sort()
        dirnames.sort()

        for d in dirnames:
            if d.startswith('.'):
                continue
            p = d
            if root_path:
                p = os.path.join(dirpath, d)
                p = relative_path(p, root_path)
            folders += [p]

        for f in filenames:
            _, ext = os.path.splitext(f)
            if ext != '.xml':
                continue
            if f.startswith('.'):
                continue
            p = f
            if root_path:
                p = os.path.join(dirpath, f)
                p = relative_path(p, root_path)
            files += [p]

        if root_only:
            return folders, files

    return folders, files


def get_all_files(abspath, root_path=None):
    """Get the files and folder containing in abspath

    :param abspath: the absolute path we want to get the containing files and
                    folder.
    :type abspath: str
    :param root_path: If given we make a relative url of the files and folders
    :type root_path: str

    ;return: the files and the folders containing in abspath
    :rtype: 2-tuple of list

    ..note:: we don't get the hidden files/folders and for the files, we only
             get the xml ones.
    """
    return get_files(abspath, root_path=root_path, root_only=False)
