var waxe = waxe || {};

(function($, ns){
    "use strict";


    var Form = function(jstreeData){
        this.selector = 'form#xmltool-form';
        this.filename_selector = '#_xml_filename';
        this.$element = null;
        this.status = null;
        this.$filename = null;
        this.filename = null;
        this.auto_save_interval = null;
        this.auto_save_time = 1000 * 60;
        this.load(jstreeData);
    };

    Form.STATUS_UPDATED = 'updated';

    Form.prototype.load = function(jstreeData){
        var that = this;
        this.$element = null;
        this.status = null;
        this.$filename = null;
        var $e = $(this.selector);
        clearInterval(this.auto_save_interval);
        if(!$e.length) {
            // Add css on the save buttons to be clear that these buttons
            // are disabled!
            return false;
        }
        this.$element = $e;
        // We assume we always have the hidden input in the form
        this.$filename = $e.find(this.filename_selector);
        this.filename = this.$filename.val();
        this.$element.xmltool({
            add_element_url: this.$element.data('add-href'),
            comment_modal_url: this.$element.data('comment-href'),
            jstreeSelector: '#tree',
            jstreeData: jstreeData,
            message: function(){
                var d = $(document);
                d.message.apply(d, arguments);
            },
            treeContainerSelector: waxe.layout.SELECTORS.center
        }).submit($.proxy(this.save, this)).on('loadedJstree', function(){
            waxe.layout.showTree();
        });
        this.$element.on('change.contenteditablesync', 'textarea', function() {
            that.status = that.STATUS_UPDATED;
        });
        this.$element.on('field_change.xmltool', function(){
            that.status = that.STATUS_UPDATED;
        });
        this.auto_save();
        return true;
    };

    Form.prototype.setFilename = function(v){
        if (this.$element) {
            this.$filename.val(v);
            this.filename = v;
            return true;
        }
        return false;
    };

    Form.prototype.save = function(e){
        if(!this.$element) {
            return false;
        }
        e.preventDefault();
        var that = this;
        var params = this.$element.serialize();
        waxe.ajax.POST(this.$element.data('href'), params, function(data){
            if (data.status){
                that.status = null;
                $(document).message('success', 'Saved');
                // TODO: we should use waxe.dom to update the content!
                $('.breadcrumb').html(data.breadcrumb);
            }
            else{
                $(document).message('error', data.error_msg);
            }
        });
    };

    Form.prototype.auto_save = function(){
        var that = this;
        var save = function(){
            if (that.status === that.STATUS_UPDATED){
                that.$element.submit();
                that.status = null;
            }
        };
        // TODO: improve this logic for the new files!
        if (this.filename){
            this.auto_save_interval = setInterval(save, this.auto_save_time);
        }
    };

    $(document).ready(function(){
        var data = null;
        if (typeof jstree_data !== 'undefined') {
            data = jstree_data;
        }
        waxe.form = new Form(data);
    });

})(jQuery, waxe);
