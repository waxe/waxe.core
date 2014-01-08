(function($){
    "use strict";

    $(document).ready(function(){
        $(document).on('click', '.select-all', function(e){
            e.preventDefault();
            $(this).parents('form').find('input[type="checkbox"]').prop('checked', true);
        });

        $(document).on('click', '.select-none', function(e){
            e.preventDefault();
            $(this).parents('form').find('input[type="checkbox"]').prop('checked', false);
        });

    });
})(jQuery);

