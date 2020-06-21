# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

import requests
from bs4 import BeautifulSoup

class res_partner(models.Model):
    _inherit = 'res.partner'

    url_financial_supervisory = fields.Text(string = 'Finansinspektionen')
    
    @api.multi
    def fi_scrape_company(self):
        for partner in self:
            page = requests.get(self.url_financial_supervisory)
            soup = BeautifulSoup(page.content, 'html.parser')
            # ~ raise Warning(soup.findAll('a'))
            for atag in soup.findAll('a'):
                if "/sv/vara-register/foretagsregistret/details/?id=" in atag['href']:
                    _logger.warn("atag %s | %s" % (atag['href'],atag.text.strip()))
                    (last,first) = atag.text.strip().split(', ')
                    name = "%s %s" % (first,last)
                    _logger.warn("atag name %s" % name)
                    child = self.env['res.partner'].search([('parent_id', '=', partner.id),('name','=',name)])
                    if not child:
                        self.env['res.partner'].create({'name':name,'parent_id':partner.id,'url_financial_supervisory': "https://fi.se/%s" % atag['href'],'insurance_company_type': 'accommodator'})
                
            