var waxe = waxe || {};


(function($, waxe){
    "use strict";

    waxe.layout = {};

    (function() {

        this.SELECTORS = {
            'center': '.ui-layout-center',
            'north': '.ui-layout-north',
            'south': '.ui-layout-south',
            'east': '.ui-layout-east',
            'west': '.ui-layout-west'
        };

        this.getTreePosition = function() {
            var $east = $(this.SELECTORS.east);
            if ($east.length) {
                this.$tree = $east;
                return 'east';
            }
            var $west = $(this.SELECTORS.west);
            if ($west.length) {
                this.$tree = $west;
                return 'west';
            }
            return null;
        };

        this.getReadonlyPostion = function() {
            var $north = $(this.SELECTORS.north);
            if ($north.length) {
                this.$readonly = $north;
                return 'north';
            }
            var $south = $(this.SELECTORS.south);
            if ($south.length) {
                this.$readonly = $south;
                return 'south';
            }
            return null;
        };

        this.init = function(){
            if (! $(this.SELECTORS.center).length) {
                // We assume if we don't have center layout, we don't have any
                // layout
                return false;
            }
            this.treePosition = this.getTreePosition();
            this.readonlyPosition = this.getReadonlyPostion();

            var pluginOptions = {
                applyDemoStyles: true,
                enableCursorHotkey: false
            };

            if(this.readonlyPosition) {
                pluginOptions[this.readonlyPosition] = {
                    initHidden: true
                };
            }
            if(this.treePosition) {
                pluginOptions[this.treePosition] = {
                    initHidden: true,
                    size: '33%',
                    onresize_end: function(size){
                        var tree = $('#tree');
                        tree.height(tree.parent().parent().height());
                    }
                };
            }
            var $body = $('body');
            $body.layout(pluginOptions);
            this.obj = $body.data('layout');
        };

        this.showTree = function() {
            if (this.treePosition) {
                this.obj.show(this.treePosition);
            }
        };

        this.hideTree = function() {
            if (this.treePosition) {
                this.obj.hide(this.treePosition);
            }
        };

        this.showReadonly = function() {
            if(this.readonlyPosition) {
                this.obj.show(this.readonlyPosition);
            }
        };

        this.hideReadonly = function() {
            if(this.readonlyPosition) {
                this.obj.hide(this.readonlyPosition);
            }
        };

        this.updateReadonly = function(html) {
            if(this.readonlyPosition) {
                this.$readonly.html(html);
                this.obj.resizeAll();
            }
        };

    }).apply(waxe.layout);


    $(document).ready(function(){
        waxe.layout.init();
    });

})(jQuery, waxe);
