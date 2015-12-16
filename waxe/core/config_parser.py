import importlib


def _parse_waxe_modules(settings, propname):
    modules = filter(bool, settings.get(propname, '').split('\n'))
    lis = []
    for mod in modules:
        if '#' in mod:
            mod, ext = mod.split('#')
            m = importlib.import_module(mod)
            splits = ext.split(',')
            exts = []
            for e in splits:
                e = e.strip()
                if not e.startswith('.'):
                    e = '.%s' % e
                exts.append(e)
        else:
            m = importlib.import_module(mod)
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
