# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    # ===========================================================================
    # Private fields
    # ===========================================================================
    _inherit = 'account.move.line'

    # ===========================================================================
    # Business methods
    # ===========================================================================
    @api.model
    def get_data_for_manual_reconciliation(self, res_type, res_ids=None, account_type=None):
        """ Returns the data required for the invoices & payments matching of partners/accounts (list of dicts).
            If no res_ids is passed, returns data for all partners/accounts that can be reconciled.

            :param res_type: either 'partner' or 'account'
            :param res_ids: ids of the partners/accounts to reconcile, use None to fetch data indiscriminately
                of the id, use [] to prevent from fetching any data at all.
            :param account_type: if a partner is both customer and vendor, you can use 'payable' to reconcile
                the vendor-related journal entries and 'receivable' for the customer-related entries.
        """
        if res_ids is not None and len(res_ids) == 0:
            # Note : this short-circuiting is better for performances, but also required
            # since postgresql doesn't implement empty list (so 'AND id in ()' is useless)
            return []
        res_ids = res_ids and tuple(res_ids)

        assert res_type in ('partner', 'account')
        assert account_type in ('payable', 'receivable', None)
        is_partner = res_type == 'partner'
        res_alias = is_partner and 'p' or 'a'

        # Start - Edited by Odootech -------------------------------------------
        query = ("""
            SELECT {0} account_id, account_name, account_code, max_date,
                   to_char(last_time_entries_checked, 'YYYY-MM-DD') AS last_time_entries_checked
            FROM (
                    SELECT {1}
                        {res_alias}.last_time_entries_checked AS last_time_entries_checked,
                        a.id AS account_id,
                        a.name AS account_name,
                        a.code AS account_code,
                        MAX(l.write_date) AS max_date
                    FROM
                        account_move_line l
                        RIGHT JOIN account_account a ON (a.id = l.account_id)
                        RIGHT JOIN account_account_type at ON (at.id = a.user_type_id)
                        {2}
                    WHERE
                        a.reconcile IS TRUE
                        AND l.full_reconcile_id is NULL
                        {3}
                        {4}
                        {5}
                        AND l.company_id = {6}
                        AND (              -- This part is edited by Odootech
                            EXISTS (
                                SELECT NULL
                                FROM account_move_line l
                                WHERE l.account_id = a.id
                                {7}
                                AND l.amount_residual > 0
                            )
                            OR EXISTS (    -- This part is edited by Odootech
                                SELECT NULL
                                FROM account_move_line l
                                WHERE l.account_id = a.id
                                {7}
                                AND l.amount_residual < 0
                            )
                        )                  -- This part is changed by Odootech
                    GROUP BY {8} a.id, a.name, a.code, {res_alias}.last_time_entries_checked
                    ORDER BY {res_alias}.last_time_entries_checked
                ) as s
            WHERE (last_time_entries_checked IS NULL OR max_date > last_time_entries_checked)
        """.format(
            is_partner and 'partner_id, partner_name,' or ' ',
            is_partner and 'p.id AS partner_id, p.name AS partner_name,' or ' ',
            is_partner and 'RIGHT JOIN res_partner p ON (l.partner_id = p.id)' or ' ',
            is_partner and ' ' or "AND at.type <> 'payable' AND at.type <> 'receivable'",
            account_type and "AND at.type = %(account_type)s" or '',
            res_ids and 'AND ' + res_alias + '.id in %(res_ids)s' or '',
            self.env.user.company_id.id,
            is_partner and 'AND l.partner_id = p.id' or ' ',
            is_partner and 'l.partner_id, p.id,' or ' ',
            res_alias=res_alias
        ))
        # End - Edited by Odootech ---------------------------------------------

        self.env.cr.execute(query, locals())

        # Apply ir_rules by filtering out
        rows = self.env.cr.dictfetchall()
        ids = [x['account_id'] for x in rows]
        allowed_ids = set(self.env['account.account'].browse(ids).ids)
        rows = [row for row in rows if row['account_id'] in allowed_ids]
        if is_partner:
            ids = [x['partner_id'] for x in rows]
            allowed_ids = set(self.env['res.partner'].browse(ids).ids)
            rows = [row for row in rows if row['partner_id'] in allowed_ids]

        # Fetch other data
        for row in rows:
            account = self.env['account.account'].browse(row['account_id'])
            row['currency_id'] = account.currency_id.id or account.company_id.currency_id.id
            partner_id = is_partner and row['partner_id'] or None
            row['reconciliation_proposition'] = self.get_reconciliation_proposition(
                account.id, partner_id)
        return rows
