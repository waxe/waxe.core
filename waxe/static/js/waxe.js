$.fn.message.defaults.css.position = 'fixed';
$.fn.message.defaults.css.top = '76px';



(function($){
    "use strict";

    var ajax = {
         GET: function(url, callback){
             $.ajax({
                 type: 'GET',
                 url: url,
                 dataType: 'json',
                 success: function(data, textStatus, jqXHR){
                     callback(data);
                 },
                 error: function(jqXHR, textStatus, errorThrown){
                    var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                    $(document).message('error', msg);
                 }
             });
         }
     };


    var set_tags = function(modal, url, dtd_url){
        // Get the tags for the given dtd_url and update the modal
        ajax.GET(url + '?dtd_url=' + dtd_url, function(data){
                var select = modal.find('.dtd-tags');
                select.html('');
                for(var index in data.tags){
                    var v = data.tags[index];
                    select.append($('<option>').attr('value', v).html(v));
                };
        });
    };

    var set_new_modal_events = function(modal){
        modal.find('.dtd-urls').on('change', function(){
            var val = $(this).val();
            if(val){
                var url = $(this).data('href');
                set_tags(modal, url, val);
            }
        });
        modal.find('.submit').click(function(e){
            e.preventDefault();
            var url = $(this).data('href');
            var dtd_url = modal.find('.dtd-urls').val();
            var dtd_tag = modal.find('.dtd-tags').val();
            if(dtd_url && dtd_tag){
                var url = url + '?dtd_url=' + dtd_url + '&dtd_tag=' + dtd_tag;
                waxe.update_page(url);
                modal.modal('hide');
            }
        })
    };

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
            ajax.GET(url, function(data, textStatus, jqXHR){
                var $section = $('section#section-content');
                $(document).scrollTop(0);
                if (data.error_msg){
                    $(document).message('error', data.error_msg);
                    return;
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
            });
        },
        init_navbar: function(){
            $('.navbar .new').on('click', function(e){
                e.preventDefault();
                var $self = $(this);
                if ($self.data('modal')){
                    $self.data('modal').modal('show');
                }
                else{
                    var url = $self.data('href');
                    ajax.GET(url, function(data){
                        var modal = $(data.content);
                        set_new_modal_events(modal);
                        $self.data('modal', modal);
                        modal.modal();
                    });
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
        waxe.init_navbar();
    });

})(jQuery);

