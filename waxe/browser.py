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


def get_files(abspath):
    """Get the files and folder containing in relpath

    :param abspath: the absolute path we want to get the containing files and
                    folder.
    :type relpath: str

    ;return: the files and the folders containing in abspath
    :rtype: 2-tuple of list

    ..note:: we don't get the hidden files/folders and for the files, we only
             get the xml ones.
    """
    for dirpath, dirnames, filenames in os.walk(abspath):
        filenames.sort()
        dirnames.sort()

        folders = []
        files = []
        for d in dirnames:
            if d.startswith('.'):
                continue
            folders += [d]

        for f in filenames:
            _,ext = os.path.splitext(f)
            if ext != '.xml':
                continue
            if f.startswith('.'):
                continue
            files += [f]
        return folders, files

    return [], []

