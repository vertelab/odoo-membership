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

    def fortnox_update(self):
        # Customer (POST https://api.fortnox.se/3/customers)

        try:
            r = requests.post(
                url="https://api.fortnox.se/3/customers",
                headers = {
                    "Access-Token":"61cf63ae-4ab9-4a95-9db5-753781c4f41f",
                    "Client-Secret":"3Er4kHXZTJ",
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
        except requests.exceptions.RequestException as e:
            _logger.warn('HTTP Request failed %s' % e)
