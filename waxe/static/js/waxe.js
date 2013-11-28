/*! Waxe - v0.1.0 - 2013-11-28
* https://github.com/LeResKP/waxe
* Copyright (c) 2013 Aurélien Matouillot; Licensed MIT */
var waxe = waxe || {};

(function($, ns){
    "use strict";


    var ajax = function(type, url, callback, data, async){
        async = typeof async === 'undefined'? true: async;
        $.ajax({
            type: type,
            url: url,
            async: async,
            data: data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                callback(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                // TODO: make sure this error message is nice!
                var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                $(document).message('error', msg);
            }
        });
    };

    ns.ajax = {
         GET: function(url, callback, async){
             ajax('GET', url, callback, null, async);
         },
         POST: function(url, data, callback, async){
             ajax('POST', url, callback, data, async);
         }
     };
})(jQuery, waxe);

var waxe = waxe || {};

(function($, ns){
    "use strict";

    var onclick = function(e){
        e.preventDefault();
        window.history.pushState(
            {'json_url': $(this).data('href')},
            $(this).text(),
            $(this).attr('href')
            );
        waxe.dom.load($(this).data('href'));
    };

    ns.dom = {
        addPushStateOnLinks: function(container){
            container.find('a[data-href]').click(onclick);
        },
        update: function(data){
            $(document).scrollTop(0);

            if (data.error_msg){
                $(document).message('error', data.error_msg);
                return;
            }

            if ('content' in data){
                var $content = $('.content');
                $content.html(data.content);
                waxe.dom.addPushStateOnLinks($content);
                waxe.form.load(data.jstree_data);
                waxe.versioning.init();
                $(document).message('info', 'Loaded!');
            }

            var $breadcrumb = $('.breadcrumb');
            if ('breadcrumb' in data){
                $breadcrumb.html(data.breadcrumb);
                waxe.dom.addPushStateOnLinks($breadcrumb);
            }
            else{
                $breadcrumb.html('');
            }

            if(!('jstree_data' in data)){
                $('body').data('layout').hide('east');
            }
        },
        load: function(url){
            $(document).message('info', 'Loading...', {'autohide': false});
            waxe.ajax.GET(url, function(data, textStatus, jqXHR){
                waxe.dom.update(data);
            });
        }
     };

    $(document).ready(function(){
        waxe.dom.addPushStateOnLinks($('.content,.breadcrumb,.navbar .dropdown-versioning'));
    });

})(jQuery, waxe);


var waxe = waxe || {};

(function($, ns){
    "use strict";


    var Form = function(jstreeData){
        this.selector = 'form#xmltool-form';
        this.filename_selector = '#_xml_filename';
        this.$element = null;
        this.status = null;
        this.$filename = null;
        this.auto_save_interval = null;
        this.auto_save_time = 1000 * 60;
        this.load(jstreeData);
    };

    Form.STATUS_UPDATED = 'updated';

    Form.prototype.load = function(jstreeData){
        var that = this;
        this.$element = null;
        this.status = null;
        this.$filename = null;
        var $e = $(this.selector);
        clearInterval(this.auto_save_interval);
        if(!$e.length) {
            // Add css on the save buttons to be clear that these buttons
            // are disabled!
            return false;
        }
        this.$element = $e;
        // We assume we always have the hidden input in the form
        this.$filename = $e.find(this.filename_selector);
        this.filename = this.$filename.val();
        this.$element.xmltool({
            add_element_url: this.$element.data('add-href'),
            comment_modal_url: this.$element.data('comment-href'),
            jstreeSelector: '#tree',
            jstreeData: jstreeData,
            message: function(){
                var d = $(document);
                d.message.apply(d, arguments);
            },
            treeContainerSelector: '.ui-layout-center'
        }).submit($.proxy(this.save, this)).on('loadedJstree', function(){
            $('body').data('layout').show('east');
        });
        this.$element.on('field_change.xmltool', function(){
            that.status = that.STATUS_UPDATED;
        });
        this.auto_save();
        return true;
    };

    Form.prototype.setFilename = function(v){
        if (this.$element) {
            this.$filename.val(v);
            this.filename = v;
            return true;
        }
        return false;
    };

    Form.prototype.save = function(e){
        if(!this.$element) {
            return false;
        }
        e.preventDefault();
        var that = this;
        var params = this.$element.serialize();
        waxe.ajax.POST(this.$element.data('href'), params, function(data){
            if (data.status){
                that.status = null;
                $(document).message('success', 'Saved');
                // TODO: we should use waxe.dom to update the content!
                $('.breadcrumb').html(data.breadcrumb);
            }
            else{
                $(document).message('error', data.error_msg);
            }
        });
    };

    Form.prototype.auto_save = function(){
        var that = this;
        var save = function(){
            if (that.status === that.STATUS_UPDATED){
                that.$element.submit();
                that.status = null;
            }
        };
        // TODO: improve this logic for the new files!
        if (this.filename){
            this.auto_save_interval = setInterval(save, this.auto_save_time);
        }
    };

    $(document).ready(function(){
        var data = null;
        if (typeof jstree_data !== 'undefined') {
            data = jstree_data;
        }
        waxe.form = new Form(data);
    });

})(jQuery, waxe);


var waxe = waxe || {};

(function($, ns){
    "use strict";

    ns.layout = {
        init: function(){
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
        }
    };

    $(document).ready(function(){
        waxe.layout.init();
    });

})(jQuery, waxe);

var waxe = waxe || {};

