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
from tabulate import tabulate
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

import requests
from bs4 import BeautifulSoup


class res_partner(models.Model):
    _inherit = 'res.partner'

    url_financial_supervisory = fields.Text(string='Finansinspektionen')

    @api.multi
    def fi_scrape_company(self):
        rek_status = self.env['membership.recruitment.status'].search([])
        if len(rek_status) == 0:
            rek_status = None
        else:
            rek_status = rek_status[0].id
        for partner in self:
            page = requests.get(self.url_financial_supervisory)
            soup = BeautifulSoup(page.content, 'html.parser')
            for atag in soup.findAll('a'):
                if "/sv/vara-register/foretagsregistret/details/?id=" in atag['href']:
                    _logger.warning("atag %s | %s" % (atag['href'], atag.text.strip()))
                    (last, first) = atag.text.strip().split(', ')
                    name = "%s %s" % (first, last)
                    _logger.warning("atag name %s" % name)
                    child = self.env['res.partner'].search([('parent_id', '=', partner.id), ('name', '=', name)])
                    if not child:
                        self.env['res.partner'].create({
                            'name': name, 'parent_id': partner.id,
                            'url_financial_supervisory': "https://fi.se/%s" % atag['href'],
                            'insurance_company_type': 'accommodator',
                            'membership_recruitment_status_id': rek_status,
                        })

                    # TODO  tag missing members

    def get_fi_partner_difference(self):

        partner_ids = self.env['res.partner'].browse(self._context.get('active_ids'))

        no_url_financial_supervisory = []
        in_odoo_not_in_web = []
        in_web_not_in_odoo = []

        for partner in partner_ids:
            children_from_web = []
            children_from_odoo = []

            if not partner.url_financial_supervisory:
                no_url_financial_supervisory.append(partner.name)

            else:
                page = requests.get(partner.url_financial_supervisory)
                soup = BeautifulSoup(page.content, 'html.parser')

                for atag in soup.findAll('a'):
                    if "/sv/vara-register/foretagsregistret/details/?id=" in atag['href']:
                        (last, first) = atag.text.strip().split(', ')
                        name = "%s %s" % (first, last)
                        children_from_web.append(name)
                        child = self.env['res.partner'].search([('parent_id', '=', partner.id), ('name', '=', name)])
                        children_from_odoo.append(child.name)

                in_odoo_not_in_web.extend(
                    [elem for elem in list(set(children_from_odoo).difference(children_from_web)) if elem]
                )

                in_web_not_in_odoo.extend(
                    [elem for elem in list(set(children_from_web).difference(children_from_odoo)) if elem]
                )

        result = ""

        result += "==" * 40 + "\n"
        result += _("List of Records in Odoo that lacks FI Link: \n\n".upper())
        result += '\n'.join(no_url_financial_supervisory)

        result += "\n" + "==" * 40 + "\n"
        result += _("List of Users in Odoo but not in FI: \n\n".upper())
        result += '\n'.join(in_odoo_not_in_web)

        result += "\n" + "==" * 40 + "\n"
        result += _("List of Users in FI but not in Odoo: \n\n".upper())
        result += '\n'.join(in_web_not_in_odoo)

        raise UserError(result)