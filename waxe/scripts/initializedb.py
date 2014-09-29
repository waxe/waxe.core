import os
import sys
import transaction
import bcrypt

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from ..models import (
    DBSession,
    Base,
    Role,
    User,
    UserConfig,
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
)

import taskq.models as taskqm


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
    Base.metadata.create_all(engine)
    taskqm.DBSession.configure(bind=engine)
    taskqm.Base.metadata.create_all(engine)
    with transaction.manager:
        admin_role = Role(name=ROLE_ADMIN)
        pwd = bcrypt.hashpw('admin', bcrypt.gensalt())
        admin_user = User(login='admin',
                          password=pwd)
        admin_user.roles = [admin_role]
        DBSession.add(admin_user)

        editor_role = Role(name=ROLE_EDITOR)
        DBSession.add(editor_role)
        contributor_role = Role(name=ROLE_CONTRIBUTOR)
        DBSession.add(contributor_role)

        lereskp_user = User(login='lereskp', password=pwd)
        lereskp_user.config = UserConfig(
            root_path='/home/lereskp/temp/waxe/client1',
            use_versioning=True
        )
        lereskp_user.roles = [editor_role]
        DBSession.add(lereskp_user)

        editor_user = User(login='editor', password=pwd)
        editor_user.config = UserConfig(
            root_path='/home/lereskp/temp/waxe/client1',
            use_versioning=True
        )
        editor_user.roles = [editor_role]
        DBSession.add(editor_user)

        contributor_user = User(login='contributor', password=pwd)
        contributor_user.config = UserConfig(
            root_path='/home/lereskp/temp/waxe/client1',
            root_template_path='/home/lereskp/temp/waxe/client1/templates',
            use_versioning=True
        )
        contributor_user.roles = [contributor_role]
        DBSession.add(contributor_user)