(function($){
    "use strict";


    var NavBar = function(element) {
        this.init(element);
    };

    NavBar.prototype.init = function(element) {
        this.$element = $(element);
        this.$elements = {
            'new': this.$element.find('.new'),
            'open': this.$element.find('.open'),
            'saveas': this.$element.find('.saveas'),
            'save': this.$element.find('.save')
        };

        for(var name in this.$elements) {
            this['init_'+name]();
        }
    };

    NavBar.prototype._setNewModalEvents = function(modal){
        modal.find('.dtd-urls').on('change', function(){
            var dtdUrl = $(this).val();
            if(dtdUrl){
                var url = $(this).data('href');
                waxe.ajax.GET(url + '?dtd_url=' + dtdUrl, function(data){
                        var select = modal.find('.dtd-tags');
                        select.html('');
                        for(var index in data.tags){
                            var v = data.tags[index];
                            select.append($('<option>').attr('value', v).html(v));
                        }
                });
            }
        });
        modal.find('.submit').click(function(e){
            e.preventDefault();
            var url = $(this).data('href');
            var dtdUrl = modal.find('.dtd-urls').val();
            var dtdTag = modal.find('.dtd-tags').val();
            if(dtdUrl && dtdTag){
                url = url + '?dtd_url=' + dtdUrl + '&dtd_tag=' + dtdTag;
                waxe.dom.load(url);
                modal.modal('hide');
            }
        });
    };

    NavBar.prototype.init_new = function() {
        var that = this;
        this.$elements.new.click(function(e){
            e.preventDefault();
            var $this = $(this);
            if ($this.data('modal')){
                $this.data('modal').modal('show');
            }
            else{
                var url = $this.data('href');
                waxe.ajax.GET(url, function(data){
                    var modal = $(data.content);
                    that._setNewModalEvents(modal);
                    $this.data('modal', modal);
                    modal.modal();
                });
            }
        });
    };

    NavBar.prototype.init_open = function() {
        this.$elements.open.filebrowser({
            url: this.$elements.open.data('fb-href'),
            title: 'Open file'
        }).bind('select', function(e){
            waxe.dom.load(e.href);
        });
    };

    NavBar.prototype.init_saveas = function() {
        var that = this;
        this.$elements.saveas.filebrowser({
            url: this.$elements.saveas.data('fb-href'),
            text: {
                title: 'Save file',
                submit: 'Save',
            },
            type: 'save'
        }).bind('before_open', function(e){
            if(!waxe.form.$element) {
                e.preventDefault();
            }
        }).bind('select', function(e){
            waxe.form.setFilename(e.href);
            // TODO: we should call window.history.pushState
            waxe.form.$element.submit();
        }).bind('create_folder', function(e){
            var url = that.$elements.saveas.data('fb-folder-href') + '?path=' + e.path;
            waxe.ajax.GET(url, function(data){
                if(data.status === false){
                   e.preventDefault();
                   $(document).message('error', data.error_msg);
                }
            }, false); // Not asynchronious
        });
    };

    NavBar.prototype.init_save = function() {
        var that = this;
        this.$elements.save.click(function(e) {
            e.preventDefault();
            if (waxe.form.filename){
                waxe.form.$element.submit();
            } else {
                that.$elements.saveas.trigger('click');
            }
        });
    };

    NavBar.prototype.destroy = function(){
        for (var name in this.$elements) {
            this.$elements[name].unbind('click');
        }
        // TODO: we should add destroy function in filebrowser
        var filebrowser = this.$elements.open.data('filebrowser');
        filebrowser.$element.unbind('select').unbind('create_folder');
        this.$elements.open.removeData('filebrowser');
        filebrowser = this.$elements.saveas.data('filebrowser');
        filebrowser.$element.unbind('select').unbind('create_folder');
        this.$elements.saveas.removeData('filebrowser');
    };

    $(document).ready(function(){
        new NavBar($('.navbar'));
    });
    // We need to be able to access NavBar for the tests
    waxe.NavBar = NavBar;

})(jQuery);


(function($){
    "use strict";
    $.fn.message.defaults.css.position = 'fixed';
    $.fn.message.defaults.css['z-index'] = 2000;
    $.fn.message.defaults.template.message = '<div class="alert">\
      <button type="button" class="close">&times;</button>\
      <span class="text"/>\
    </div>';
    $.fn.message.defaults.extra_class = {
        info: 'alert-info',
        success: 'alert-success',
        error: 'alert-danger'
    };
    $.fn.message.defaults.selector.close_btn = '.close';

    $.fn.filebrowser.defaults.template.nav_file = '<li><i class="icon-file"></i></li>';
    $.fn.filebrowser.defaults.template.nav_folder = '<li><i class="icon-folder-close"></i></li>';
})(jQuery);

var waxe = waxe || {};

(function($, ns){
    "use strict";

    ns.versioning = {
        init: function(){

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
                                    waxe.versioning.commit(params);
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

    $(document).ready(function(){
        waxe.versioning.init();
    });

})(jQuery, waxe);


var waxe = waxe || {};

(function($){
    "use strict";

    window.onpopstate = function(e) {
        if(e.state !== null){
            waxe.dom.load(e.state.json_url);
        }
    };

    window.onbeforeunload = function(event) {
        if(waxe.form.status === waxe.form.STATUS_UPDATED){

            event = event || window.event;
            var confirmClose = 'The file has been updated, are you sure you want to exit?';
            if (event) {
                event.returnValue = confirmClose;
            }
            // For safari
            return confirmClose;
        }
    };

})(jQuery);
