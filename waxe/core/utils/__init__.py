import re

EOL = '\n'
eol_regex = re.compile(r'\r?\n|\r\n?')


def escape_entities(s):
    """Escape the main entities
    """
    return s.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")


def safe_str(s):
    """We want unicode and UNIX EOL
    """
    s = eol_regex.sub(EOL, s)
    return s.decode('utf-8')
