import os
import sys
import transaction

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
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
    ROLE_ADMIN
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
        admin_user = User(login='admin', password='admin')
        admin_user.roles = [admin_role]
        config = UserConfig(root_path=os.path.normpath(
            '/home/lereskp/temp/waxe/client1'))
        admin_user.config = config
        DBSession.add(admin_user)

        editor_role = Role(name=ROLE_EDITOR)
        editor_user = User(login='editor', password='editor')
        editor_user.roles = [editor_role]
        config = UserConfig(root_path=os.path.normpath(
            '/home/lereskp/temp/waxe/client1'))
        editor_user.config = config
        DBSession.add(editor_user)

        contributor_role = Role(name=ROLE_CONTRIBUTOR)
        contributor_user = User(login='contributor', password='contributor')
        contributor_user.roles = [contributor_role]
        config = UserConfig(root_path=os.path.normpath(
            '/home/lereskp/temp/waxe/client1'), use_versioning=True)
        contributor_user.config = config
        DBSession.add(contributor_user)
