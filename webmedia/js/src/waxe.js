if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($){
    "use strict";

    waxe.old = {
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
                        $(waxe.form.selector).removeData('status');
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
            var form = $(waxe.form.selector);
            if (form.length){
                form.xmltool({
                    add_element_url: '/add-element.json',
                    comment_modal_url: '/get-comment-modal.json',
                }).submit(waxe.old.on_submit_form);
                form.on('field_change.xmltool', function(){
                    form.data('status', 'updated');
                });
                waxe.old.auto_save();
            }
            else{
                // Add css on the save buttons to be clear that these buttons
                // are disabled!
            }
        },
        auto_save: function(){
            var form = $(waxe.form.selector);
            var save = function(){
                if (form.data('status') === 'updated'){
                    form.submit();
                    form.removeData('status');
                }
            };
            // TODO: improve this logic for the new files!
            if (form.length && waxe.form.getFilename()){
                setInterval(save, 1000 * 60);
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
    };

    window.onpopstate = function(e) {
        if(e.state !== null){
            waxe.dom.load(e.state.json_url);
        }
    };

    $(document).ready(function(){
        window.onbeforeunload = function(event) {
            var form = $(waxe.form.selector);
            if(form.data('status') === 'updated'){

            event = event || window.event;
            var confirmClose = 'The file has been updated, are you sure you want to exit?';
            if (event) {
                event.returnValue = confirmClose;
            }
            // For safari
            return confirmClose;
            }
        };
        waxe.dom.addPushStateOnLinks($('.content,.breadcrumb,.navbar .dropdown-versioning'));
        waxe.old.init_form();
        waxe.old.init_layout();

    });

})(jQuery);
