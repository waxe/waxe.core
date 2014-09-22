var waxe = waxe || {};

(function($){
    "use strict";

    waxe.navbar = {};


    var formToObj = function($form) {
        var lis = $form.serializeArray();
        var o = {};
        $.each(lis, function(i, $input) {
            o[$input.name] = $input.value;
        });
        return o;
    };


    var existFile = function($form, filename) {
        var exist = false;
        $form.parents('.waxe-modal-content-saveas').find('.file').each(function(i, link) {
            if (filename === $(link).text()) {
                exist = true;
                return false;
            }
        });
        return exist;
    };

    $(document).on('submit', '.form-saveas', function(e) {
        e.preventDefault();

        var data = formToObj($(this));
        if (! data.name ) {
            // We need at least a name
            return false;
        }

        if(existFile($(this), data.name)) {
            var res = confirm('The file already exists, would you want to overwrite it?');
            if (! res) {
                return false;
            }
        }
        var relpath = data.name;
        if (data.path) {
            relpath = data.path + '/' + data.name;
        }

        waxe.form.setFilename(relpath);
        $(this).parents('.modal').modal('hide');
        // TODO: we should call window.history.pushState
        waxe.form.$element.submit();
    });

    $(document).on('click', '.waxe-modal-content-saveas .file', function(e) {
        e.preventDefault();
        $(this).parents('.waxe-modal-content-saveas').find('.form-saveas input[name="name"]').val($(this).text());
    });



    (function() {

        this.save = function(e, $element) {
            e.preventDefault();
            if (waxe.form.filename){
                waxe.form.$element.submit();
            } else {
                // Not really nice but working :)
                $('.saveas').trigger('click');
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

