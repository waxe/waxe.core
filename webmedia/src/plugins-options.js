(function($){
    "use strict";
    $.fn.message.defaults.css.position = 'fixed';
    $.fn.message.defaults.css['z-index'] = 2000;
    $.fn.message.defaults.template.message = '<div class="alert">\
      <button type="button" class="close">&times;</button>\
      <span class="text"/>\
    </div>';
    $.fn.message.defaults.extra_class = {
        info: 'alert-info',
        success: 'alert-success',
        error: 'alert-error'
    };
    $.fn.message.defaults.selector.close_btn = '.close';

    $.fn.filebrowser.defaults.template.nav_file = '<li><i class="icon-file"></i></li>';
    $.fn.filebrowser.defaults.template.nav_folder = '<li><i class="icon-folder-close"></i></li>';
})(jQuery);
