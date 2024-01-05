# -*- coding:utf-8 -*-
# Odootech
# 2024

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from datetime import date, datetime
from dateutil.relativedelta import relativedelta as rdelta
import time
import re
import requests
import logging
_logger = logging.getLogger('account_currency_rate_auto_update')


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def run_currency_rate_update(self):
        ''' Монгол банкны ханшийг автоматаар шинэчлэн татах сервис
            Ханш татах json сервис: http://monxansh.appspot.com/xansh.json?currency=USD
        '''

        currencies = self.env['res.currency'].sudo().search(
            [('active', '=', True)])
        company = self.env.user.company_id

        if currencies:
            currencies -= company.currency_id
        if not currencies:
            _logger.warn(
                'There is no currencies for auto update rate from Web Service.')
            return True

        curr_params = '|'.join(currencies.mapped('name'))
        currency_by_name = dict([(x.name, x) for x in currencies])
        aurl = 'http://monxansh.appspot.com/xansh.json?currency='+curr_params

        response = requests.get(aurl, timeout=60*3)
        if not response:
            _logger.warn('There is no response for Web Service %s.' % aurl)
            return True
        updated = {}

        for ratedata in response.json():
            if currency_by_name.get(ratedata['code'], False):
                currency = currency_by_name[ratedata['code']]
                rate_date = datetime.strptime(
                    ratedata['last_date'], '%Y-%m-%d %H:%M:%S') + rdelta(days=1)
                exists = self.env['res.currency.rate'].search(
                    [('currency_id', '=', currency.id),
                     ('name', '>=', rate_date.strftime('%Y-%m-%d 00:00:00')),
                     ('name', '<=', rate_date.strftime('%Y-%m-%d 23:59:59')),
                     '|', ('company_id', '=', False), ('company_id', '=', company.id)])
                if not exists:
                    updated.setdefault(currency.name, {})
                    updated[currency.name][rate_date] = ratedata['rate_float']
                    self.env['res.currency.rate'].create({
                        'name': rate_date.strftime('%Y-%m-%d 00:00:00'),
                        'currency_id': currency.id,
                        'rate': ratedata['rate_float']
                    })
        if updated:

            updated_message = []
            for curr, currdates in updated.items():
                for ratedate, rate in currdates.items():
                    updated_message.append(u"%s:%s on %s" %
                                           (curr, rate, ratedate))
            _logger.info('Currency rate updated from Web Service: %s' %
                         ', '.join(updated_message))
        return True
