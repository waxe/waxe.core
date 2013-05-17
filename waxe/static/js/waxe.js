(function($){
    "use strict";

    var waxe = {
        content_events: function(){
            $('section#section-content').each(function(){
                $(this).find('#file-navigation a[data-href]').click(function(){
                    waxe.update_page($(this).data('href'));
                });
            });
        },
        update_page: function(url){
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'json',
                success: function(data, textStatus, jqXHR){
                    $('section#section-content').html(data.content);
                    waxe.content_events();
                },
                error: function(jqXHR, textStatus, errorThrown){
                    alert('Error ajax loading');
                }
            });
        }
    };


    $(document).ready(function(){
        waxe.content_events();
    });

})(jQuery);
