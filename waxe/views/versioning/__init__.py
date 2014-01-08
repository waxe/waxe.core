from pyramid.view import view_config
from pyramid.exceptions import NotFound
from . import pysvn_backend


CALLABLE_VIEWS = [
    'short_status',
    'short_diff',
    'prepare_commit',
    'status',
    'diff',
    'update',
    'commit',
    'update_texts',
]


@view_config(route_name='versioning_dispatcher', renderer='index.mak', permission='edit')
@view_config(route_name='versioning_dispatcher_json', renderer='json', permission='edit')
def versioning_dispatcher(request):
    method = request.matchdict.get('method')
    if not method:
        raise AttributeError('No method for versioning')

    if method not in CALLABLE_VIEWS:
        raise NotFound('Method %s not supported' % method)
    v = pysvn_backend.PysvnView(request)
    return getattr(v, method)()


def includeme(config):
    config.add_route('versioning_dispatcher_json', '/versioning/{method}.json')
    config.add_route('versioning_dispatcher', '/versioning/{method}')
    config.scan(__name__)
