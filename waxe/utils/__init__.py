import re
import webob


def escape_entities(s):
    """Escape the main entities
    """
    return s.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")
