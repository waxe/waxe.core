var waxe = waxe || {};

(function($, ns){
    "use strict";

    var onclick = function(e){
        e.preventDefault();
        window.history.pushState(
            {'json_url': $(this).data('href')},
            $(this).text(),
            $(this).attr('href')
            );
        waxe.dom.load($(this).data('href'));
    };

    ns.dom = {
        addPushStateOnLinks: function(container){
            container.find('a[data-href]').click(onclick);
        },
        update: function(data, msg){
            msg = typeof msg === 'undefined'? 'Loaded!': msg;
            $(document).scrollTop(0);

            if ('content' in data){
                var $content = $('.content');
                $content.html(data.content);
                waxe.dom.addPushStateOnLinks($content);
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
                waxe.dom.addPushStateOnLinks($breadcrumb);
            }
            else{
                $breadcrumb.html('');
            }

            if(!('jstree_data' in data)){
                $('body').data('layout').hide('east');
            }

            if (data.error_msg){
                $(document).message('error', data.error_msg);
            }
            else if (data.info_msg){
                $(document).message('info', data.info_msg);
            }

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
        }
     };

    $(document).ready(function(){
        waxe.dom.addPushStateOnLinks($('.content,.breadcrumb,.navbar .dropdown-versioning'));
        $(document).on('submit', 'form[data-action]', function(e){
            e.preventDefault();
            var $form = $(this);
            var modal = $form.parents('.modal');
            waxe.dom.submit($form.data('action'),
                            $form.serialize(),
                            $form.data('msg'),
                            modal);
        });
    });

})(jQuery, waxe);

