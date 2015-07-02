#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from waxe.core import search, browser

from waxe.core.models import (
    DBSession,
    UserConfig,
)
import  sqla_taskq.models as taskqm


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, name="waxe")
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    taskqm.DBSession.configure(bind=engine)

    if 'whoosh.path' not in settings:
        print 'whoosh_indexes_path not defined in your conf, nothing to do!'
        sys.exit(1)

    whoosh_path = settings['whoosh.path']

    for uc in UserConfig.query.all():
        if not uc.root_path:
            continue
        DBSession.add(uc)
        dirname = uc.user.get_search_dirname(whoosh_path)
        # TODO: support another extensions for the search
        extensions = ['.xml']
        paths = browser.get_all_files(extensions, uc.root_path, uc.root_path)[1]
        # search.do_index(dirname, paths)
        taskqm.Task.create(search.do_index, [dirname, paths],
                    owner=str(uc.user.iduser),
                    unique_key='search_%i' % uc.user.iduser)


if __name__ == '__main__':
    main()
