(function($){

    var Message = function(element, options){
        this.init(element, options);
    }

    Message.prototype = {
        constructor: Message,
        init: function(element, options){
            this.settings = $.extend(true, {}, $.fn.message.defaults, options),
                body = $('body');

            if(element == document){
                this.$element = $(this.settings.template.message).hide().appendTo(body);
            }
            else{
                this.$element = $(element).hide();
            }
            this.$text = this.$element.find(this.settings.selector.text);
            this.element_classes = this.$element.attr('class').split(' ');

            this.$overlay = $(this.settings.selector.overlay);
            if (! this.$overlay.length){
                this.$overlay = $(this.settings.template.overlay).hide().appendTo(body);
            }

            var close_btn = this.$element.find(this.settings.selector.close_btn);
            if (close_btn.length){
                this.$close_btn = close_btn;
                var self = this;
                this.$close_btn.click(function(){self.close()});
            }
        },
        _get_options: function(type, options){
            var tmp = {};
            for(var key in this.settings){
                var opt = this.settings[key];
                if (type in opt){
                    tmp[key] = opt[type];
                }
                else{
                    tmp[key] = opt;
                }
            }
            return $.extend(true, {}, tmp, options);
        },
        _get_class: function(css_class){
            var classes = this.element_classes.slice();
            classes.push(css_class);
            return classes.join(' ');
        },
        _add_arguments: function(arg, args){
            var args = Array.prototype.slice.call(args);
            args.reverse().push(arg);
            args.reverse();
            return args
        },
        _show: function(type, msg, options){
            if (typeof this.autohide_timeout != 'undefined')
                clearTimeout(this.autohide_timeout);

            var settings = this._get_options(type, options);
            this.$element.attr('class', this._get_class(settings.extra_class));
            this.$text.html(msg);
            if(settings.overlay){
                this.$overlay.show();
            }
            else{
                this.$overlay.hide();
            }
            if (this.$close_btn){
                if(settings.modal){
                    this.$close_btn.hide();
                }
                else{
                    this.$close_btn.show();
                }
            }
            this.set_position(settings);
            this.$element.show();
            if(settings.autohide){
                var self = this;
                this.autohide_timeout = setTimeout(function(){self.close()}, settings.autohide);
            }
        },
        set_position: function(settings){
            this.$element.css(settings.css);
            if (settings.css.position != 'absolute' && settings.css.position != 'fixed')
                return

            var left = ($('body').width() - this.$element.outerWidth()) / 2;
            this.$element.css({left: left + 'px'});
        },
        info: function(){
            var args = this._add_arguments('info', arguments);
            this._show.apply(this, args);
        },
        success: function(){
            var args = this._add_arguments('success', arguments);
            this._show.apply(this, args);
        },
        error: function(){
            var args = this._add_arguments('error', arguments);
            this._show.apply(this, args);
        },
        close: function(){
            if (typeof this.autohide_timeout != 'undefined')
                clearTimeout(this.autohide_timeout);
            this.$element.fadeOut();
            this.$overlay.fadeOut();
        }
    }


    $.fn.message = function(options){
        var args = arguments;
        return this.each(function(){
            var $this = $(this),
                data = $this.data('message'),
                settings = typeof options == 'object' && options;

            if(!data){
                data = new Message(this, settings);
                $this.data('message', data)
            }
            if (typeof options == 'string'){
                data[options].apply(data, Array.prototype.slice.call(args, 1));
            }
        });
    }

    $.fn.message.defaults = {
        extra_class: {
            info: 'message-info',
            success: 'message-success',
            error: 'message-error'
        },
        autohide: {
            info: 1000,
            success: 1000,
            error: null
        },
        overlay: {
            info: false,
            success: false,
            error: false
        },
        modal: {
            info: false,
            success: false,
            error: false
        },
        selector: {
            message: '.message',
            text: '.text',
            overlay: '#message-overlay',
            close_btn: '.btn-close'
        },
        template: {
            message: '<div class="message"><a class="btn-close">x</a><span class="text"/></div>',
            overlay: '<div id="message-overlay"></div>'
        },
        css: {
            position: 'absolute',
            top: 0,
            'max-width': '100%'
        }
    }

})(window.jQuery);

