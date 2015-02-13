#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .. import search, browser
import os
import shutil
from whoosh import index
from mock import patch


path = os.path.join(os.getcwd(), 'waxe/core/tests')
filepath = os.path.join(path, 'whoosh')
indexpath = os.path.join(path, 'whoosh_index')


class TestSearch(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(indexpath):
            shutil.rmtree(indexpath)
        super(TestSearch, self).tearDown()

    def test_clean_index(self):
        paths = browser.get_all_files(filepath, filepath)[1]
        search.clean_index(indexpath, paths)

        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            fields = list(searcher.all_stored_fields())
            self.assertEqual(len(fields), 5)

    def test_incremental_index(self):
        # Create the index
        paths = browser.get_all_files(filepath, filepath)[1]
        search.clean_index(indexpath, paths)

        dic = {}
        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            for field in searcher.all_stored_fields():
                dic[field['path']] = field['content']
        self.assertEqual(len(dic), 5)

        content = 'New file'
        newfile = os.path.join(filepath, 'newfile.xml')
        open(newfile, 'w').write(content)
        try:
            # New file
            search.incremental_index(indexpath, paths + [newfile])
            newdic = {}
            ix = index.open_dir(indexpath)
            with ix.searcher() as searcher:
                for field in searcher.all_stored_fields():
                    newdic[field['path']] = field['content']
            self.assertEqual(len(newdic), 6)
            self.assertEqual(newdic[newfile], content)
            newdic.pop(newfile)
            self.assertEqual(dic, newdic)

            # Update file
            open(newfile, 'w').write(content + ' updated')
            search.incremental_index(indexpath, paths + [newfile])
            newdic = {}
            ix = index.open_dir(indexpath)
            with ix.searcher() as searcher:
                for field in searcher.all_stored_fields():
                    newdic[field['path']] = field['content']
            self.assertEqual(len(newdic), 6)
            self.assertEqual(newdic[newfile], content + ' updated')
            newdic.pop(newfile)
            self.assertEqual(dic, newdic)

            # Don't index newfile, it should not be deleted
            search.incremental_index(indexpath, paths + [newfile])
            with ix.searcher() as searcher:
                fields = list(searcher.all_stored_fields())
                self.assertEqual(len(fields), 6)

            # Delete the file
            os.remove(newfile)
            search.incremental_index(indexpath, paths + [newfile])
            with ix.searcher() as searcher:
                fields = list(searcher.all_stored_fields())
                self.assertEqual(len(fields), 5)

            open(newfile, 'w').write(content)
            search.incremental_index(indexpath, paths + [newfile])
            with ix.searcher() as searcher:
                fields = list(searcher.all_stored_fields())
                self.assertEqual(len(fields), 6)

            search.incremental_index(indexpath, [newfile])
            with ix.searcher() as searcher:
                fields = list(searcher.all_stored_fields())
                self.assertEqual(len(fields), 6)

            search.incremental_index(indexpath, paths[:1])
            with ix.searcher() as searcher:
                fields = list(searcher.all_stored_fields())
                self.assertEqual(len(fields), 6)

        finally:
            try:
                os.remove(newfile)
            except:
                pass

        # file is deleted
        search.incremental_index(indexpath, paths + [newfile])
        newdic = {}
        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            for field in searcher.all_stored_fields():
                newdic[field['path']] = field['content']

        self.assertEqual(len(newdic), 5)
        self.assertEqual(newdic, dic)

    def test_do_index(self):
        paths = browser.get_all_files(filepath, filepath)[1]
        self.assertEqual(len(paths), 5)

        search.do_index(indexpath, paths)
        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            fields = list(searcher.all_stored_fields())
            self.assertEqual(len(fields), 5)

    def test_do_search(self):
        paths = browser.get_all_files(filepath, filepath)[1]
        search.do_index(indexpath, paths)

        res = search.do_search(indexpath, 'file')
        expected = ([
            (os.path.join(filepath, '1.xml'),
             u'<b class="match term0">File</b> 1'),
            (os.path.join(filepath, '2.xml'),
             u'<b class="match term0">File</b> 2'),
            (os.path.join(filepath, 'sub/1.xml'),
             u'<b class="match term0">File</b> 1')
        ], 3)
        self.assertEqual(res, expected)

        # Make sure it searches in sub folder when we pass abspath
        res = search.do_search(indexpath, 'file', abspath=filepath)
        expected = ([
            (os.path.join(filepath, '1.xml'),
             u'<b class="match term0">File</b> 1'),
            (os.path.join(filepath, '2.xml'),
             u'<b class="match term0">File</b> 2'),
            (os.path.join(filepath, 'sub/1.xml'),
             u'<b class="match term0">File</b> 1')
        ], 3)
        self.assertEqual(res, expected)

        # Search in a subfolder
        res = search.do_search(
            indexpath,
            'file',
            abspath=os.path.join(filepath, 'sub'))
        expected = ([
            (os.path.join(filepath, 'sub/1.xml'),
             u'<b class="match term0">File</b> 1')
        ], 1)
        self.assertEqual(res, expected)

        res = search.do_search(indexpath, u'Téster')
        expected = ([
            (os.path.join(filepath, u'é-iso.xml'),
             u'<b class="match term0">Téster</b> les accents à risque'),
            (os.path.join(filepath, u'é.xml'),
             u'<b class="match term0">Téster</b> les accents à risque'),
        ], 2)
        self.assertEqual(res, expected)

        res = search.do_search(indexpath, u'tester')
        expected = ([
            (os.path.join(filepath, u'é-iso.xml'),
             u'<b class="match term0">Téster</b> les accents à risque'),
            (os.path.join(filepath, u'é.xml'),
             u'<b class="match term0">Téster</b> les accents à risque'),
        ], 2)
        self.assertEqual(res, expected)

        # The XML tags are not indexed
        res = search.do_search(indexpath, 'text')
        self.assertEqual(res, ([], 0))
