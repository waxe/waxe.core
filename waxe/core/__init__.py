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

# Add the modules you want to be include in the config
views_modules = [
    ('waxe.core.views.index', False, ''),
    ('waxe.core.views.explorer', True, ''),
]


def parse_waxe_editors(settings):
    modules = filter(bool, settings.get('waxe.editors', '').split('\n'))
    lis = []
    for mod in modules:
        if '#' in mod:
            mod, ext = mod.split('#')
            exts = ext.split(',')
        else:
            exts = importlib.import_module(mod).EXTENSIONS

        lis += [(mod, exts)]

    # TODO: check conflict between extensions
    return lis


def get_views_modules(settings, waxe_editors):
    lis = list(views_modules)
    for mod, exts in waxe_editors:
        lis += [('%s.views.editor' % mod, True, '')]
    if 'versioning' in settings:
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
    waxe_editors = parse_waxe_editors(settings)
    extensions = sum([exts for mod, exts in waxe_editors], [])
    settings['waxe.extensions'] = extensions

    session_key = settings['session.key']
    session_factory = UnencryptedCookieSessionFactoryConfig(session_key)
    config = Configurator(settings=settings,
                          session_factory=session_factory,
                          root_factory=RootFactory)
    config.add_static_view('static', 'waxe.core:static', cache_max_age=3600)
    # TODO: not sure we need to define dtd_urls here.
    config.set_request_property(get_dtd_urls, 'dtd_urls', reify=True)

    config.set_request_property(get_xml_plugins, 'xml_plugins', reify=True)

    for module, prefix, extra_prefix in get_views_modules(settings,
                                                          waxe_editors):
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
