import os
import locale
import importlib

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
    ('waxe.core.views.index', False, ''),
    ('waxe.core.views.explorer', True, ''),
]


def get_views_modules(settings, waxe_editors, waxe_renderers):
    lis = list(views_modules)
    for exts, mod in waxe_editors:
        route_prefix = mod.ROUTE_PREFIX
        lis += [(mod.__name__, True, route_prefix)]
    for exts, mod in waxe_renderers:
        route_prefix = mod.ROUTE_PREFIX
        lis += [(mod.__name__, True, route_prefix)]
    if 'waxe.versioning' in settings:
        lis += [('waxe.core.views.versioning.views', True, 'versioning')]
    return lis


def get_dtd_urls(request):
    if 'dtd_urls' not in request.registry.settings:
        raise AttributeError('No dtd_urls defined in the ini file.')
    return filter(bool, request.registry.settings['dtd_urls'].split('\n'))


def get_xml_plugins(request):
    if 'waxe.xml.plugins' not in request.registry.settings:
        return []
    lis = filter(bool,
                 request.registry.settings['waxe.xml.plugins'].split('\n'))

    mods = []
    for s in lis:
        mods.append(importlib.import_module(s))
    return mods


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

    cache_timeout = settings.get('xmltool.cache_timeout')
    if cache_timeout:
        os.environ['XMLTOOL_CACHE_TIMEOUT'] = cache_timeout

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    taskqm.DBSession.configure(bind=engine)
    taskqm.Base.metadata.bind = engine

    # Get the editors and the extensions supported
    waxe_editors = config_parser.parse_waxe_editors(settings)
    waxe_renderers = config_parser.parse_waxe_renderers(settings)
    # TODO: extensions should be split in both: editor and renderer
    extensions = sum([exts for exts, mod in waxe_editors], [])
    settings['waxe.extensions'] = extensions

    session_key = settings['session.key']
    session_factory = UnencryptedCookieSessionFactoryConfig(session_key)
    config = Configurator(settings=settings,
                          session_factory=session_factory,
                          root_factory=RootFactory)
    config.add_static_view('static-core', 'waxe.core:static', cache_max_age=3600)

    # TODO: not sure we need to define dtd_urls here.
    config.set_request_property(get_dtd_urls, 'dtd_urls', reify=True)

    config.set_request_property(get_xml_plugins, 'xml_plugins', reify=True)
    config.set_request_property(get_js_resources, 'js_resources', reify=True)
    config.set_request_property(get_css_resources, 'css_resources', reify=True)

    for module, prefix, extra_prefix in get_views_modules(settings,
                                                          waxe_editors,
                                                          waxe_renderers):
        route_prefix = None
        if prefix:
            route_prefix = '/account/{login}'
            if extra_prefix:
                route_prefix += '/%s' % extra_prefix
        else:
            if extra_prefix:
                route_prefix = '/%s' % extra_prefix
        config.include(module, route_prefix=route_prefix)
    return config.make_wsgi_app()
