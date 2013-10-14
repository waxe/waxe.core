var waxe = waxe || {};
(function($) {

    var $navbar = $('<div class="navbar" />');
    $navbar.append($('<a data-href="/new.json" class="new">New</a>'));
    $navbar.append($('<a class="open">Open</a>'));
    $navbar.append($('<a class="save">Save</a>'));
    $navbar.append($('<a class="saveas">Save as</a>'));

    var old_waxe_ajax_GET;
    var ajax_cnt = 0;
    var navbar;

    QUnit.module('Test waxe.navbar', {
        setup: function() {
            $('#qunit-fixture').html($navbar);
            old_waxe_ajax_GET = waxe.ajax.GET;
            ajax_cnt = 0;
            waxe.ajax.GET = function() {
                ajax_cnt += 1;
            };
            navbar = new waxe.NavBar($navbar);
        },
        teardown: function() {
            waxe.ajax.GET = old_waxe_ajax_GET;
            navbar.destroy();
        }
    });

    test("init", function() {
        equal(navbar.$element.attr('class'), $navbar.attr('class'));
        equal(navbar.$elements.new.attr('class'), 'new');
        equal(navbar.$elements.open.attr('class'), 'open');
        equal(navbar.$elements.save.attr('class'), 'save');
        equal(navbar.$elements.saveas.attr('class'), 'saveas');
    });

    test("new", function() {
        var modalHtml = '<div><select class="dtd-urls" name="dtd-urls"><option value="url1">url1</option></select><select class="dtd-tags" name="dtd-tags"><option>opt1</option></select><input class="submit" /></div>';
        var old_waxe_ajax_GET = waxe.ajax.GET;
        var old_waxe_dom_load = waxe.dom.load;

        var count_load = 0;
        waxe.dom.load = function() {
            count_load += 1;
        };

        waxe.ajax.GET = function(url, callback) {
            ajax_cnt += 1;
            if (url === '/new.json') {
                callback({content: modalHtml});
            }
            else {
                ok(false, 'Should not be called');
            }
        };

        navbar.$elements.new.trigger('click');
        var modal = navbar.$elements.new.data('modal');
        equal(modal.length, 1, 'The modal is created');
        equal(ajax_cnt, 1, 'waxe.ajax.GET called');
        equal(count_load, 0, 'The modal is created');
        ok(modal.is(':visible'), 'The modal is displayed');

        navbar.$elements.new.trigger('click');
        modal = navbar.$elements.new.data('modal');
        equal(modal.length, 1, 'The modal is created');
        equal(ajax_cnt, 1, 'waxe.ajax.GET not called');
        equal(count_load, 0, 'The modal is created');
        ok(modal.is(':visible'), 'The modal is displayed');

        // To be continued
        modal.find('.submit').click();
        ok(!modal.is(':visible'), 'The modal is closed');
        equal(ajax_cnt, 1, 'waxe.ajax.GET not called');
        equal(count_load, 1, 'Create new file');

        waxe.ajax.GET = old_waxe_ajax_GET;
        waxe.dom.load = old_waxe_dom_load;
    });

    test("open", function() {
        var count = 0;
        var load_count = 0;
        var old_waxe_dom_load = waxe.dom.load;
        waxe.dom.load = function() {
             load_count += 1;
        };
        navbar.$elements.open.unbind('before_open').on('before_open', function(e) {
            count += 1;
            e.preventDefault();
        });
        navbar.$elements.open.trigger('click');
        equal(count, 1, 'filebrowser called');
        equal(load_count, 0, 'select event not called');

        navbar.$elements.open.trigger('select');
        equal(load_count, 1, 'select event called');
        waxe.dom.load = old_waxe_dom_load;
    });

    test("saveas", function() {
        var count = 0;
        var count_ok = 0;
        navbar.$elements.saveas.on('before_open', function(e) {
            count += 1;
            if (!e.isDefaultPrevented()) {
                count_ok += 1;
            }
        });
        navbar.$elements.saveas.trigger('click');
        var filebrowser = navbar.$elements.saveas.data('filebrowser');
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
        navbar.$elements.saveas.unbind('click').on('click', function (){
            click_count += 1;
        });

        var submit_count = 0;
        waxe.form.$element.submit = function () {
            submit_count += 1;
        };

        navbar.$elements.save.trigger('click');
        equal(click_count, 1, 'saveas called');
        equal(submit_count, 0, 'save not called');

        waxe.form.filename = 'plop';
        navbar.$elements.save.trigger('click');
        equal(click_count, 1, 'saveas not called');
        equal(submit_count, 1, 'save called');
        waxe.form = old_waxe_form;
    });

})(window.jQuery);
