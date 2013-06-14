from pyramid.security import Everyone, Allow, unauthenticated_userid
import sqlalchemy.orm.exc as sqla_exc
import logging

from .models import User, ROLE_ADMIN, ROLE_EDITOR, ROLE_CONTRIBUTOR

log = logging.getLogger(__name__)


class RootFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'role:%s' % ROLE_ADMIN, ['admin', 'edit']),
        (Allow, 'role:%s' % ROLE_EDITOR, ['edit']),
        (Allow, 'role:%s' % ROLE_CONTRIBUTOR, ['edit']),
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


def get_user_from_request(request):
    login = unauthenticated_userid(request)
    return get_user(login)


def get_root_path_from_request(request):
    if not request.user:
        return None

    if request.user.multiple_account():
        if 'root_path' in request.session:
            return request.session['root_path']

    if not request.user.config:
        return None

    return request.user.config.root_path

