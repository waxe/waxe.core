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
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
)


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
