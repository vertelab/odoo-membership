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
import time
import re
from odoo.exceptions import except_orm, Warning, RedirectWarning
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    def _get_invoice_line_name_from_product(self):
        """ Returns the automatic name to give to the invoice line depending on
        the product it is linked to.
        """
        self.ensure_one()
        if not self.product_id:
            return ''
        return self.product_id.name
        

	
    
