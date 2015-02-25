import importlib


def _parse_waxe_modules(settings, propname):
    modules = filter(bool, settings.get(propname, '').split('\n'))
    lis = []
    for mod in modules:
        m = importlib.import_module(mod)
        if '#' in mod:
            mod, ext = mod.split('#')
            exts = ext.split(',')
        else:
            exts = m.EXTENSIONS

        lis += [(exts, m)]

    extensions = sum([l for l, d in lis], [])
    if len(extensions) != len(set(extensions)):
        raise Exception('An extension is defined in many waxe modules', lis)

    return lis


def parse_waxe_editors(settings):
    return _parse_waxe_modules(settings, 'waxe.editors')


def parse_waxe_renderers(settings):
    return _parse_waxe_modules(settings, 'waxe.renderers')
