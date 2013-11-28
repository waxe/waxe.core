(function($){

    var FileBrowser = function(element, options){
        this.init(element, options);
    }

    FileBrowser.prototype = {
        constructor: FileBrowser,
        init: function(element, options){
            this.is_initialize = false;
            this.settings = $.extend(true, {}, $.fn.filebrowser.defaults, options),
            this.$element = $(element);
            this.$dialog = $(this.settings.template.dialog);
            this.$navfile = this.$dialog.find(this.settings.selector.nav_file);
            this.$nav_btns = this.$dialog.find(this.settings.selector.nav_btns);
            this.$title = this.$dialog.find(this.settings.selector.title);
            this.$submit = this.$dialog.find(this.settings.selector.submit);
            this.$cancel = this.$dialog.find(this.settings.selector.cancel);
            this.$title.html(this.settings.text.title);
            this.$submit.html(this.settings.text.submit);
            this.$cancel.html(this.settings.text.cancel);
            this.path = null;
            this.url = null;
            this.$filename = null;

            var self = this;
            if(this.settings.type == 'save'){
                this.$nav_btns.before(this.settings.template.filename);
                this.$filename = this.$dialog.find(this.settings.selector.filename);
                this.$filename.keydown(function(e){
                    if(e.which == 13){
                        if ($(this).val()){
                            self.$submit.click();
                        }
                    }
                });

                var tmp = $('<input type="text" class="foldername"/>').hide().keydown(function(e){
                    if(e.which == 13){
                        var value = $(this).val();
                        if (value){
                            if(self.path){
                                var path = self.path + '/' + value;
                            }
                            else{
                                var path = value;
                            }
                            var evt = $.Event('create_folder', {path: path});
                            self.$element.trigger(evt);
                            if(!evt.isDefaultPrevented()){
                                $(this).hide();
                                self._get_ajax_data(self.url);
                            }
                        }
                    }
                    else if(e.which == 27){
                        e.preventDefault();
                        e.stopPropagation();
                        $(this).hide();
                    }
                }).keyup(function(e){
                    if(e.which == 27){
                        e.preventDefault();
                        e.stopPropagation();
                    }
                });

                this.$new_folder = $(this.settings.template.new_folder).on('click', function(e){
                    tmp.show().focus().val('');
                });
                this.$navfile.before(tmp);

                this.$nav_btns.after(this.$new_folder);
            }

            this.$submit.click(function(e){self.on_submit(e)});

            var self = this;
            this.$element.on('click', function(e){
                e.preventDefault();

                var evt = $.Event('before_open');
                self.$element.trigger(evt);
                if(evt.isDefaultPrevented())
                    return false;
                self.$navfile.find('li.file').removeClass(self.settings.css_class.selected_file);
                if (self.is_initialize){
                    self.settings.func.open_dialog(self.$dialog);
                }
                else{
                    self._initialize_dialog();
                }
            });
        },
        _initialize_dialog: function(){
            this._get_ajax_data(this.settings.url);
            this.settings.func.init_dialog(this.$dialog);
            this.is_initialize = true;
        },
        _get_ajax_data: function(url){
            var self = this;
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'json',
                success: function(data, textStatus, jqXHR){
                    self.path = data.path;
                    self.url = url;
                    if(self.$filename){
                        self.$filename.val('');
                    }
                    self._construct(data);
                },
                error: function(jqXHR, textStatus, errorThrown){
                    // TODO: add nice way to catch the exception
                    alert('Error ajax loading');
                }
            });
        },
        on_click: function(e, element){
            e.preventDefault();
            this._get_ajax_data($(element).data('href'));
        },
        _construct: function(data){
            this.$nav_btns.html('');
            var self = this;
            for(var i=0; i < data.nav_btns.length; i++){
                var btn_data = data.nav_btns[i];
                var btn = $(this.settings.template.nav_btn).html(btn_data.name).data('href', btn_data.data_href).on('click', function(e){self.on_click(e, this);});

                if (i >= (data.nav_btns.length - 1)){
                    btn.addClass(this.settings.css_class.last_nav_file);
                }
                this.$nav_btns.append(btn);
            }

            var container = $(this.settings.template.nav_files);
            for(var i=0; i < data.folders.length; i++){
                var folder = data.folders[i];
                var span = $('<span />').html(folder.name);
                var li = $(this.settings.template.nav_folder).append(span).on('click', function(e){self.on_click(e, this);}).data('href', folder.data_href).addClass(this.settings.css_class.folder);
                container.append(li);
            }

            for(var i=0; i < data.filenames.length; i++){
                var filename = data.filenames[i];
                var span = $('<span />').html(filename.name);
                var li = $(this.settings.template.nav_file).append(span).data('href', filename.data_href).addClass(this.settings.css_class.file);
                if(this.settings.type == 'open'){
                    li.on('click', function(){
                        var selected_class = self.settings.css_class.selected_file;
                        $(this).addClass(selected_class).siblings().removeClass(selected_class);
                    }).dblclick(function(){
                        self.$submit.click();
                    });
                }
                else{
                    li.on('click', function(){
                        self.$filename.val($(this).text());
                    });
                }

                container.append(li);
            }
            this.$navfile.html(container);
        },
        _get_selected_file: function(){
            return this.$navfile.find('li.file.selected').data('href');
        },
        _notok_filename: function(filename){
            var is_folder = false;
            this.$navfile.find('.' + this.settings.css_class.folder).each(function(){
                if ($(this).text() == filename){
                    is_folder = true;
                }
            });
            return is_folder;
        },
        _exist_filename: function(filename){
            var exist = false;
            this.$navfile.find('.' + this.settings.css_class.file).each(function(){
                if ($(this).text() == filename){
                    exist = true;
                }
            });
            return exist;
        },
        on_submit: function(e){
            e.preventDefault();
            if(this.settings.type == 'open'){
                var href = this._get_selected_file();
                if(href){
                    var evt = $.Event('select', {href: href});
                    this.$element.trigger(evt);
                    if(! evt.isDefaultPrevented()){
                        this.settings.func.close_dialog(this.$dialog);
                    }
                }
            }
            else{
                var input = this.$dialog.find(this.settings.selector.filename);
                if(input.length){
                    var filename = input.val();
                    if (filename){
                        if(this._notok_filename(filename)){
                            alert('You can not use this filename since it\'s a folder name');
                            return false;
                        }
                        if(this._exist_filename(filename)){
                            if(!confirm('Do you want to overwrite ' + filename + '?'))
                                return false;
                        }
                        if(this.path)
                            var path = this.path + '/' + filename
                        else
                            var path = filename;
                        var evt = $.Event('select', {href: path});
                        this.$element.trigger(evt);
                        if(! evt.isDefaultPrevented()){
                            this.settings.func.close_dialog(this.$dialog);
                        }
                    }
                }
            }
        }
    }


    $.fn.filebrowser = function(options){
        var args = arguments;
        return this.each(function(){
            var $this = $(this),
                data = $this.data('filebrowser'),
                settings = typeof options == 'object' && options;

            if(!data){
                data = new FileBrowser(this, settings);
                $this.data('filebrowser', data)
            }
            if (typeof options == 'string'){
                data[options].apply(data, Array.prototype.slice.call(args, 1));
            }
        });
    };

    $.fn.filebrowser.defaults = {
        template: {
            dialog: '<drv class="modal fade">' +
                '<div class="modal-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">' +
                '<div class="modal-content">' +
                '<div class="modal-header">' +
                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>' +
    '<h4 class="modal-title"></h4>' +
    '</div>' +
    '<div class="modal-body">' +
    '<div class="btn-group"></div>' +
    '<br />' +
    '<br />' +
    '<div class="navfile">' +
    '</div>' +
    '</div>' +
    '<div class="modal-footer">' +
    '<a href="#" class="btn cancel" data-dismiss="modal"></a>' +
    '<a href="#" class="btn btn-primary submit"></a>' +
    '</div>' +
    '</div>' +
    '</div>' +
    '</div>',
            nav_btn: '<button class="btn"/>',
            nav_files: '<ul class="list-unstyled"/>',
            nav_file: '<li/>',
            nav_folder: '<li/>',
            filename: '<div class="form-inline"><label>Filename:</label><input class="filename" type="text" name="filename" /></div><br />',
            new_folder: '<button class="pull-right">New folder</button>'
        },
        css_class: {
            last_nav_file: 'disabled',
            folder: 'folder',
            file: 'file',
            selected_file: 'selected'
        },
        selector: {
            title: 'h4',
            nav_btns: '.btn-group',
            nav_file: '.navfile',
            submit: '.submit',
            cancel: '.cancel',
            filename: '.filename'
        },
        func: {
            init_dialog: function(dialog){
                dialog.modal();
            },
            open_dialog: function(dialog){
                dialog.modal('show');
            },
            close_dialog: function(dialog){
                dialog.modal('hide');
            }
        },
        text: {
            title: 'Open file',
            submit: 'Open',
            cancel: 'Cancel'
        },
        type: 'open'
    }

})(jQuery);
