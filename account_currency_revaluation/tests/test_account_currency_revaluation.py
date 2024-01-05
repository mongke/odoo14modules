# -*- coding: utf-8 -*-
'''
from odoo.tests.common import SavepointCase
from odoo import fields
from datetime import timedelta

class TestCurrencyRevaluation(SavepointCase):
    _account_usd = False
    _amount_usd = 247.0
    _date_prev = fields.Date.today()
    _date_last = (fields.Date.from_string(_date_prev) + timedelta(5)).strftime(fields.DATE_FORMAT)
    _journal_exchange = False
    _journal_usd = False
    _rate_prev = 2468.0
    _rate_last = 2455.0
    _revaluation = False

    @classmethod
    def setUpClass(cls):
        super(TestCurrencyRevaluation, cls).setUpClass()

        # Set currencies
        ResCurrency = cls.env['res.currency']

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

        company = cls.env.user.company_id
        company.write({ 'currency_id': currency_mnt.id })
'''
        # Set previous rate
#        query = '''
#            INSERT INTO res_currency_rate (name, rate, currency_id, company_id)
#                VALUES (%s, %s, %s, %s);
#        '''
#        cls.cr.execute(query, (cls._date_prev, 1.0, currency_mnt.id, company.id))
#        cls.cr.execute(query, (cls._date_prev, cls._rate_prev, currency_usd.id, company.id))

        # Set last rate
#        query = '''
#            INSERT INTO res_currency_rate (name, rate, currency_id, company_id)
#                VALUES (%s, %s, %s, %s);
#        '''
#        cls.cr.execute(query, (cls._date_last, cls._rate_last, currency_usd.id, company.id))

        # Set accounts
#        query = '''
#            UPDATE account_account
#                SET currency_revaluation = \'f\';
#        '''
#        cls.cr.execute(query)

#        account_type = cls.env.ref('account.data_account_type_liquidity')
#        query = '''
#            INSERT INTO account_account (code, name, currency_revaluation, user_type_id, company_id)
#                VALUES ('TEST100200', 'Cash USD', 't', %s, %s) RETURNING id;
#        '''
#        cls.cr.execute(query, (account_type.id if account_type else False, company.id))
#        account_usd_record = cls.cr.fetchall()
#        account_usd_id = account_usd_record[0][0]
#        cls._account_usd = cls.env['account.account'].search([('id', '=', account_usd_id)])

        # Set USD journal
#        journal_usd_sequence = cls.env['ir.sequence'].search([], order='id DESC', limit=1)
#        query = '''
#            INSERT INTO account_journal (name, type, code, sequence_id, currency_id, company_id)
#                VALUES ('Cash USD', 'cash', 'TCUSD', %s, %s, %s) RETURNING id;
#        '''
#        cls.cr.execute(query, (journal_usd_sequence.id, currency_usd.id, company.id))
#        journal_usd_record = cls.cr.fetchall()
#        journal_usd_id = journal_usd_record[0][0]
#        cls._journal_usd = cls.env['account.journal'].search([('id', '=', journal_usd_id)])

        # Set journal entry in USD
#        amount_mnt = ResCurrency._compute(
#            from_currency=currency_usd,
#            to_currency=currency_mnt,
#            from_amount=cls._amount_usd)
#        query = '''
#            WITH move AS
#            (
#                INSERT INTO account_move (name, date, company_id, journal_id, state)
#                    VALUES (%s, %s, %s, %s, 'posted') RETURNING id
#            )

#            INSERT INTO account_move_line (move_id, name, date, date_maturity, currency_id, account_id, amount_currency, balance)
#                SELECT id, %s, %s, %s, %s, %s, %s, %s FROM move RETURNING id;
#        '''
#        move_name = cls._journal_usd.with_context(ir_sequence_date=cls._date_prev).sequence_id.next_by_id()
#        cls.cr.execute(query, (
#            move_name, cls._date_prev, company.id, cls._journal_usd.id,
#            '/', cls._date_prev, cls._date_prev, currency_usd.id, cls._account_usd.id, cls._amount_usd, amount_mnt
#        ))

        # Set currency exchange journal
#        query = '''
#            INSERT INTO account_account (code, name, user_type_id, company_id)
#                VALUES ('TEST811200', 'Currency Exchange Gain/Loss', %s, %s) RETURNING id;
#        '''
#        cls.cr.execute(query, (account_type.id if account_type else False, company.id))
#        journal_exchange_account_record = cls.cr.fetchall()
#        journal_exchange_account_id = journal_exchange_account_record[0][0]

#        journal_exchange_sequence = cls.env['ir.sequence'].search([], order='id DESC', limit=1)
#        query = '''
#            INSERT INTO account_journal (name, type, code, default_debit_account_id, default_credit_account_id, sequence_id, company_id)
#                VALUES ('Currency Exchange', 'general', 'EXCH', %s, %s, %s, %s) RETURNING id;
#        '''
#        cls.cr.execute(query, (journal_exchange_account_id, journal_exchange_account_id, journal_exchange_sequence.id, company.id))
#        journal_exchange_record = cls.cr.fetchall()
#        journal_exchange_id = journal_exchange_record[0][0]
#        cls._journal_exchange = cls.env['account.journal'].search([('id', '=', journal_exchange_id)])

        # Set revaluation
#        cls._revaluation = cls.env['account.currency.revaluation'].create({
#            'date': cls._date_last,
#            'currency_id': currency_usd.id,
#            'journal_id': cls._journal_exchange.id,
#        })

'''
    def test_compute(self):
        self.assertEqual(self._revaluation.state, 'draft')

        self._revaluation.compute()
        self.assertEqual(self._revaluation.state, 'computed')

        amount_prev = self._amount_usd * self._rate_prev
        amount_last = self._amount_usd * self._rate_last
        difference = amount_last - amount_prev
        self.assertEqual(self._revaluation.difference_total, difference)

    def test_cancel_computation(self):
        self._revaluation.compute()
        self.assertEqual(self._revaluation.state, 'computed')

        lines = self.env['account.currency.revaluation.line'].search([
            ('revaluation_id', '=', self._revaluation.id)
        ])
        self.assertGreater(len(lines), 0)

        self._revaluation.cancel_computation()
        self.assertEqual(self._revaluation.state, 'draft')

        lines = self.env['account.currency.revaluation.line'].search([
            ('revaluation_id', '=', self._revaluation.id)
        ])
        self.assertEqual(len(lines), 0)

    def test_post(self):
        self._revaluation.compute()
        self.assertEqual(self._revaluation.state, 'computed')

        self._revaluation.post()
        self.assertEqual(self._revaluation.state, 'posted')

        moves = self.env['account.move'].search([
            ('journal_id', '=', self._revaluation.journal_id.id),
            ('date', '=', self._date_last),
        ])
        amount_credit = 0
        amount_debit = 0
        for move in moves:
            for line in move.line_ids:
                amount_debit += line.debit
                amount_credit += line.credit
        self.assertEqual(amount_debit, amount_credit)

        amount_prev = self._amount_usd * self._rate_prev
        amount_last = self._amount_usd * self._rate_last
        difference = amount_last - amount_prev
        self.assertEqual(abs(difference), amount_debit)
'''
