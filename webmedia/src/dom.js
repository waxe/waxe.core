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
        update: function(data){
            $(document).scrollTop(0);

            if (data.error_msg){
                $(document).message('error', data.error_msg);
                return;
            }

            if ('content' in data){
                var $content = $('.content');
                $content.html(data.content);
                waxe.dom.addPushStateOnLinks($content);
                waxe.form.load();
                waxe.versioning.init();
                $(document).message('info', 'Loaded!');
            }

            var $breadcrumb = $('.breadcrumb');
            if ('breadcrumb' in data){
                $breadcrumb.html(data.breadcrumb);
                waxe.dom.addPushStateOnLinks($breadcrumb);
            }
            else{
                $breadcrumb.html('');
            }

            if('jstree_data' in data){
                waxe.jstree.load(data.jstree_data);
            }
            else{
                $('body').data('layout').hide('east');
            }
        },
        load: function(url){
            $(document).message('info', 'Loading...', {'autohide': false});
            waxe.ajax.GET(url, function(data, textStatus, jqXHR){
                waxe.dom.update(data);
            });
        }
     };

    $(document).ready(function(){
        waxe.dom.addPushStateOnLinks($('.content,.breadcrumb,.navbar .dropdown-versioning'));
    });

})(jQuery, waxe);
