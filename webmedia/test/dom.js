var waxe = waxe || {};
(function($) {

    var FakeLayout = function(){
        this.$elt = $('<div/>');
        this.hide = function(){
            this.$elt.hide();
        };
    };

    var versioning_nb_called = 0;
    var FakeVersioning = {
        init: function(){
            versioning_nb_called += 1;
        }
    };

    var message_error_nb_called = 0;
    var message_info_nb_called = 0;
    var message_success_nb_called = 0;
    $.fn.message = function(type){
        if (type === 'success'){
            message_success_nb_called += 1;
        }
        else if (type === 'info'){
            message_info_nb_called += 1;
        }
        else {
            message_error_nb_called += 1;
        }
    };

    var breadcrumb = $('<div class="breadcrumb" />');
    var content = $('<div class="content" />');
    var layout = new FakeLayout();
    var old_waxe_versioning;
    QUnit.module('Test waxe.dom', {
        setup: function(){
            old_waxe_versioning = waxe.versioning;
            waxe.versioning = FakeVersioning;
            $('#qunit-fixture').html(breadcrumb);
            $('#qunit-fixture').append(content);
            $('#qunit-fixture').append(layout.$elt);
            $('body').data('layout', layout);
            versioning_nb_called = 0;
            message_error_nb_called = 0;
            message_success_nb_called = 0;
            message_info_nb_called = 0;
        },
        teardown: function(){
            waxe.versioning = old_waxe_versioning;
        }
    });

    test("addPushStateOnLinks", function(){
        var old_waxe_dom_load = waxe.dom.load;

        var hist_cnt = window.history.length;
        var cnt = 0;
        waxe.dom.load = function(){
            cnt += 1;
        };
        var a = $('<a data-href="/plop">plop</a>');
        $('#qunit-fixture').append(a);
        equal(window.history.length, hist_cnt, 'initial history');
        waxe.dom.addPushStateOnLinks($('#qunit-fixture'));
        a.trigger('click');
        equal(window.history.length, hist_cnt + 1, 'history is updated');
        equal(cnt, 1, 'page loaded');
        waxe.dom.load = old_waxe_dom_load;
    });

    test("update", function() {
        var old_waxe_dom_addPushStateOnLinks = waxe.dom.addPushStateOnLinks;
        var cnt = 0;
        waxe.dom.addPushStateOnLinks = function(){
            cnt += 1;
        };
        equal(layout.$elt.is(':visible'), true, 'layout displayed by default');
        var data = {};
        waxe.dom.update(data);
        equal(content.html(), '', 'no content');
        equal(breadcrumb.html(), '', 'no breadcrumb');
        equal(layout.$elt.is(':visible'), false, 'layout is hidden');

        data = {
            content: 'My content',
            breadcrumb: 'My breadcrumb'
        };
        waxe.dom.update(data);
        equal(content.html(), 'My content', 'content updated');
        equal(breadcrumb.html(), 'My breadcrumb', 'breadcrumb updated');
        equal(layout.$elt.is(':visible'), false, 'layout is always hidden');
        equal(versioning_nb_called, 1);
        equal(message_error_nb_called,  0);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 1);
        equal(cnt, 2);

        data = {
            content: 'My new content',
        };
        waxe.dom.update(data);
        equal(content.html(), 'My new content', 'content updated');
        equal(breadcrumb.html(), '', 'breadcrumb is empty');
        equal(layout.$elt.is(':visible'), false, 'layout is always hidden');
        equal(versioning_nb_called, 2);
        equal(message_error_nb_called,  0);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 2);
        equal(cnt, 3);

        data = {
            breadcrumb: 'My breadcrumb'
        };
        waxe.dom.update(data);
        equal(content.html(), 'My new content', 'content not updated');
        equal(breadcrumb.html(), 'My breadcrumb', 'breadcrumb updated');
        equal(layout.$elt.is(':visible'), false, 'layout is always hidden');
        equal(versioning_nb_called, 2);
        equal(message_error_nb_called,  0);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 2);
        equal(cnt, 4);

        data = {};
        waxe.dom.update(data);
        equal(content.html(), 'My new content', 'content not updated');
        equal(breadcrumb.html(), '', 'breadcrumb updated');
        equal(layout.$elt.is(':visible'), false, 'layout is always hidden');
        equal(versioning_nb_called, 2);
        equal(message_error_nb_called,  0);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 2);
        equal(cnt, 4);

        data = {
            error_msg: 'My error'
        };
        // Nothing has changed, we just display the error message!
        waxe.dom.update(data);
        equal(content.html(), 'My new content', 'content not updated');
        equal(breadcrumb.html(), '', 'breadcrumb updated');
        equal(layout.$elt.is(':visible'), false, 'layout is always hidden');
        equal(versioning_nb_called, 2);
        equal(message_error_nb_called,  1);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 2);
        equal(cnt, 4);

        var modal_nb_called = 0;
        var old_modal = $.fn.modal;
        $.fn.modal = function() {
            modal_nb_called += 1;
        };
        data = {
            modal: 'Content of my modal'
        };
        // Nothing has changed, we just display the modal!
        waxe.dom.update(data);
        equal(content.html(), 'My new content', 'content not updated');
        equal(breadcrumb.html(), '', 'breadcrumb updated');
        equal(layout.$elt.is(':visible'), false, 'layout is always hidden');
        equal(versioning_nb_called, 2);
        equal(message_error_nb_called,  1);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 3);
        equal(cnt, 4);
        equal(modal_nb_called, 1);

        waxe.dom.addPushStateOnLinks = old_waxe_dom_addPushStateOnLinks;
        $.fn.modal = old_modal;
    });

    test("load", function() {
        var old_waxe_ajax_GET = waxe.ajax.GET;
        waxe.ajax.GET = function(url, callback){
            callback({'content': url + ' was loaded'});
        };
        waxe.dom.load('http://plop');
        equal(content.html(), 'http://plop was loaded');
        equal(message_error_nb_called,  0);
        equal(message_success_nb_called,  0);
        equal(message_info_nb_called, 2);
        waxe.ajax.GET = old_waxe_ajax_GET;
    });

})(window.jQuery);
