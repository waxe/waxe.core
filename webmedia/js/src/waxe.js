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
        init_diff: function(){

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
                                var msg = modal.find('textarea').val();
                                if (msg !== ''){
                                    params = params + '&msg=' + msg;
                                    waxe.old.commit(params);
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
                        var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + '/update.json';
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
                        var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + '/update.json';
                        $(document).message('error', msg);
                    }
                });
            });
        },
        commit: function(params){
            $(document).message('info', 'Commit in progress...', {'autohide': false});
            $.ajax({
                 type: 'POST',
                 url: '/versioning/commit.json',
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
                    var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + '/versioning/commit.json';
                    $(document).message('error', msg);
                }
            });
        }
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
        waxe.old.init_diff();

    });

})(jQuery);
