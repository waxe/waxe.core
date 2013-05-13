from pyramid.security import Everyone, Allow
import sqlalchemy.orm.exc as sqla_exc
import logging

from .models import User

log = logging.getLogger(__name__)


class RootFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'role:admin', ['admin', 'edit']),
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


def validate_password(login, password):
    user = get_user(login)
    if not user:
        return False
    return user.password == password


def get_user_permissions(login, request):
    user = get_user(login)
    if not user:
        return []
    permissions = ['role:%s' % role.name for role in user.roles]
    permissions += ['group:%s' % group.name for group in user.groups]
    return permissions

