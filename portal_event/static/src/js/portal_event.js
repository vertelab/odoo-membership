odoo.define('portal_event.portal_event', function (require) {

    var ajax = require('web.ajax');

    $(function (){
        $('.sst-field-of-interest-select').click(function(){
            console.log(this)
            ajax.rpc('/portal_event/event_type_tags',  {'id': [this.id]}) 
                .then(function(data){})
        })
    })
})

//~ 'id': this.id, 'checked': this.checked
