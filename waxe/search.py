import os.path
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.analysis import PathTokenizer, StemmingAnalyzer, CharsetFilter
from whoosh.support.charset import accent_map
from whoosh import index
from whoosh.qparser import QueryParser, FuzzyTermPlugin
import re
import math


HITS_PER_PAGE = 20


def get_schema():
    analyser = StemmingAnalyzer() | CharsetFilter(accent_map)
    return Schema(
        path=ID(analyzer=PathTokenizer(), stored=True),
        content=TEXT(analyser, stored=True, chars=True),
        time=STORED,
    )


encodings = ['utf-8', 'iso8859-1']


def to_unicode(s):
    if isinstance(s, unicode):
        return s
    for encoding in encodings:
        try:
            return unicode(s.decode(encoding))
        except UnicodeDecodeError:
            pass


def add_doc(writer, path):
    """Index file
    """
    content = open(path, "r").read()
    content = to_unicode(content)
    path = to_unicode(path)
    # Remove the XML tags
    content = re.sub(r'\s*<[^>/]*?>', ' ', content)
    content = re.sub(r'<[^>]*?>\s*', ' ', content)
    modtime = os.path.getmtime(path)
    writer.add_document(
        path=path,
        content=content,
        time=modtime,
    )


def incremental_index(dirname, paths):
    """Update the existing index
    """
    ix = index.open_dir(dirname)

    # The set of all paths in the index
    indexed_paths = set()
    # The set of all paths we need to re-index
    to_index = set()

    with ix.searcher() as searcher:
        writer = ix.writer()

        # Loop over the stored fields in the index
        for fields in searcher.all_stored_fields():
            indexed_path = fields['path']
            indexed_paths.add(indexed_path)

            if not os.path.exists(indexed_path):
                # This file was deleted since it was indexed
                writer.delete_by_term('path', indexed_path)

            else:
                # Check if this file was changed since it
                # was indexed
                indexed_time = fields['time']
                mtime = os.path.getmtime(indexed_path)
                if mtime > indexed_time:
                    # The file has changed, delete it and add it to the list of
                    # files to reindex
                    writer.delete_by_term('path', indexed_path)
                    to_index.add(indexed_path)

        # Loop over the files in the filesystem
        # Assume we have a function that gathers the filenames of the
        # documents to be indexed
        for path in paths:
            path = to_unicode(path)
            if path in to_index or path not in indexed_paths:
                # This is either a file that's changed, or a new file
                # that wasn't indexed before. So index it!
                add_doc(writer, path)

        writer.commit()


def clean_index(dirname, paths):
    """Create the index in the given directory
    """
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    ix = index.create_in(dirname, schema=get_schema())
    writer = ix.writer()

    for path in paths:
        add_doc(writer, path)

    writer.commit()


def do_index(dirname, paths):
    """Create index if it doesn't exist or update it if exists
    """
    if os.path.exists(dirname):
        incremental_index(dirname, paths)
        return
    clean_index(dirname, paths)


def do_search(dirname, expr, page=1):
    """Search for the given expr in the given index path dirname
    """
    ix = index.open_dir(dirname)

    qp = QueryParser("content", schema=ix.schema)
    qp.add_plugin(FuzzyTermPlugin())
    q = qp.parse(u"%(expr)s OR %(expr)s~" % {'expr': expr})

    lis = []
    nb = 0
    with ix.searcher() as s:
        results = s.search_page(q, page, pagelen=HITS_PER_PAGE, terms=True)
        nb = len(results)
        for hit in results:
            lis += [(hit['path'], hit.highlights("content"))]
    return lis, nb
