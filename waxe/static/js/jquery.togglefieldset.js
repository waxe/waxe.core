(function($){

    var ToggleFieldset = function(elt, options){
        var self = this;
        var css_class = 'togglefieldset-hide';

        var get_children = function(){
            return elt.children(":not('legend')");
        }

        $.extend(self,{
            init: function(){
                self.legend = elt.children('legend');
                self.is_displayed = (!elt.hasClass(css_class));
                self.legend.click(self.toggle);
            },
            hide: function(trigger){
                elt.addClass(css_class);
                get_children().hide();
                self.is_displayed = false;
                if(trigger){
                    var e = jQuery.Event("hide.togglefieldset");
                    elt.trigger(e);
                }
            },
            show: function(trigger){
                elt.removeClass(css_class);
                get_children().show();
                self.is_displayed = true;
                if(trigger){
                    var e = jQuery.Event("show.togglefieldset");
                    elt.trigger(e);
                }
            },
            toggle: function(e){
                if (self.is_displayed){
                    self.hide(true);
                }
                else{
                    self.show(true);
                }
            }
        });
        self.init();
    }

    $.fn.togglefieldset = function(options){
        return $(this).each(function(){
            if (typeof($(this).data('togglefieldset')) == 'undefined'){
                var obj = new ToggleFieldset($(this), options);
                $(this).data('togglefieldset', obj);
            }
        });
    }


})(jQuery);

