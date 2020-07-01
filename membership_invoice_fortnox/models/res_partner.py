# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import Warning

import requests
import json

import logging
_logger = logging.getLogger(__name__)
#FIXME: This part is not working yet. Have to be fixed, Realated to account_invoice.py
class ResCompany(models.Model):
    _inherit = "res.company"
    
    invoice_fortnox = fields.Boolean(string = "Send to Fortnox", default=True)
    # ~ invoice_is_fortnox = fields.Boolean('Fortnox by default', default=True)

class res_partner(models.Model):
    _inherit = 'res.partner'
#FIXME:make fortnox_update auto-updating.
    @api.multi
    def fortnox_update(self):
        # Customer (PUT https://api.fortnox.se/3/customers)
        for partner in self:
            if not partner.commercial_partner_id.ref:
                url = "https://api.fortnox.se/3/customers"
                """ r = response """
                r = self.env['res.config.settings'].fortnox_request('post', url,
                    data={
                        "Customer": {
                            "Address1": partner.street,
                            "Address2": partner.street2,
                            "City": partner.city,
                            "Comments": partner.comment,
                            "CountryCode": "SE",
                            "Currency": "SEK",
                            # ~ "CustomerNumber": partner.commercial_partner_id.id,
                            "Email": partner.email,
                            "Name": partner.commercial_partner_id.name,
                            "OrganisationNumber": partner.commercial_partner_id.company_registry,
                            "OurReference": partner.commercial_partner_id.user_id.name,
                            "Phone1": partner.commercial_partner_id.phone,
                            "Phone2": None,
                            "PriceList": "A",
                            "ShowPriceVATIncluded": False,
                            "TermsOfPayment": partner.commercial_partner_id.property_payment_term_id.name,
                            "Type": "COMPANY",
                            "VATNumber": partner.commercial_partner_id.vat,
                            "VATType": "SEVAT",
                            "WWW": partner.commercial_partner_id.website,
                            "YourReference": partner.name,
                            "ZipCode": partner.zip,
                        }
                    })
            if partner.commercial_partner_id.ref:
                url = "https://api.fortnox.se/3/customers/%s" % partner.commercial_partner_id.ref
                """ r = response """
                r = self.env['res.config.settings'].fortnox_request('put', url,
                    data={
                        "Customer": {
                            "Address1": partner.street,
                            "Address2": partner.street2,
                            "City": partner.city,
                            "Comments": partner.comment,
                            "CountryCode": "SE",
                            "Currency": "SEK",
                            # ~ "CustomerNumber": partner.commercial_partner_id.id,
                            "Email": partner.email,
                            "Name": partner.commercial_partner_id.name,
                            "OrganisationNumber": partner.commercial_partner_id.company_registry,
                            "OurReference": partner.commercial_partner_id.user_id.name,
                            "Phone1": partner.commercial_partner_id.phone,
                            "Phone2": None,
                            "PriceList": "A",
                            "ShowPriceVATIncluded": False,
                            "TermsOfPayment": partner.commercial_partner_id.property_payment_term_id.name,
                            "Type": "COMPANY",
                            "VATNumber": partner.commercial_partner_id.vat,
                            "VATType": "SEVAT",
                            "WWW": partner.commercial_partner_id.website,
                            "YourReference": partner.name,
                            "ZipCode": partner.zip,
                        }
                    })
            
            r = json.loads(r)
            raise Warning(str(r))
            partner.commercial_partner_id.ref = r["Customer"]["CustomerNumber"]
    
            return r  
            
    # ~ def fortnox_request(self,request_type,url,data=None):
        # ~ # Customer (POST https://api.fortnox.se/3/customers)
        # ~ Access_token=self.env['ir.config_parameter'].sudo().get_param('fortnox.access.token')
        # ~ Client_secret=self.env['ir.config_parameter'].sudo().get_param('fortnox.client.secret')
        # ~ headers = {
            # ~ "Access-Token": Access_token,
            # ~ "Client-Secret": Client_secret,
            # ~ "Content-Type":"application/json",
            # ~ "Accept":"application/json",
        # ~ }

        # ~ try:
            # ~ if request_type == 'post':
                # ~ r = requests.post(url=url,headers = headers,data = json.dumps(data))
            # ~ if request_type == 'put':
                # ~ r = requests.put(url=url,headers = headers,data = json.dumps(data))
            # ~ if request_type == 'get':
                # ~ r = requests.get(url=url,headers = headers)
            # ~ if request_type == 'delete':
                # ~ r = requests.get(url=url,headers = headers)
            # ~ _logger.warn(' >>>>>>> Response HTTP Status Code : {status_code}'.format(status_code=r.status_code))
            # ~ _logger.warn('Response HTTP Response Body : {content}'.format(content=r.content))


            # ~ if not r.status_code == 200: 
            # ~ if r.status_code in [403]:
                # ~ raise Warning(r.content)
            
        # ~ except requests.exceptions.RequestException as e:
            # ~ _logger.warn('HTTP Request failed %s' % e)
            # ~ raise Warning('HTTP Request failed %s' % e)
        # ~ return r.content
