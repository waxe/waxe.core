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
                }
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
                url = url + '?dtd_url=' + dtd_url + '&dtd_tag=' + dtd_tag;
                waxe.update_page(url);
                modal.modal('hide');
            }
        });
    };

    var form_selector = 'form#xmltool-form';

    var exist_form = function(){
        var form = $(form_selector);
        if (form.length)
            return true;
        return false;
    };

    var get_filename = function(){
        return $(form_selector + ' #_xml_filename').val();
    };

    var set_filename = function(value){
        $(form_selector + ' #_xml_filename').val(value);
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
                $(document).scrollTop(0);
                if (data.error_msg){
                    $(document).message('error', data.error_msg);
                    return;
                }
                else if(data.content){
                    var $content = $('.content');
                    $content.html(data.content);
                    waxe.link_events($content);
                    waxe.init_form();
                    if(data.jstree_data){
                        waxe.load_jstree(data.jstree_data);
                    }
                    else{
                        $('body').data('layout').hide('east');
                    }
                    $(document).message('info', 'Loaded!');
                }
                var $breadcrumb = $('.breadcrumb');
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
                var url = '/create-folder.json?path=' + e.path;
                $.ajax({
                     type: 'GET',
                     url: url,
                     dataType: 'json',
                     async: false,
                     success: function(data, textStatus, jqXHR){
                         if(data.status === false){
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
            $('.navbar .dropdown-versioning li a').click(function(e){
                e.preventDefault();
                var url = $(this).data('href');
                if (url !== undefined){
                    waxe.update_page(url);
                }
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
                        $('.breadcrumb').html(data.breadcrumb);
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
                form.xmltool({
                    add_element_url: '/add-element.json',
                    comment_modal_url: '/get-comment-modal.json',
                }).submit(waxe.on_submit_form);
            }
            else{
                // Add css on the save buttons to be clear that these buttons
                // are disabled!
            }
        },
        init_layout: function(){
            $('body').layout({
                applyDemoStyles: true,
                north: {
                    applyDefaultStyles: false,
                    closable: false,
                    resizable: false,
                    pane_spacing: 0,
                    size: 55
                },
                east: {
                    initHidden: true,
                    onresize_end: function(size){
                        var tree = $('#tree');
                        tree.height(tree.parent().parent().height());
                    }
                }
            });
        },
        load_jstree: function(data){
            var tree = $("#tree");
            tree.jstree({
                "json_data" : {'data': [data]},
                "plugins" : ["themes", "json_data", "ui", 'crrm', 'dnd'],
                "core": {
                    html_titles: true
                },
                "ui" : {select_multiple_modifier: false},
                "crrm" : {
                    "move" : {
                        "check_move" : xmltool.jstree.check_move,
                    }
                },
                "dnd" : {
                    "drop_target" : false,
                    "drag_target" : false
                },
            }).bind("select_node.jstree", function (e, data) {
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:'));
                elt.focus();
                var t =  elt.offset().top + $('.ui-layout-center').scrollTop() - $('.ui-layout-center').offset().top - 30;
                $('.ui-layout-center').animate({
                    scrollTop: t,
                    }, 1000
                );
            }).bind("loaded.jstree", function (event, data) {
                tree.jstree('open_all');
                tree.height(tree.parent().parent().height());
                $('body').data('layout').show('east');
            }).bind("move_node.jstree", function(event, data){
                $(document).message('info', 'Moving...', {overlay: true, modal: true});
                setTimeout(function(){
                    xmltool.jstree.move_node(event, data);
                    $(document).message('success', 'Moved!');
                }, 50);
            }).bind('close_node.jstree', function(event, data){
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:'));
                elt.data('togglefieldset').hide(false);
            }).bind('open_node.jstree', function(event, data){
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:'));
                elt.data('togglefieldset').show(false);
            });
        }
    };

    window.onpopstate = function(e) {
        if(e.state != null){
            waxe.update_page(e.state.json_url);
        }
    };

    $(document).ready(function(){
        waxe.link_events($('.content,.breadcrumb'));
        waxe.init_navbar();
        waxe.init_form();
        waxe.init_layout();

        if(typeof(jstree_data) !== 'undefined'){
            waxe.load_jstree(jstree_data);
        }
    });

})(jQuery);

