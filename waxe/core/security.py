from pyramid.security import (
    Everyone,
    Allow,
    unauthenticated_userid,
    Authenticated
)
import sqlalchemy.orm.exc as sqla_exc
import logging
import bcrypt

from .models import (
    User,
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
    ROLE_SUPERVISOR
)

log = logging.getLogger(__name__)


class RootFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'authenticated'),
        (Allow, 'role:%s' % ROLE_ADMIN, ['admin', 'edit']),
        (Allow, 'role:%s' % ROLE_EDITOR, ['editor', 'edit']),
        (Allow, 'role:%s' % ROLE_CONTRIBUTOR, ['contributor', 'edit']),
        (Allow, 'role:%s' % ROLE_SUPERVISOR, ['supervisor', 'edit']),
        (Allow, 'ldap:waxe_admin', ['admin', 'edit']),
        (Allow, 'ldap:waxe_editor', ['editor', 'edit']),
        (Allow, 'ldap:waxe_contributor', ['contributor', 'edit']),
        (Allow, 'ldap:waxe_supervisor', ['supervisor', 'edit']),
    ]

    def __init__(self, request):
        pass


def get_user(login):
    if not login:
        return None
    try:
        return User.query.filter_by(login=login).one()
    except sqla_exc.NoResultFound:
        pass
    except sqla_exc.MultipleResultsFound, e:
        log.exception(e)


def validate_password(request, login, password):
    user = get_user(login)
    if not user:
        return False
    if not user.password or not password:
        # A define and valid password can't be empty
        return False
    try:
        if bcrypt.checkpw(password.encode('utf8'), user.password.encode('utf8')):
            return user
    except ValueError:
        # Can fail if the value in the DB is not bcrypted.
        pass
    return False


def get_user_permissions(login, request):
    user = get_user(login)
    if not user:
        return []
    permissions = ['role:%s' % role.name for role in user.roles]
    return permissions


def get_userid_from_request(request):
    return unauthenticated_userid(request)
