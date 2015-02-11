def match(request, str_id, dtd_url):
    for plugin in request.xml_plugins:
        if plugin.match(request, str_id, dtd_url):
            return plugin


def add_element(request, str_id, dtd_url):
    plugin = match(request, str_id, dtd_url)
    if not plugin:
        return None
    return plugin.add_element(request, str_id, dtd_url)
