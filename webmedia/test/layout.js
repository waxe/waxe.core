(function($, waxe) {


    var layout_html = [
        '<div class="ui-layout-north"></div>',
        '<div class="ui-layout-west"></div>',
        '<div class="ui-layout-center"></div>',
    ].join("");

    QUnit.module('Test waxe.layout', {
        setup: function(){
            $('body').append(layout_html);
        },
        teardown: function(){
            // waxe.versioning = old_waxe_versioning;
            if (waxe.layout.obj) {
                waxe.layout.obj.destroy();
            }
            $(".ui-layout-north").remove();
            $(".ui-layout-west").remove();
            $(".ui-layout-center").remove();
        }
    });


    test('getTreePosition', function(){
        equal(waxe.layout.getTreePosition(), 'west', 'The tree should be on the left');
        $(".ui-layout-west").remove();
        equal(waxe.layout.getTreePosition(), null, 'No tree');

        $('#qunit-fixture').html('<div class="ui-layout-east"></div>');
        equal(waxe.layout.getTreePosition(), 'east', 'The tree should be on the right');

    });

    test('getReadonlyPostion', function(){
        equal(waxe.layout.getReadonlyPostion(), 'north', 'The readonly should be on the top');

        $(".ui-layout-north").remove();
        equal(waxe.layout.getReadonlyPostion(), null, 'No readonly');

        $('#qunit-fixture').html('<div class="ui-layout-south"></div>');
        equal(waxe.layout.getReadonlyPostion(), 'south', 'The readonly should be on the bottom');
    });

    test('init', function(){
        equal(waxe.layout.obj, null, 'Layout not initialized');
        waxe.layout.init();
        ok(waxe.layout.obj, 'the layout is initialized');
    });

    test('showTree hideTree', function(){
        waxe.layout.init();
        ok(!waxe.layout.$tree.is(':visible'), 'by default tree is hidden');

        waxe.layout.showTree();
        ok(waxe.layout.$tree.is(':visible'), 'tree is visible');

        waxe.layout.hideTree();
        ok(!waxe.layout.$tree.is(':visible'), 'tree is hidden');
    });

    test('showReadonly hideReadonly', function(){
        waxe.layout.init();
        ok(!waxe.layout.$readonly.is(':visible'), 'by default readonly is hidden');

        waxe.layout.showReadonly();
        ok(waxe.layout.$readonly.is(':visible'), 'readonly is visible');

        waxe.layout.hideReadonly();
        ok(!waxe.layout.$readonly.is(':visible'), 'readonly is hidden');

    });

    test('updateReadonly', function(){
        waxe.layout.init();
        equal(waxe.layout.$readonly.html(), '', 'readonly is empty');
        waxe.layout.updateReadonly('Hello world');
        equal(waxe.layout.$readonly.html(), 'Hello world', 'readonly updated');
    });

})(jQuery, waxe);
