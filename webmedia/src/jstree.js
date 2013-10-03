var waxe = waxe || {};

(function($, ns){
    "use strict";

    ns.jstree = {
        load: function(data){
            var tree = $("#tree");
            tree.jstree({
                "json_data" : {'data': [data]},
                "plugins" : ["themes", "json_data", "ui", 'crrm', 'dnd'],
                "core": {
                    html_titles: true
                },
                "ui" : {select_multiple_modifier: false},
                "crrm" : {
                    "move" : {
                        "check_move" : xmltool.jstree.check_move,
                    }
                },
                "dnd" : {
                    "drop_target" : false,
                    "drag_target" : false
                },
            }).bind("select_node.jstree", function (e, data) {
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:'));
                elt.focus();
                var t =  elt.offset().top + $('.ui-layout-center').scrollTop() - $('.ui-layout-center').offset().top - 30;
                $('.ui-layout-center').animate({
                    scrollTop: t,
                    }, 1000
                );
            }).bind("loaded.jstree", function (event, data) {
                tree.jstree('open_all');
                tree.height(tree.parent().parent().height());
                $('body').data('layout').show('east');
            }).bind("move_node.jstree", function(event, data){
                $(document).message('info', 'Moving...', {overlay: true, modal: true});
                setTimeout(function(){
                    xmltool.jstree.move_node(event, data);
                    $(document).message('success', 'Moved!');
                }, 50);
            }).bind('close_node.jstree', function(event, data){
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:'));
                elt.data('togglefieldset').hide(false);
            }).bind('open_node.jstree', function(event, data){
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:'));
                elt.data('togglefieldset').show(false);
            });
        }
    };


    $(document).ready(function(){
        var jstree_data = jstree_data || undefined;
        if(typeof(jstree_data) !== 'undefined'){
            waxe.jstree.load(jstree_data);
        }
    });

})(jQuery, waxe);
