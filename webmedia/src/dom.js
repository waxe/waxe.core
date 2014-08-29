var waxe = waxe || {};

(function($, ns){
    "use strict";

    var onclick = function(e){
        if (e.isDefaultPrevented()) {
            return false;
        }
        if (waxe.form.status === waxe.form.STATUS_UPDATED) {
            var res = confirm('The file has been updated, continue without saving?');
            if (! res) {
                return false;
            }
        }
        e.preventDefault();
        window.history.pushState(
            {'json_url': $(this).data('href')},
            $(this).text(),
            $(this).attr('href')
            );
        waxe.dom.load($(this).data('href'));
    };
    $(document).on('click', 'a[data-href]', onclick);

    ns.dom = {
        update: function(data, msg){
            msg = typeof msg === 'undefined'? 'Loaded!': msg;

            $('body').data('layout').hide('south');
            $(document).scrollTop(0);

            if ('content' in data){
                var $content = $('.content');
                $content.html(data.content);
                waxe.form.load(data.jstree_data);
                waxe.versioning.init();
                $(document).message('info', msg);
            }

            if ('modal' in data){
                var modal = $(data.modal);
                modal.modal('show');
                $(document).message('info', msg);
            }

            var $breadcrumb = $('.breadcrumb');
            if ('breadcrumb' in data){
                $breadcrumb.html(data.breadcrumb);
            }
            else{
                $breadcrumb.html('');
            }

            if(!('jstree_data' in data)){
                $('body').data('layout').hide('west');
            }

            if (data.error_msg){
                $(document).message('error', data.error_msg);
            }
            else if (data.info_msg){
                $(document).message('info', data.info_msg);
            }

            waxe.dom.loadCodemirror();
        },
        load: function(url){
            $(document).message('info', 'Loading...', {'autohide': false});
            waxe.ajax.GET(url, function(data, textStatus, jqXHR){
                waxe.dom.update(data);
            });
        },
        submit: function(url, params, msg, modal) {
            msg = typeof msg === 'undefined'? 'Updating...': msg;
            $(document).message('info', msg, {'autohide': false});
            waxe.ajax.POST(url, params, function(data, textStatus, jqXHR) {
                waxe.dom.update(data, 'Updated!');
                if (! data.error_msg && typeof(modal) !== 'undefined') {
                    modal.modal('hide');
                }
            });
        },
        loadCodemirror: function() {
            var c = $('.codemirror');
            if (c.length)
            {
                c = c[0];
                if ($(c).css('display') === 'none'){
                    // codemirror seems to be loaded
                    return false;
                }
                var editor = CodeMirror.fromTextArea(c, {
                        mode: {name: "xml"},
                        lineNumbers: true,
                        lineWrapping: true,
                      });
                editor.setSize('auto', 'auto');
                // Make sure the textarea content is updated
                editor.on('blur', function() {
                    c.value = editor.getValue();
                });
                editor.on('focus', function() {
                    // TODO: find a better logic to know if the text has been
                    // updated
                    if(waxe.form.$element) {
                        waxe.form.$element.trigger('field_change.xmltool');
                    }
                });
            }
        },
     };

    $(document).ready(function(){
        waxe.dom.loadCodemirror();

        $(document).on('click', 'form[data-action]', function(e){
            $(this).data('clicked', $(e.target));
        });
        $(document).on('submit', 'form[data-action]', function(e){
            e.preventDefault();
            var $form = $(this);
            var modal = $form.parents('.modal');

            // Since jQuery doesn't include the submit button in the form, we
            // include it manually
            var btn = $form.data('clicked');
            var params = $form.serialize() +
                         '&' + encodeURI(btn.attr('name')) +
                         '=' + encodeURI(btn.attr('value'));
            waxe.dom.submit($form.data('action'),
                            params,
                            $form.data('msg'),
                            modal);
        });

        $(document).on('mouseenter', 'textarea.form-control', function(){
            // TODO: try to find a way to load all the textarea in background
            // or load according to the scroll
            $(this).autosize();
        }).on('focus', 'textarea.form-control', function(){
            $(this).autosize();
        });
    });

})(jQuery, waxe);

