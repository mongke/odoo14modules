# -*- coding: utf-8 -*-

from odoo import models, api


class Currency(models.Model):
    # Private fields
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        return super(Currency, self)._get_conversion_rate(
            from_currency=to_currency,
            to_currency=from_currency,
            company=company,
            date=date
        )
