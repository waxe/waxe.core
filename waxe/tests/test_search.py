#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .. import search, browser
import os
import shutil
from whoosh import index
from mock import patch


path = os.path.join(os.getcwd(), 'waxe/tests')
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
            self.assertEqual(len(fields), 4)

    def test_incremental_index(self):
        # Create the index
        paths = browser.get_all_files(filepath, filepath)[1]
        search.clean_index(indexpath, paths)

        dic = {}
        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            for field in searcher.all_stored_fields():
                dic[field['path']] = field['content']
        self.assertEqual(len(dic), 4)

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
            self.assertEqual(len(newdic), 5)
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
            self.assertEqual(len(newdic), 5)
            self.assertEqual(newdic[newfile], content + ' updated')
            newdic.pop(newfile)
            self.assertEqual(dic, newdic)
        finally:
            os.remove(newfile)

        # file is deleted
        search.incremental_index(indexpath, paths)
        newdic = {}
        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            for field in searcher.all_stored_fields():
                newdic[field['path']] = field['content']

        self.assertEqual(len(newdic), 4)
        self.assertEqual(newdic, dic)

    def test_do_index(self):
        paths = browser.get_all_files(filepath, filepath)[1]
        search.do_index(indexpath, paths)
        search.do_index(indexpath, paths)

        ix = index.open_dir(indexpath)
        with ix.searcher() as searcher:
            fields = list(searcher.all_stored_fields())
            self.assertEqual(len(fields), 4)

    def test_do_search(self):
        paths = browser.get_all_files(filepath, filepath)[1]
        search.do_index(indexpath, paths)

        res = search.do_search(indexpath, 'file')
        expected = ([
            (os.path.join(filepath, '1.xml'),
             u'<b class="match term0">File</b> 1'),
            (os.path.join(filepath, '2.xml'),
             u'<b class="match term0">File</b> 2')
        ], 2)
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
