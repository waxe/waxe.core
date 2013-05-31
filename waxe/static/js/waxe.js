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

    var form_selector = 'form#xmltool-form';

    var exist_form = function(){
        var form = $(form_selector);
        if (form.length)
            return true;
        return false;
    }

    var get_filename = function(){
        return $(form_selector + ' #_xml_filename').val();
    }

    var set_filename = function(value){
        $(form_selector + ' #_xml_filename').val(value);
    }

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
                    waxe.init_form();
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

            $('.navbar .open').filebrowser({
                url: '/open.json',
                title: 'Open file'
            }).bind('select', function(e){
                waxe.update_page(e.href);
            });

            $('.navbar .saveas').filebrowser({
                url: '/open.json',
                text: {
                    title: 'Save file',
                    submit: 'Save',
                },
                type: 'save'
            }).bind('before_open', function(e){
                if(!exist_form())
                    e.preventDefault();
            }).bind('select', function(e){
                set_filename(e.path);
                $(form_selector).submit();
            }).bind('create_folder', function(e){
                var url = '/create-folder.json?path=' + e.path
                $.ajax({
                     type: 'GET',
                     url: url,
                     dataType: 'json',
                     async: false,
                     success: function(data, textStatus, jqXHR){
                         if(data.status == false){
                            e.preventDefault();
                            $(document).message('error', data.error_msg);
                         }
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                        $(document).message('error', msg);
                    }
                });
            });
            $('.navbar .save').click(function(e){
                e.preventDefault();
                if(exist_form())
                    $(form_selector).submit();
            });
        },
        on_submit_form: function(e){
            e.preventDefault();
            var params = $(this).serialize();
            $.ajax({
                 type: 'POST',
                 url: '/update.json',
                 data: params,
                 dataType: 'json',
                 success: function(data, textStatus, jqXHR){
                    if (data.status){
                        $(document).message('success', 'Saved');
                        $('section#section-breadcrumb').html(data.breadcrumb);
                    }
                    else{
                        $(document).message('error', data.error_msg);
                    }
                },
                error: function(jqXHR, textStatus, errorThrown){
                    var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + '/update.json';
                    $(document).message('error', msg);
                }
            });
        },
        init_form: function(){
            var form = $(form_selector);
            if (form.length){
                form.submit(waxe.on_submit_form);
            }
            else{
                // Add css on the save buttons to be clear that these buttons
                // are disabled!
            }
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
        waxe.init_form();
    });

})(jQuery);

