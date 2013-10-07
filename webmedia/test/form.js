var waxe = waxe || {};
(function($) {

var get_form = function(){
    return $('<form id="xmltool-form"><input type="hidden" id="_xml_filename" /></form>');
};


QUnit.module('Test waxe.form', {
    setup: function() {
        $('#xmltool-form').remove();
        waxe.form.load();
    }
});

test("load (no form)", function() {
    equal(waxe.form.load(), false, 'nothing was loaded');
    equal(waxe.form.$element, null, 'No form');
    equal(waxe.form.$filename, null, 'No filename');
    equal(waxe.form.status, null, 'No status');
});

test("load (not defined id)", function() {
    $('#qunit-fixture').append('<form />');
    equal(waxe.form.load(), false, 'nothing was loaded');
    equal(waxe.form.$element, null, 'No form');
    equal(waxe.form.$filename, null, 'No filename');
    equal(waxe.form.status, null, 'No status');
});

test("load", function() {
    equal(waxe.form.load(), false, 'form was not loaded');
    var f = get_form();
    $('#qunit-fixture').append(f);
    equal(waxe.form.load(), true, 'form was loaded');
    ok(waxe.form.$element, 'form');
    equal(waxe.form.$element.attr('id'), 'xmltool-form', 'form id');
    ok(waxe.form.$filename, 'filename');
    ok(waxe.form.$filename.is('input'), null, 'filename input');
    equal(waxe.form.status, null, 'No status');
});

test("reload", function() {
    equal(waxe.form.load(), false, 'nothing was loaded');
    var f = get_form();
    $('#qunit-fixture').append(f);
    equal(waxe.form.load(), true, 'form was loaded');
    ok(waxe.form.$element, 'form');
    f.remove();
    equal(waxe.form.load(), false, 'nothing was loaded');
    equal(waxe.form.$element, null, 'No form');
    equal(waxe.form.$filename, null, 'No filename');
    equal(waxe.form.status, null, 'No status');
});

test("filename", function() {
    equal(waxe.form.load(), false, 'form was not loaded');
    var f = get_form();
    $('#qunit-fixture').append(f);
    equal(waxe.form.load(), true, 'form was loaded');
    equal(waxe.form.filename, '', 'no defined');
    ok(waxe.form.setFilename('plop'), 'set filename');
    equal(waxe.form.filename, 'plop', 'defined');
});

test("setFilename", function() {
    equal(waxe.form.load(), false, 'form was not loaded');
    ok(!waxe.form.setFilename('plop'), 'filename not set');
    var f = get_form();
    $('#qunit-fixture').append(f);
    equal(waxe.form.load(), true, 'form was loaded');
    equal(f.find('input').val(), '', 'no set');
    ok(waxe.form.setFilename('plop'), 'set filename');
    equal(f.find('input').val(), 'plop', 'set');
    equal(waxe.form.filename, 'plop', 'constant set');
});

test("save", function() {
    expect(2);
    var old_ajax = waxe.ajax;

    waxe.ajax.POST = function(){
        ok(true, 'POST was called');
    };
    var e = $.Event();
    equal(waxe.form.save(e), false, 'Not saved');

    var f = get_form();
    $('#qunit-fixture').append(f);
    waxe.form.load();
    waxe.form.save(e);

    waxe.ajax = old_ajax;
});

test("auto_save", function() {
    expect(6);
    waxe.form.auto_save();
    var old_setInterval = setInterval;
    setInterval = function(func){
        func();
        return true;
    };

    ok(!waxe.form.auto_save_interval, 'auto_save not launch (no form)');

    var f = get_form();
    $('#qunit-fixture').append(f);
    waxe.form.load();
    waxe.form.auto_save();
    ok(!waxe.form.auto_save_interval, 'auto_save not launch (no filename)');

    waxe.form.load();
    var submit_cnt = 0;
    waxe.form.$element.unbind('submit').submit(function(e){
        e.preventDefault();
        ok(true, 'Submit form called');
        submit_cnt += 1;
    });
    waxe.form.setFilename('test.xml');
    waxe.form.auto_save_time = 100;
    waxe.form.auto_save();
    ok(waxe.form.auto_save_interval, 'auto_save launch');
    equal(submit_cnt, 0, 'Interval function not called');
    waxe.form.status = waxe.form.STATUS_UPDATED;
    waxe.form.auto_save();
    equal(submit_cnt, 1, 'Interval function called');
    setInterval = old_setInterval;
});

}(jQuery));
