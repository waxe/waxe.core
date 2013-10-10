var waxe = waxe || {};

(function($) {

    var old_ajax;
    QUnit.module('Test waxe.ajax', {
        setup: function(){
            old_ajax = $.ajax;
            $.ajax = function(params){
                return params.success(params);
            };
        },
        teardown: function(){
            $.ajax = old_ajax;
        }
    });

    test("GET", function() {
        expect(10);
        waxe.ajax.GET('/test', function(params){
            ok(true, 'callback was called');
            equal(params.type, 'GET', 'GET method');
            equal(params.url, '/test', 'url');
            equal(params.dataType, 'json', 'json');
            equal(params.async, true, 'async is true');
        });

        waxe.ajax.GET('/test', function(params){
            ok(true, 'callback was called');
            equal(params.type, 'GET', 'GET method');
            equal(params.url, '/test', 'url');
            equal(params.dataType, 'json', 'json');
            equal(params.async, false, 'async is false');
        }, false);
    });

    test("POST", function() {
        expect(10);
        waxe.ajax.POST('/test', {}, function(params){
            ok(true, 'callback was called');
            equal(params.type, 'POST', 'POST method');
            equal(params.url, '/test', 'url');
            equal(params.dataType, 'json', 'json');
            equal(params.async, true, 'async is true');
        });

        waxe.ajax.POST('/test', {}, function(params){
            ok(true, 'callback was called');
            equal(params.type, 'POST', 'POST method');
            equal(params.url, '/test', 'url');
            equal(params.dataType, 'json', 'json');
            equal(params.async, false, 'async is false');
        }, false);
    });
})(jQuery);
