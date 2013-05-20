$.fn.message.defaults.css.position = 'fixed';
$.fn.message.defaults.css.top = '76px';



(function($){
    "use strict";

    var waxe = {
        link_events: function(container){
            container.find('a[data-href]').click(function(e){
                e.preventDefault();
                window.history.pushState(
                    {'json_url': $(this).data('href')},
                    $(this).text(),
                    $(this).attr('href')
                    );
                waxe.update_page($(this).data('href'));
            });
        },
        update_page: function(url){
            $(document).message('info', 'Loading...', {'autohide': false});
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'json',
                success: function(data, textStatus, jqXHR){
                    var $section = $('section#section-content');
                    $(document).scrollTop(0);
                    if (data.error_msg){
                        $(document).message('error', data.error_msg);
                    }
                    else if(data.content){
                        var $content = $section.find('.content');
                        $content.html(data.content);
                        waxe.link_events($content);
                        $(document).message('info', 'Loaded!');
                    }
                    var $breadcrumb = $section.find('.breadcrumb');
                    if (data.breadcrumb){
                        $breadcrumb.html(data.breadcrumb);
                        waxe.link_events($breadcrumb);
                    }
                    else{
                        $breadcrumb.html('');
                    }
                },
                error: function(jqXHR, textStatus, errorThrown){
                    var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                    $(document).message('error', msg);
                }
            });
        }
    };

    window.onpopstate = function(e) {
        if(e.state != null){
            waxe.update_page(e.state.json_url);
        }
    };

    $(document).ready(function(){
        waxe.link_events($('section#section-content'));
    });

})(jQuery);

