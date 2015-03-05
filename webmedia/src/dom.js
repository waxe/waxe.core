var waxe = waxe || {};

waxe.cache = {
    open: null,
    saveas: null,
};

(function($, ns){
    "use strict";


    // This event should be called first since we also have data-href on some
    // elements
    $(document).on('click', '[data-call]', function(e) {

        if ($(this).hasClass('event-disabled')) {
            return false;
        }

        var call = $(this).data('call');
        var fun = waxe;
        call.split('.').map(function(s){ fun=fun[s];});
        fun(e, $(this));
    });


    $(document).on('click', '[data-cache]', function(e) {
        var $this = $(this);
        var call = $(this).data('cache');
        var fun = waxe;
        call.split('.').map(function(s){ fun=fun[s];});
        if (fun) {
            $this.attr('data-params', 'path=' + fun);
        }
    });

    var updateModal = function($modal, data) {
        $(document).message('close');
        if (data.error_msg){
            $(document).message('error', data.error_msg);
            return false;
        }
        if (data.content) {
            $modal.find('.waxe-modal-content').html(data.content);
        }
        if (data.breadcrumb) {
            $modal.find('.waxe-modal-breadcrumb').html(data.breadcrumb);
        }
        else {
            $modal.find('.waxe-modal-breadcrumb').html('');
        }
        if (data.relpath) {
            // Need for the search.
            $modal.find('.relpath').val(data.relpath);
        }
        if (data.cache) {
            for(var k in data.cache) {
                ns.cache[k] = data.cache[k];
            }
        }
    };


    $(document).on('click', '[data-modal-href]', function(e) {
        e.preventDefault();

        if ($(this).hasClass('event-disabled')) {
            return false;
        }
        var $this = $(this),
            $modal = $(this).parents('.modal'),
            url = $(this).data('modal-href');
        waxe.ajax.GET(url, function(data, textStatus, jqXHR){
            updateModal($modal, data);
        });
    });

    $(document).on('submit', 'form[data-modal-action]', function(e){
        e.preventDefault();
        var $this = $(this),
            $modal = $this.parents('.modal'),
            url = $this.data('modal-action');

        var params = $this.serialize();
        waxe.ajax.POST(url, params, function(data, textStatus, jqXHR){
            updateModal($modal, data);
        });
    });


    var onclick = function(e){
        if (e.isDefaultPrevented()) {
            return false;
        }

        var $this = $(this);
        if ($this.hasClass('event-disabled')) {
            return false;
        }

        if (waxe.form.status === waxe.form.STATUS_UPDATED) {
            var res = confirm('The file has been updated, continue without saving?');
            if (! res) {
                return false;
            }
        }
        e.preventDefault();
        if ($this.attr('href')) {
            // Don't pushState if we don't have attribute href, since it's only
            // json link.
            waxe.dom.pushState($this.attr('href'), $this.data('href'), $this.text());
        }
        var modal = $this.parents('.modal');
        var href = $this.data('href');
        var params = $this.attr('data-params');
        if(params) {
            href += '?' + params;
        }
        waxe.dom.load(href, modal, $this);
    };

    $(document).on('click', 'a[data-href]', onclick);

    ns.dom = {
        pushState: function(url, data_url, text) {
            window.history.pushState(
                {'json_url': data_url},
                text,
                url
            );
        },
        update: function(data, msg, scrolltop){
            msg = typeof msg === 'undefined'? 'Loaded!': msg;
            scrolltop = typeof scrolltop === 'undefined'? true: scrolltop;

            // TODO: improve message to not do this
            $(document).message('close');

            waxe.layout.hideReadonly();
            if (scrolltop) {
                $(document).scrollTop(0);
                $('.ui-layout-center').scrollTop(0);
            }

            if (data.error_msg){
                $(document).message('error', data.error_msg);
            }
            else if (data.info_msg){
                $(document).message('info', data.info_msg);
            }

            if ('redirect_url' in data) {
                waxe.dom.load(data['redirect_url']);
                return;
            }

            if ('content' in data){
                var $content = $('.content');
                $content.html(data.content);
                waxe.form.load(data.jstree_data);
                var $form = $('.form-save');
                if ($form.length) {
                    $('.save').removeClass('event-disabled').parent('li').removeClass('disabled');
                }
                waxe.versioning.init();
                $(document).message('info', msg);
            }

            if ('modal' in data){
                var modal = $(data.modal);
                modal.modal('show');
                $(document).message('info', msg);
                // It's a modal we shouldn't update the next parts
                return false;
            }

            var $breadcrumb = $('.breadcrumb');
            if ('breadcrumb' in data){
                $breadcrumb.html(data.breadcrumb);
            }
            else{
                $breadcrumb.html('');
            }

            var $nav_editor = $('.nav-editor');
            if ('nav_editor' in data){
                $nav_editor.html(data.nav_editor);
            }
            else{
                $nav_editor.html('');
            }


            var xtForm = $('#xmltool-form');
            if (xtForm.length === 0 || xtForm.hasClass('no-tree')){
                waxe.layout.hideTree();
            }
            else {
                waxe.layout.showTree();
            }


            waxe.dom.loadCodemirror();
        },
        load: function(url, modal){
            $(document).message('info', 'Loading...', {'autohide': false});
            waxe.ajax.GET(url, function(data, textStatus, jqXHR){
                waxe.dom.update(data);
                if (! data.error_msg && typeof(modal) !== 'undefined') {
                    modal.modal('hide');
                }
            });
        },
        submit: function(url, params, msg, doneMsg, modal) {
            msg = typeof msg === 'undefined'? 'Updating...': msg;
            doneMsg = typeof doneMsg === 'undefined'? 'Updated!': doneMsg;
            $(document).message('info', msg, {'autohide': false});
            waxe.ajax.POST(url, params, function(data, textStatus, jqXHR) {
                waxe.dom.update(data, doneMsg, false);
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

        $(document).on('click', 'form[data-action] [type=submit]', function(e){
            $(this).parents('form').data('clicked', $(e.target));
        });
        $(document).on('submit', 'form[data-action]', function(e){
            e.preventDefault();
            var $form = $(this),
                modal = $form.parents('.modal'),
                params = $form.serialize(),
                $btn = $form.data('clicked');
            if ($btn) {
                // Since jQuery doesn't include the submit button in the form,
                // we include it manually if a submit button has been clicked.
                // It's usefull when we make full diff to only save updates
                // without commiting.
                params = params +
                         '&' + encodeURI($btn.attr('name')) +
                         '=' + encodeURI($btn.attr('value'));
            }
            waxe.dom.submit($form.data('action'),
                            params,
                            $form.data('msg'),
                            $form.data('donemsg'),
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

