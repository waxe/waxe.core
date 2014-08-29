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
                west: {
                    initHidden: true,
                    onresize_end: function(size){
                        var tree = $('#tree');
                        tree.height(tree.parent().parent().height());
                    }
                },
                south: {
                    initHidden: true
                }
            });
        }
    };

    $(document).ready(function(){
        if ($('.ui-layout-center').length) {
            waxe.layout.init();
        }
    });

})(jQuery, waxe);
