odoo.define('portal_communication.portal_communication', function (require) {

    var ajax = require('web.ajax');

    $(function (){
        $('.sst-communication-select').click(function(){
            ajax.rpc('/communication_preferences/change_preference',  {'id': this.id, 'checked': this.checked})
                .then(function(data){})
        })
    })
})
