if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($, ns){
    "use strict";

    ns.form = {
        selector: 'form#xmltool-form',
        exist: function(){
            if ($(this.selector).length)
                return true;
            return false;
        },
        getFilename: function(){
            return $(this.selector + ' #_xml_filename').val();
        },
        setFilename: function(value){
            $(this.selector + ' #_xml_filename').val(value);
        }
    };

})(jQuery, waxe);
