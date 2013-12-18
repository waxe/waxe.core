var waxe = waxe || {};

(function($, ns){
    "use strict";

    ns.versioning = {
        init: function(){
            var navfile = $('#file-navigation').each(function() {
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

            $('a.select-all').click(function(e){
                e.preventDefault();
                $(this).parents('form').find('input[type="checkbox"]').attr('checked', true);
            });

            $('a.select-none').click(function(e){
                e.preventDefault();
                $(this).parents('form').find('input[type="checkbox"]').removeAttr('checked');
            });

            if ($('table.diff').next('input.diff-submit').length) {
                $('table.diff td.diff_to').attr('contenteditable', 'true');
            }

            $('form.diff').submit(function(e){
                var params = $(this).serialize();
                if (params === ''){
                    // No file selected
                    e.preventDefault();
                }
            });

            $('form.multiple-diff-submit').submit(function(e){
                $(document).message('info', 'Loading...', {'autohide': false});
                e.preventDefault();
                var url = $(this).data('action');
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
                var params = $(this).serialize();
                params = params + '&commit=true';
                $.ajax({
                     type: 'POST',
                     url: url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                        if (data.status){
                            $(document).message('success', 'Saved');
                            var modal = $(data.content);
                            modal.find('.submit').click(function(){
                                var url = $(this).data('href');
                                var msg = modal.find('textarea').val();
                                if (msg !== ''){
                                    params = params + '&msg=' + msg;
                                    waxe.versioning.commit(url, params);
                                    modal.modal('hide');
                                }
                            });
                            modal.modal('show');
                        }
                        else{
                            $(document).message('error', data.error_msg);
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                        $(document).message('error', msg);
                    }
                });
            });

            $('form.multiple-diff').submit(function(e){
                $(document).message('info', 'Loading...', {'autohide': false});
                e.preventDefault();
                var url = $(this).data('action');
                var params = $(this).serialize();
                $.ajax({
                     type: 'POST',
                     url: url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                        waxe.dom.update(data);
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                        $(document).message('error', msg);
                    }
                });
            });
        },
        commit: function(url, params){
            $(document).message('info', 'Commit in progress...', {'autohide': false});
            $.ajax({
                 type: 'POST',
                 url: url,
                 data: params,
                 dataType: 'json',
                 success: function(data, textStatus, jqXHR){
                    if (data.status){
                        $(document).message('success', 'Commit done');
                    }
                    else{
                        $(document).message('error', data.error_msg);
                    }
                },
                error: function(jqXHR, textStatus, errorThrown){
                    var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                    $(document).message('error', msg);
                }
            });
        }
    };

    $(document).ready(function(){
        waxe.versioning.init();
    });

})(jQuery, waxe);

