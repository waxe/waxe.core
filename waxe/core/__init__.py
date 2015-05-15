import os
import locale

from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from .models import (
    DBSession,
    Base,
)
import taskq.models as taskqm
from .security import RootFactory
from . import config_parser
from . import resource


# Add the modules you want to be include in the config
views_modules = [
    ('waxe.core.views.index', False, True, ''),
    ('waxe.core.views.auth', False, True, ''),
    ('waxe.core.views.filemanager', True, True, ''),
    ('waxe.angular.views.index', False, False, ''),
    ('waxe.txt.views.editor', True, True, 'txt'),
]


def get_views_modules(settings, waxe_editors, waxe_renderers):
    lis = list(views_modules)
    for exts, mod in waxe_editors:
        route_prefix = mod.ROUTE_PREFIX
        lis += [(mod.__name__, True, True, route_prefix)]
    for exts, mod in waxe_renderers:
        route_prefix = mod.ROUTE_PREFIX
        lis += [(mod.__name__, True, True, route_prefix)]
    if 'waxe.versioning' in settings:
        lis += [('waxe.core.views.versioning.views', True, True, 'versioning')]
    return lis


def get_str_resources(request):
    return resource.STR_RESOURCES


def get_js_resources(request):
    lis = resource.JS_RESOURCES
    settings = request.registry.settings
    if 'waxe.extra_js_resources' not in settings:
        return lis
    return lis + settings['waxe.extra_js_resources'].strip().split()


def get_css_resources(request):
    lis = resource.CSS_RESOURCES
    settings = request.registry.settings
    if 'waxe.extra_css_resources' not in settings:
        return lis
    return lis + settings['waxe.extra_css_resources'].strip().split()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # We need to set locale.LC_ALL for pysvn
    language_code, encoding = locale.getdefaultlocale()
    language_code = language_code or 'en_US'
    encoding = encoding or 'UTF8'
    locale.setlocale(locale.LC_ALL, '%s.%s' % (language_code, encoding))

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    # taskq should use the same engine
    taskqm.DBSession.configure(bind=engine)
    taskqm.Base.metadata.bind = engine

    # Get the editors and the extensions supported
    waxe_editors = config_parser.parse_waxe_editors(settings)
    waxe_renderers = config_parser.parse_waxe_renderers(settings)

    # TODO: extensions should be split in both: editor and renderer
    extensions = sum([exts for exts, mod in waxe_editors], [])
    settings['waxe.extensions'] = extensions

    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings['session.key'])
    config = Configurator(settings=settings,
                          session_factory=session_factory,
                          root_factory=RootFactory)
    config.add_static_view('static-core', 'waxe.core:static',
                           cache_max_age=3600)

    config.set_request_property(get_str_resources, 'str_resources', reify=True)
    config.set_request_property(get_js_resources, 'js_resources', reify=True)
    config.set_request_property(get_css_resources, 'css_resources', reify=True)

    for (module, prefix, api, extra_prefix) in get_views_modules(
            settings,
            waxe_editors,
            waxe_renderers):
        route_prefix = None
        if api:
            route_prefix = '/api/1'
        if prefix:
            route_prefix += '/account/{login}'
            if extra_prefix:
                route_prefix += '/%s' % extra_prefix
        else:
            if extra_prefix:
                route_prefix += '/%s' % extra_prefix
        config.include(module, route_prefix=route_prefix)
    return config.make_wsgi_app()
