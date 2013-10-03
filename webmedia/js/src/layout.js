if (typeof waxe === "undefined"){
    var waxe = {};
}

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
