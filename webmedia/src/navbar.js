var waxe = waxe || {};

(function($){
    "use strict";

    waxe.navbar = {};

    (function() {

        this.open = function(e, $element) {
            if(typeof $element.data('filebrowser') === 'undefined') {
                $element.filebrowser({
                    url: $element.data('fb-href'),
                    title: 'Open file'
                }).bind('select', function(e){
                    waxe.dom.load(e.href);
                });
            }
        };

        this.save = function(e, $element) {
            e.preventDefault();
            if (waxe.form.filename){
                waxe.form.$element.submit();
            } else {
                // Not really nice but working :)
                $('.saveas').trigger('click');
            }
        };

        this.saveas = function(e, $element) {
            if(typeof $element.data('filebrowser') === 'undefined') {
                var that = this;
                $element.filebrowser({
                    url: $element.data('fb-href'),
                    text: {
                        title: 'Save file',
                        submit: 'Save',
                    },
                    type: 'save'
                }).bind('before_open', function(e){
                    if(!waxe.form.$element) {
                        e.preventDefault();
                    }
                }).bind('select', function(e){
                    waxe.form.setFilename(e.href);
                    // TODO: we should call window.history.pushState
                    waxe.form.$element.submit();
                }).bind('create_folder', function(e){
                    var url = $element.data('fb-folder-href') + '?path=' + e.path;
                    waxe.ajax.GET(url, function(data){
                        if(data.status === false){
                           e.preventDefault();
                           $(document).message('error', data.error_msg);
                        }
                    }, false); // Not asynchronious
                });
            }
        };

        this.split = function(e, $element) {
            e.preventDefault();
            if (waxe.form.filename){
                var iframe = $('<iframe frameborder="0">');
                iframe.css({width: '100%', height: '100%'});
                iframe.attr('src', $element.data('href') + '?iframe=1&path=' + waxe.form.filename);
                waxe.layout.updateReadonly(iframe);
                waxe.layout.showReadonly();
            }
        };
    }).apply(waxe.navbar);


})(jQuery);

