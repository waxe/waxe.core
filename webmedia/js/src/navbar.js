if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($, ns){
    "use strict";

    var set_tags = function(modal, url, dtd_url){
        // Get the tags for the given dtd_url and update the modal
        waxe.ajax.GET(url + '?dtd_url=' + dtd_url, function(data){
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
                waxe.dom.load(url);
                modal.modal('hide');
            }
        });
    };


    ns.navbar = {
        'new': function(){
            $('.navbar .new').on('click', function(e){
                e.preventDefault();
                var $self = $(this);
                if ($self.data('modal')){
                    $self.data('modal').modal('show');
                }
                else{
                    var url = $self.data('href');
                    waxe.ajax.GET(url, function(data){
                        var modal = $(data.content);
                        set_new_modal_events(modal);
                        $self.data('modal', modal);
                        modal.modal();
                    });
                }
            });
        },
        open: function(){
            $('.navbar .open').filebrowser({
                url: '/open.json',
                title: 'Open file'
            }).bind('select', function(e){
                waxe.dom.load(e.href);
            });
        },
        saveas: function(){
            $('.navbar .saveas').filebrowser({
                url: '/open.json',
                text: {
                    title: 'Save file',
                    submit: 'Save',
                },
                type: 'save'
            }).bind('before_open', function(e){
                if(!waxe.form.exist())
                    e.preventDefault();
            }).bind('select', function(e){
                waxe.form.setFilename(e.href);
                $(waxe.form.selector).submit();
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
        },
        save: function(){
            $('.navbar .save').click(function(e){
                e.preventDefault();
                if(waxe.form.exist()){
                    if (waxe.form.getFilename()){
                        $(waxe.form.selector).submit();
                    } else {
                        $('.navbar .saveas').trigger('click');
                    }
                }
            });
        }
    };

    $(document).ready(function(){
        for (var key in waxe.navbar){
            console.log(key);
            waxe.navbar[key]();
        }
    });

})(jQuery, waxe);

