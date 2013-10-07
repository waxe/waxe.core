var waxe = waxe || {};

(function($, ns){
    "use strict";


    var ajax = function(type, url, callback, data){
        $.ajax({
            type: type,
            url: url,
            data: data,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                callback(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                // TODO: make sure this error message is nice!
                var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                $(document).message('error', msg);
            }
        });
    };

    ns.ajax = {
         GET: function(url, callback){
             ajax('GET', url, callback);
         },
         POST: function(url, data, callback){
             ajax('POST', url, callback, data);
         }
     };
})(jQuery, waxe);
