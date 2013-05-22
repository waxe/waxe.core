from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from .models import (
    DBSession,
    Base,
    )
from .security import (
    get_user_permissions,
    RootFactory,
    get_user_from_request,
    get_root_path_from_request,
)

# Add the modules you want to be include in the config
views_modules = [
    'waxe.views.index',
]


def get_dtd_urls(request):
    if 'dtd_urls' not in request.registry.settings:
        raise AttributeError, 'No dtd_urls defined in the ini file.'
    return filter(bool, request.registry.settings['dtd_urls'].split('\n'))


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    session_key = settings['session.key']
    session_factory = UnencryptedCookieSessionFactoryConfig(session_key)
    config = Configurator(settings=settings,
                          session_factory=session_factory,
                          root_factory=RootFactory)
    config.add_static_view('static', 'static', cache_max_age=3600)

    # Authentification
    authentication_policy = AuthTktAuthenticationPolicy(
        settings['authentication.key'],
        callback=get_user_permissions,
        debug=settings['authentication.debug'],
        hashalg='sha512',
        )
    authorization_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)
    config.set_request_property(get_user_from_request, 'user', reify=True)
    config.set_request_property(get_root_path_from_request,
                                'root_path', reify=True)
    config.set_request_property(get_dtd_urls, 'dtd_urls', reify=True)

    for module in views_modules:
        config.include(module)
    return config.make_wsgi_app()

