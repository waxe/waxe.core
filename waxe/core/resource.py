JS_RESOURCES = []
CSS_RESOURCES = []


def add_js_resource(resource):
    """Add a javascript resource
    """
    global JS_RESOURCES
    if resource not in JS_RESOURCES:
        JS_RESOURCES += [resource]


def add_css_resource(resource):
    """Add a css resource
    """
    global CSS_RESOURCES
    if resource not in CSS_RESOURCES:
        CSS_RESOURCES += [resource]
