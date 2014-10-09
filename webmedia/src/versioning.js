var waxe = waxe || {};

(function($, ns){
    "use strict";

    ns.versioning = {
        init: function(){

            // Set the versioning status on the files
            var navfile = $('.file-navigation').each(function() {
                var that = this;
                var url = $(that).data('versioning-path');
                if (typeof(url) === 'undefined') {
                    return false;
                }
                waxe.ajax.GET(url, function(data, textStatus, jqXHR){
                    $(that).find('a').each(function() {
                        var status = data[$(this).data('relpath')];
                        if (typeof(status) !== 'undefined') {
                            $(this).parent().addClass('versioning-' + status);
                        }
                    });
                });
            });

            // TODO: put this in python
            $('table.diff td.diff_to').attr('contenteditable', 'true');

            // Reconstruct the file before submitting the diff updated
            $('form.editable-diff').submit(function() {
                $('table.diff').each(function(){
                    $(this).prev('textarea').val('');
                    var html = '';
                    $(this).find('td.diff_to pre').each(function(){
                        $(this).contents().each(function(){
                            html += $(this).text();
                        });
                        html += '\n';
                    });
                    $(this).prev('textarea').val(html);
                });
            });
        }
    };

    $(document).ready(function(){
        waxe.versioning.init();
    });

})(jQuery, waxe);

