# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import Warning

import requests
import json

import logging
_logger = logging.getLogger(__name__)



class res_partner(models.Model):
    _inherit = 'res.partner'


    def fortnox_get_access_code(self):
        # ~ Authorization_code="31bcb6c6-cc64-8fe4-68cb-2acbaf8a5128"
        # ~ Access_token = "7909a2c5-b810-4d62-84c6-bb0df1f84c1f"
        # ~ Client_secret = "m4uufTy3n1"        
        Access_token=self.env['ir.config_parameter'].sudo().get_param('fortnox.access.token')
        if not Access_token:
            Authorization_code=self.env['ir.config_parameter'].sudo().get_param('fortnox.authorization.code')
            if not Authorization_code:
                raise Warning("You have to set up Authorization_token for FortNox, you get that when you activate Odoo in your FortNox-account")
            Client_secret=self.env['ir.config_parameter'].sudo().get_param('fortnox.client.secret')
            if not Client_secret:
                raise Warning("You have to set up Client_secret for FortNox, you get that when you activate Odoo in your FortNox-account")
            try:
                _logger.warn('Authorization-code %s Client Secret %s' % (Authorization_code,Client_secret))

                r = requests.post(
                    url="https://api.fortnox.se/3/customers",    
                    headers = {
                        "Authorization-Code": Authorization_code,
                        "Client-Secret": Client_secret,
                        "Content-Type":"application/json",
                        "Accept":"application/json",
                    },
                )
                _logger.warn('Response HTTP Status Code : {status_code}'.format(status_code=r.status_code))
                _logger.warn('Response HTTP Response Body : {content}'.format(content=r.content))
                auth_rec = eval(r.content)
                Access_token = auth_rec.get('Authorization',{}).get('AccessToken')
                self.env['ir.config_parameter'].sudo().set_param('fortnox.access.token',Access_token)
            except requests.exceptions.RequestException as e:
                _logger.warn('HTTP Request failed %s' % e)

    def fortnox_update(self):
        # Customer (POST https://api.fortnox.se/3/customers)
        Access_token=self.env['ir.config_parameter'].sudo().get_param('fortnox.access.token')
        Client_secret=self.env['ir.config_parameter'].sudo().get_param('fortnox.client.secret')

        try:
            r = requests.post(
                url="https://api.fortnox.se/3/customers",    
                headers = {
                    "Access-Token": Access_token,
                    "Client-Secret": Client_secret,
                    "Content-Type":"application/json",
                    "Accept":"application/json",
                },
                data = json.dumps({
                    "Customer": {
                        "Name": "Klara Norström"
                    }
                })
            )
            
            _logger.warn('Response HTTP Status Code : {status_code}'.format(status_code=r.status_code))
            _logger.warn('Response HTTP Response Body : {content}'.format(content=r.content))

            raise Warning(r.content)
            
            if r.status_code in [403]:
                raise Warning(r.content)
            
        except requests.exceptions.RequestException as e:
            _logger.warn('HTTP Request failed %s' % e)
            raise Warning('HTTP Request failed %s' % e)
