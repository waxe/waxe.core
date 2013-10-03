if (typeof waxe === "undefined"){
    var waxe = {};
}

(function($){
    "use strict";

    waxe.ajax = {
         GET: function(url, callback){
             $.ajax({
                 type: 'GET',
                 url: url,
                 dataType: 'json',
                 success: function(data, textStatus, jqXHR){
                     callback(data);
                 },
                 error: function(jqXHR, textStatus, errorThrown){
                    var msg = jqXHR.status + ' ' + jqXHR.statusText + ': ' + url;
                    $(document).message('error', msg);
                 }
             });
         }
     };
})(jQuery, waxe);