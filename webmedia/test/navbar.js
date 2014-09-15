(function($) {

    var $navbar = $('<div class="navbar" />');
    $navbar.append($('<a class="open" data-call="navbar.open">Open</a>'));
    $navbar.append($('<a class="save" data-call="navbar.save">Save</a>'));
    $navbar.append($('<a class="saveas" data-call="navbar.saveas">Save as</a>'));

    var old_waxe_ajax_GET;
    var ajax_cnt = 0;

    QUnit.module('Test waxe.navbar', {
        setup: function() {
            $('#qunit-fixture').html($navbar);
            old_waxe_ajax_GET = waxe.ajax.GET;
            ajax_cnt = 0;
            waxe.ajax.GET = function() {
                ajax_cnt += 1;
            };
        },
        teardown: function() {
            waxe.ajax.GET = old_waxe_ajax_GET;
        }
    });

    test("open", function() {
        var count = 0;
        var load_count = 0;
        var old_waxe_dom_load = waxe.dom.load;
        waxe.dom.load = function() {
             load_count += 1;
        };
        var $open = $navbar.find('.open');
        $open.trigger('click');
        $open.unbind('before_open').on('before_open', function(e) {
            count += 1;
            e.preventDefault();
        });
        $open.trigger('click');
        equal(count, 1, 'filebrowser called');
        equal(load_count, 0, 'select event not called');

        $open.trigger('select');
        equal(load_count, 1, 'select event called');
        waxe.dom.load = old_waxe_dom_load;
    });

    test("saveas", function() {
        var count = 0;
        var count_ok = 0;
        var $saveas = $navbar.find('.saveas');
        waxe.form.$element = 'something';
        $saveas.trigger('click');
        $saveas.on('before_open', function(e) {
            count += 1;
            if (!e.isDefaultPrevented()) {
                count_ok += 1;
            }
        });
        waxe.form.$element = null;
        $saveas.trigger('click');
        var filebrowser = $saveas.data('filebrowser');
        ok(filebrowser, 'filebrowser defined');
        equal(count, 1, 'before_open called');
        equal(count_ok, 0, 'before_open preventDefault not called');

        filebrowser.$element.click();
        equal(count, 2, 'before_open called');
        equal(count_ok, 0, 'before_open preventDefault not called');

        var form = $('<form id="xmltool-form"><input type="hidden" id="_xml_filename" /></form>');
        $('#qunit-fixture').append(form);
        waxe.form.load();

        var count_submit = 0;
        waxe.form.$element.unbind('submit').on('submit', function(e){
            e.preventDefault();
            count_submit += 1;
        });
        filebrowser.$element.click();
        equal(count, 3, 'before_open called');
        equal(count_ok, 1, 'before_open preventDefault called');
        equal(count_submit, 0, 'No submit');

        equal(waxe.form.filename, '', 'filename not defined');
        var e = $.Event('select');
        e.href = 'filename.xml';
        filebrowser.$element.trigger(e);
        equal(waxe.form.filename, 'filename.xml', 'filename is defined');
        equal(count_submit, 1, 'submit was called');
        equal(ajax_cnt, 0, 'No ajax request done');

        e = $.Event('create_folder');
        e.path = 'filename.xml';
        filebrowser.$element.trigger(e);
        equal(ajax_cnt, 1, 'No ajax request done');
    });

    test("save", function() {
        var old_waxe_form = waxe.form;
        waxe.form = {$element: {}};
        var click_count = 0;
        var $saveas = $navbar.find('.saveas');
        var $save = $navbar.find('.save');
        $saveas.unbind('click').on('click', function (){
            click_count += 1;
        });

        var submit_count = 0;
        waxe.form.$element.submit = function () {
            submit_count += 1;
        };

        $save.trigger('click');
        equal(click_count, 1, 'saveas called');
        equal(submit_count, 0, 'save not called');

        waxe.form.filename = 'plop';
        $save.trigger('click');
        equal(click_count, 1, 'saveas not called');
        equal(submit_count, 1, 'save called');
        waxe.form = old_waxe_form;
    });

})(window.jQuery);
