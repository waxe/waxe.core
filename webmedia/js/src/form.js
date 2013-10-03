if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($, ns){
    "use strict";

    ns.form = {
        selector: 'form#xmltool-form',
        exist: function(){
            if ($(this.selector).length)
                return true;
            return false;
        },
        getFilename: function(){
            return $(this.selector + ' #_xml_filename').val();
        },
        setFilename: function(value){
            $(this.selector + ' #_xml_filename').val(value);
        },
        init: function(){
            var form = $(waxe.form.selector);
            if (form.length){
                form.xmltool({
                    add_element_url: '/add-element.json',
                    comment_modal_url: '/get-comment-modal.json',
                }).submit(this.on_submit);
                form.on('field_change.xmltool', function(){
                    form.data('status', 'updated');
                });
                this.auto_save();
            }
            else{
                // Add css on the save buttons to be clear that these buttons
                // are disabled!
            }
        },
        on_submit: function(e){
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
        }
    };

    $(document).ready(function(){
        waxe.form.init();
    });

})(jQuery, waxe);
