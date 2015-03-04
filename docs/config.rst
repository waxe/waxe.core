Configuration options
#####################


``waxe.extra_js_resources``

    Default: ``None``. The list of extra javascript resources to include in the
    HTML.

``waxe.extra_css_resources``

    Default: ``None``. The list of extra css resources to include in the HTML.

``waxe.editors``

    Default: ``None``. The list of editors available. Each editor should handle
    at least one extension

``waxe.renderers``

    Default: ``None``. The list of renderers available. Each renderer should handle at least one extension.

``waxe.xml.xmltool.renderer_func``

    Default: ``None``. Function which returns the XML renderer to use. The login of the user is passed as parameter.
    List of predefined renderer in xmltool:
        * xmltool.render.Render: (Default renderer) the editable parts are in a textarea
        * xmltool.render.ContenteditableRender: the editable parts are in a div with contenteditable activated.
        * xmltool.render.CKeditorRender: CKEditor is to use to edit.
        * xmltool.render.ReadonlyRender: The parts are not editable.

``waxe.xml.plugins``

    Default: ``None``. List of plugin to use in waxe.xml.

``waxe.versioning.get_svn_username``

    Default: ``None``. Function which returns the svn username to use for authentiction. By default we use the user login.

``waxe.versioning``

    Default: ``false``. Should be true if you want to use versioning


``xmltool.cache_timeout``

    Default: ``None``. If you want to put a cache in milliseconds in xmltool, set an integer.
