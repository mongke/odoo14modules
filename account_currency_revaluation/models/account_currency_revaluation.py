# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CurrencyRevaluation(models.Model):
    # ===========================================================================
    # Private fields
    # ===========================================================================
    _name = 'account.currency.revaluation'
    _description = 'Currency Revaluation'
    _order = 'date DESC, currency_id'

    # ===========================================================================
    # Public fields
    # ===========================================================================
    name = fields.Char(
        string='Reference', readonly=True,
        copy=False, default='Draft Revaluation')
    state = fields.Selection(
        [('draft', 'Draft'), ('computed', 'Computed'), ('posted', 'Posted')],
        string='Status', readonly=True, copy=False, default='draft')
    date = fields.Date(
        string='Date', readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today, required=True)
    rate = fields.Float(string='Rate', digits=(12, 6),
                        readonly=True, copy=False)
    currency_id = fields.Many2one('res.currency',
                                  string='Currency', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  domain=lambda self: [('id', '!=', self.env.user.company_id.currency_id.id)])
    journal_id = fields.Many2one('account.journal',
                                 string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain=[('type', '=', 'general')])
    company_currency_id = fields.Many2one('res.currency',
                                          required=True, readonly=True,
                                          default=lambda self: self.env.user.company_id.currency_id)
    line_ids = fields.One2many('account.currency.revaluation.line', 'revaluation_id',
                               string='Currency Revaluation Lines', readonly=True, copy=False)
    difference_total = fields.Monetary(
        string='Difference Total', readonly=True, store=True,
        currency_field='company_currency_id', compute='_compute_difference_total')

    _sql_constraints = [(
        'unique_currency_revaluation',
        'UNIQUE(date, currency_id)',
        _('You can not enter more than one currency revaluation '
          'for the same date and same currency. '
          'Combination of date and currency must be unique.')
    )]

    # ===========================================================================
    # Compute methods
    # ===========================================================================
    @api.depends('line_ids.difference')
    def _compute_difference_total(self):
        self.ensure_one()

        self.difference_total = sum(line.difference for line in self.line_ids)

    # ===========================================================================
    # CRUD methods
    # ===========================================================================
    def unlink(self):
        if any(rec.state != 'draft' for rec in self):
            raise ValidationError(
                _('You can not delete a currency valuation that is either Computed or Posted!'))
        return super(CurrencyRevaluation, self).unlink()

    # ===========================================================================
    # Business methods
    # ===========================================================================
    def compute(self):
        self.ensure_one()

        if self.state != 'draft':
            raise ValidationError(_('Only a draft currency revaluation can be COMPUTED. '
                                    'You are trying to compute a currency revaluation in state \'%s\'.') % self.state)

        # Get rate at specified date
        currency_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', self.currency_id.id),
            ('name', '=', self.date)
        ], order='name', limit=1)
        if not currency_rate:
            raise ValidationError(
                _('Currency rate is not defined on %s. To proceed, enter a rate on this date.') % self.date)
        self.rate = currency_rate.rate

        # Check if there are any accounts which allow currency revaluation
        account_count = self.env['account.account'].search_count(
            [('currency_revaluation', '=', True)])
        if account_count < 1:
            raise ValidationError(
                _('There are no accounts that allow currency revaluation!'))

        # Retrieve account move lines
        query = '''
            SELECT
                A.account_id,
                SUM(A.amount_currency) AS balance_original,
                SUM(A.balance) AS balance_prev_rate
             FROM account_move_line AS A
                INNER JOIN account_account AS B ON B.id = A.account_id
             WHERE B.currency_revaluation = 't'
                AND A.currency_id = %s
                AND A.date < %s
             GROUP BY A.account_id;
        '''
        self.env.cr.execute(query, (self.currency_id.id, self.date))
        move_lines = self.env.cr.fetchall()

        # Compute revaluation
        account_ids = []
        for account_id, balance_original, balance_prev_rate in move_lines:
            # Set line
            balance_last_rate = balance_original * self.rate
            difference = balance_last_rate - balance_prev_rate
            line_vals = {
                'revaluation_id': self.id,
                'account_id': account_id,
                'balance_original': balance_original,
                'balance_prev_rate': balance_prev_rate,
                'balance_last_rate': balance_last_rate,
                'difference': difference,
            }
            self.env['account.currency.revaluation.line'].create(line_vals)
            account_ids.append(account_id)

        if len(account_ids) == 0:
            raise ValidationError(_('There is no data to revaluate!'))

        self.name = 'Computed Revaluation'
        self.state = 'computed'

    def cancel_computation(self):
        self.ensure_one()

        if self.state != 'computed':
            raise ValidationError(_('Only a computed currency revaluation can be CANCELLED.'
                                    'You are trying to cancel a currency revaluation in state %s.') % self.state)

        lines = self.env['account.currency.revaluation.line'].search([
            ('revaluation_id', '=', self.id)
        ])
        lines.unlink()

        self.name = 'Draft Revaluation'
        self.state = 'draft'

    def post(self):
        self.ensure_one()
        if self.state != 'computed':
            raise ValidationError(_('Only a computed currency revaluation can be POSTED.'
                                    'You are trying to post a currency revaluation in state %s.') % self.state)

        next_revaluations = self.env['account.currency.revaluation'].search([
            ('currency_id', '=', self.currency_id.id),
            ('state', '=', 'posted'),
            ('date', '>=', self.date)
        ])
        if next_revaluations:
            raise ValidationError(_('There are already posted currency revaluations after %s.'
                                    'Date must be greater than last currency revaluation.') % self.date)
        # Set reference
        sequence_code = 'currency.revaluation.doc'
        reference = self.env['ir.sequence'].with_context(
            ir_sequence_date=self.date).next_by_code(sequence_code)

        lines = self.env['account.currency.revaluation.line'].search([
            ('revaluation_id', '=', self.id)
        ])
        for line in lines:
            self._create_journal_entry(line.account_id.id, line.difference)

        self.name = reference
        self.state = 'posted'

    def _create_journal_entry(self, account_id, difference):
        move = self.env['account.move'].create(self._get_move_vals())
        line_name = self._get_move_line_name(account_id)
        line_base_data = {
            'move_id': move.id,
            'name': line_name,
            'date': self.date,
            'amount_currency': 0.0,
        }

        AccountMoveLine = self.env['account.move.line'].with_context(
            check_move_validity=False)
        if difference >= 0.0:
            # Debit line
            line_data = {
                'currency_id': self.currency_id.id,
                'debit': difference,
                'account_id': account_id,
            }
            line_data.update(line_base_data)
            AccountMoveLine.create(line_data)

            # Credit line
            line_data = {
                'credit': difference,
                'account_id': self.journal_id.default_credit_account_id.id,
            }
            line_data.update(line_base_data)
            AccountMoveLine.create(line_data)
        else:
            # Credit line
            difference = abs(difference)
            line_data = {
                'currency_id': self.currency_id.id,
                'credit': difference,
                'account_id': account_id,
            }
            line_data.update(line_base_data)
            AccountMoveLine.create(line_data)

            # Debit line
            line_data = {
                'debit': difference,
                'account_id': self.journal_id.default_debit_account_id.id,
            }
            line_data.update(line_base_data)
            AccountMoveLine.create(line_data)
        move.post()

    def _get_move_vals(self):
        journal = self.journal_id
        if not journal.sequence_id:
            raise ValidationError(_('Configuration Error!'), _(
                'The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise ValidationError(_('Configuration Error!'), _(
                'The sequence of journal %s is deactivated.') % journal.name)
        name = journal.with_context(
            ir_sequence_date=self.date).sequence_id.next_by_id()
        return {
            'name': name,
            'date': self.date,
            'company_id': journal.company_id.id,
            'journal_id': journal.id,
        }

    def _get_move_line_name(self, account_id):
        text = _('%(currency)s %(account)s %(rate)s currency revaluation')
        account = self.env['account.account'].browse(account_id)
        data = {'account': account.code or False,
                'currency': self.currency_id.name or False,
                'rate': self.rate or False}
        return text % data


class CurrencyRevaluationLine(models.Model):
    # ===========================================================================
    # Private fields
    # ===========================================================================
    _name = 'account.currency.revaluation.line'
    _description = 'Currency Revaluation Line'
    _order = 'account_id'

    # ===========================================================================
    # Public fields
    # ===========================================================================
    revaluation_id = fields.Many2one('account.currency.revaluation',
                                     string='Currency Revaluation', ondelete='cascade', index=True)
    account_id = fields.Many2one(
        'account.account', string='Account', ondelete='restrict', index=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', related='account_id.currency_id')
    company_currency_id = fields.Many2one('res.currency',
                                          readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    balance_original = fields.Monetary(
        string='Balance in Original Currency', currency_field='currency_id')
    balance_prev_rate = fields.Monetary(
        string='Balance at Previous Rate', currency_field='company_currency_id')
    balance_last_rate = fields.Monetary(
        string='Balance at Last Rate', currency_field='company_currency_id')
    difference = fields.Monetary(
        string='Difference', currency_field='company_currency_id')
