#!/usr/bin/env python

import unittest
from .. import browser
import os

class TestBrowser(unittest.TestCase):

    def test_relative_path(self):
        root_path = os.path.join(os.getcwd(), 'waxe', 'tests', 'files')
        assert os.path.exists(root_path)
        try:
            relpath = browser.relative_path('.', root_path)
            assert 0
        except IOError, e:
            self.assertEqual(str(e), ". doesn't exist")

        try:
            relpath = browser.relative_path('test', root_path)
            assert 0
        except IOError, e:
            self.assertEqual(str(e), "test doesn't exist")

        relpath = browser.relative_path(root_path, root_path)
        self.assertEqual(relpath, '.')

        relpath = browser.relative_path(root_path + '/folder', root_path)
        self.assertEqual(relpath, 'folder')

        relpath = browser.relative_path(root_path + '/folder/file.xml', root_path)
        self.assertEqual(relpath, 'folder/file.xml')

        path = os.path.normpath(root_path + '/../../folder/file.xml')
        try:
            relpath = browser.relative_path(path, root_path)
            assert 0
        except IOError, e:
            pass

    def test_absolute_path(self):
        root_path = os.path.join(os.getcwd(), 'waxe', 'tests', 'files')
        relpath = 'folder1'
        abspath = browser.absolute_path(relpath, root_path)
        self.assertEqual(abspath, os.path.join(root_path, 'folder1'))

        relpath = 'folder1/file.xml'
        abspath = browser.absolute_path(relpath, root_path)
        self.assertEqual(abspath, os.path.join(root_path, 'folder1/file.xml'))

        relpath = '/folder1/file.xml'
        try:
            browser.absolute_path(relpath, root_path)
            assert 0
        except IOError, e:
            self.assertEqual(str(e), "/folder1/file.xml doesn't exist")

        relpath = '../folder1/file.xml'
        try:
            browser.absolute_path(relpath, root_path)
            assert 0
        except IOError, e:
            self.assertEqual(str(e), "../folder1/file.xml doesn't exist")

    def test_get_files(self):
        root_path = os.path.join(os.getcwd(), 'waxe', 'tests', 'files')
        abspath = root_path
        folders, filenames = browser.get_files(abspath, root_path=root_path)
        self.assertEqual(folders, ['folder1'])
        self.assertEqual(filenames, ['file1.xml'])

        folders, filenames = browser.get_files(abspath, root_path=root_path)
        self.assertEqual(folders, ['folder1'])
        self.assertEqual(filenames, ['file1.xml'])

        abspath = os.path.join(root_path, 'folder1')
        folders, filenames = browser.get_files(abspath, root_path=root_path)
        self.assertEqual(folders, [])
        self.assertEqual(filenames, ['file2.xml'])

        abspath = os.path.join(os.getcwd(), 'waxe', 'tests', 'files',
                               'nonexisting')
        try:
            folders, filenames = browser.get_files(abspath, root_path=root_path)
            assert(False)
        except IOError, e:
            self.assertEqual(str(e), 'Directory nonexisting doesn\'t exist')

        abspath = root_path
        folders, filenames = browser.get_files(abspath, root_path=root_path,
                                               root_only=False, relative=False)
        self.assertEqual(folders, ['folder1'])
        self.assertEqual(filenames, ['file1.xml', 'file2.xml'])
        folders, filenames = browser.get_files(abspath, root_path=root_path,
                                               root_only=False, relative=True)

        self.assertEqual(folders, ['folder1'])
        self.assertEqual(filenames, ['file1.xml', 'folder1/file2.xml'])

    def test_get_all_files(self):
        root_path = os.path.join(os.getcwd(), 'waxe', 'tests', 'files')
        abspath = root_path
        folders, filenames = browser.get_all_files(abspath,
                                                   root_path=root_path,
                                                   relative=True,
                                                  )
        self.assertEqual(folders, ['folder1'])
        self.assertEqual(filenames, ['file1.xml', 'folder1/file2.xml'])
