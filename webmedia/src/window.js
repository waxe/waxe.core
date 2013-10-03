if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($){
    "use strict";

    window.onpopstate = function(e) {
        if(e.state !== null){
            waxe.dom.load(e.state.json_url);
        }
    };

    window.onbeforeunload = function(event) {
        var form = $(waxe.form.selector);
        if(form.data('status') === 'updated'){

        event = event || window.event;
        var confirmClose = 'The file has been updated, are you sure you want to exit?';
        if (event) {
            event.returnValue = confirmClose;
        }
        // For safari
        return confirmClose;
        }
    };

})(jQuery);
