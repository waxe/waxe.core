if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($){
    "use strict";

    waxe.dom = {
        addPushStateOnLinks: function(container){
            container.find('a[data-href]').click(function(e){
                e.preventDefault();
                window.history.pushState(
                    {'json_url': $(this).data('href')},
                    $(this).text(),
                    $(this).attr('href')
                    );
                waxe.dom.load($(this).data('href'));
            });
        },
        update: function(data){
            $(document).scrollTop(0);
            if (data.error_msg){
                $(document).message('error', data.error_msg);
                return;
            }
            else if(data.content){
                var $content = $('.content');
                $content.html(data.content);
                waxe.dom.addPushStateOnLinks($content);
                waxe.old.init_form();
                waxe.old.init_diff();
                if(data.jstree_data){
                    waxe.old.load_jstree(data.jstree_data);
                }
                else{
                    $('body').data('layout').hide('east');
                }
                $(document).message('info', 'Loaded!');
            }
            var $breadcrumb = $('.breadcrumb');
            if (data.breadcrumb){
                $breadcrumb.html(data.breadcrumb);
                waxe.dom.addPushStateOnLinks($breadcrumb);
            }
            else{
                $breadcrumb.html('');
            }
        },
        load: function(url){
            $(document).message('info', 'Loading...', {'autohide': false});
            waxe.ajax.GET(url, function(data, textStatus, jqXHR){
                waxe.dom.update(data);
            });
        }
     };

})(jQuery, waxe);

