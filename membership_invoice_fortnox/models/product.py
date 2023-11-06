# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# build dateutil helper, starting with the relevant *lazy* imports
import dateutil
import dateutil.parser
import dateutil.relativedelta
import dateutil.rrule
import dateutil.tz
import base64
import requests
import json


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import datetime
import time

from pytz import timezone
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def article_update(self):
        for product in self:
            if not product.default_code:
                raise UserError('Missing default code for product')

            url = "https://api.fortnox.se/3/articles/%s" % product.default_code
            r = self.env.user.company_id.fortnox_request(
                'get', url, raise_error=False)
            default_code = r.get('Article', {}).get('ArticleNumber')
            if default_code == product.default_code:
                try:
                    url = f"https://api.fortnox.se/3/articles/{product.default_code}"
                    self.env.user.company_id.fortnox_request(
                        'put',
                        url,
                        data={
                            "Article": {
                                "Description": product.name,
                            }
                        })
                except requests.exceptions.RequestException as e:
                    _logger.exception(f'Request error in article update: {e}')
            else:
                r = self.env.user.company_id.fortnox_request(
                    'post',
                    'https://api.fortnox.se/3/articles',
                    data={
                        'Article': {
                            'Description': product.name,
                            'ArticleNumber': product.default_code,
                        }
                    })



