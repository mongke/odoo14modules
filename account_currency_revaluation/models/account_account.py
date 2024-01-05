# -*- coding: utf-8 -*-

from odoo import models, fields

class AccountAccount(models.Model):
    # Private fields
    _inherit = 'account.account'

    # Public fields
    currency_revaluation = fields.Boolean(
        string='Currency Revaluation',
        default=False,
    )