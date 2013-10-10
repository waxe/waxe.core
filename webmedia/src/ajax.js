var waxe = waxe || {};

(function($, ns){
    "use strict";


    var ajax = function(type, url, callback, data, async){
        async = typeof async === 'undefined'? true: async;
        $.ajax({
            type: type,
            url: url,
            async: async,
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
         GET: function(url, callback, async){
             ajax('GET', url, callback, null, async);
         },
         POST: function(url, data, callback, async){
             ajax('POST', url, callback, data, async);
         }
     };
})(jQuery, waxe);
