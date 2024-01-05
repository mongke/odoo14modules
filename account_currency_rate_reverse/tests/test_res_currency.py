# -*- coding: utf-8 -*-
'''
from odoo.tests.common import TransactionCase
from odoo import fields

class TestCurrency(TransactionCase):
    def test_reverse_rate(self):
        # Set currencies
        ResCurrency = self.env['res.currency']

        currency_usd = ResCurrency.search([('name', '=', 'USD')], limit=1)
        if not currency_usd:
            currency_usd = ResCurrency.search([
                ('name', '=', 'USD'),
                ('active', '=', False),
            ], limit=1)
            currency_usd.write({ 'active': True })

        currency_mnt = ResCurrency.search([('name', '=', 'MNT')], limit=1)
        if not currency_mnt:
            currency_mnt = ResCurrency.search([
                ('name', '=', 'MNT'),
                ('active', '=', False),
            ], limit=1)
            currency_mnt.write({ 'active': True })

        # Set rates
        company = self.env.user.company_id
        rate_mnt = 1.0
        rate_usd = 2468.0

        date = fields.Datetime.now()
'''
#        query = '''INSERT INTO res_currency_rate (name, rate, currency_id, company_id)
#                        VALUES (%s, %s, %s, %s);'''
'''
        self.cr.execute(query, (date, rate_mnt, currency_mnt.id, company.id))
        self.cr.execute(query, (date, rate_usd, currency_usd.id, company.id))

        # Convert rates
        amount_usd = 247.0
        amount_mnt = currency_mnt.round(amount_usd * rate_usd)
        computed_amount = ResCurrency._compute(
            from_currency=currency_usd,
            to_currency=currency_mnt,
            from_amount=amount_usd)

        # Check results
        self.assertEqual(computed_amount, amount_mnt)
'''
