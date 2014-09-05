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
            'save': this.$element.find('.save'),
            'split': this.$element.find('.split')
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

    NavBar.prototype.init_split = function() {
        var that = this;
        this.$elements.split.click(function(e) {
            e.preventDefault();
            if (waxe.form.filename){
                var iframe = $('<iframe frameborder="0">');
                iframe.css({width: '100%', height: '100%'});
                iframe.attr('src', $(this).data('href') + '?iframe=1&path=' + waxe.form.filename);
                waxe.layout.updateReadonly(iframe);
                waxe.layout.showReadonly();
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

