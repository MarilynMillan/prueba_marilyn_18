# -*- coding: utf-8 -*-
# Libro mayor de empresas

import json

from odoo import models, _, fields
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, get_lang

from datetime import timedelta
from collections import defaultdict

class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'


    def _query_partners(self, options):
        """ Executes the queries and performs all the computation.
        :return:        A list of tuple (partner, column_group_values) sorted by the table's model _order:
                        - partner is a res.parter record.
                        - column_group_values is a dict(column_group_key, fetched_values), where
                            - column_group_key is a string identifying a column group, like in options['column_groups']
                            - fetched_values is a dictionary containing:
                                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        """
        def assign_sum(row):
            fields_to_assign = ['balance', 'debit', 'credit']
            if any(row[field] is not None and not company_currency.is_zero(row[field]) for field in fields_to_assign):
                groupby_partners.setdefault(row['groupby'], defaultdict(lambda: defaultdict(float)))
                for field in fields_to_assign:
                    groupby_partners[row['groupby']][row['column_group_key']][field] += (row[field] or 0.0)

        company_currency = self.env.company.currency_id

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options)

        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            assign_sum(res)

        # Correct the sums per partner, for the lines without partner reconciled with a line having a partner
        query, params = self._get_sums_without_partner(options)

        self._cr.execute(query, params)
        totals = {}
        for total_field in ['debit', 'credit', 'balance']:
            totals[total_field] = {col_group_key: 0 for col_group_key in options['column_groups']}

        for row in self._cr.dictfetchall():
            totals['debit'][row['column_group_key']] += row['debit']
            totals['credit'][row['column_group_key']] += row['credit']
            totals['balance'][row['column_group_key']] += row['balance']

            if row['groupby'] not in groupby_partners:
                continue

            assign_sum(row)

        if None in groupby_partners:
            # Debit/credit are inverted for the unknown partner as the computation is made regarding the balance of the known partner
            for column_group_key in options['column_groups']:
                groupby_partners[None][column_group_key]['debit'] += totals['credit'][column_group_key]
                groupby_partners[None][column_group_key]['credit'] += totals['debit'][column_group_key]
                groupby_partners[None][column_group_key]['balance'] -= totals['balance'][column_group_key]

        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        if groupby_partners:
            # Note a search is done instead of a browse to preserve the table ordering.
            partners = self.env['res.partner'].with_context(active_test=False).search_fetch([('id', 'in', list(groupby_partners.keys()))], ["id", "name", "trust", "company_registry", "vat"])
        else:
            partners = []

        # Add 'Partner Unknown' if needed
        if None in groupby_partners.keys():
            partners = [p for p in partners] + [None]

        return [(partner, groupby_partners[partner.id if partner else None]) for partner in partners]


        

    def _get_initial_balance_values(self, partner_ids, options):
        ################# codigo darrell ###################
        lista=self.env['account.move.line'].search([('conv_credit_debit_balanc','=','no')])
        if lista:
            for rec in lista:
                rec. update_usd()  # codigo darrell
        lista2=self.env['account.move'].search([('amount_residual','!=',0)])
        if lista2:
            for roc in lista2:
                roc.amount_residual_usd=roc.amount_residual
        ################# fin codigo darrell ###################
        queries = []
        params = []
        report = self.env.ref('account_reports.partner_ledger_report')
        ct_query = report._get_query_currency_table(options)
        currency_dif = options['currency_dif'] if 'currency_dif' in options else self.env.company.currency_id.symbol
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            # Get sums for the initial balance.
            # period: [('date' <= options['date_from'] - 1)]
            new_options = self._get_options_initial_balance(column_group_options)
            tables, where_clause, where_params = report._query_get(new_options, 'normal',
                                                                   domain=[('partner_id', 'in', partner_ids)])
            params.append(column_group_key)
            params += where_params
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(f"""
                    SELECT
                        account_move_line.partner_id,
                        %s                                                                                    AS column_group_key,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance
                    FROM {tables}
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    WHERE {where_clause}
                    GROUP BY account_move_line.partner_id
                """)
            else:
                queries.append(f"""
                                    SELECT
                                        account_move_line.partner_id,
                                        %s                                                                                    AS column_group_key,
                                        SUM(ROUND(account_move_line.debit_usd, currency_table.precision))   AS debit,
                                        SUM(ROUND(account_move_line.credit_usd, currency_table.precision))  AS credit,
                                        SUM(ROUND(account_move_line.balance_usd, currency_table.precision)) AS balance
                                    FROM {tables}
                                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                                    WHERE {where_clause}
                                    GROUP BY account_move_line.partner_id
                                """)

        self._cr.execute(" UNION ALL ".join(queries), params)

        init_balance_by_col_group = {
            partner_id: {column_group_key: {} for column_group_key in options['column_groups']}
            for partner_id in partner_ids
        }
        for result in self._cr.dictfetchall():
            init_balance_by_col_group[result['partner_id']][result['column_group_key']] = result

        return init_balance_by_col_group

    def _get_query_sums(self, options):
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all partners.
        - sums for the initial balances.
        :param options:             The report options.
        :return:                    (query, params)
        """
        params = []
        queries = []
        report = self.env.ref('account_reports.partner_ledger_report')
        currency_dif = options['currency_dif'] if 'currency_dif' in options else self.env.company.currency_id.symbol
        # Create the currency table.
        ct_query = report._get_query_currency_table(options)
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(column_group_options, 'normal')
            params.append(column_group_key)
            params += where_params
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(f"""
                    SELECT
                        account_move_line.partner_id                                                          AS groupby,
                        %s                                                                                    AS column_group_key,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance
                    FROM {tables}
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    WHERE {where_clause}
                    GROUP BY account_move_line.partner_id
                """)
            else:
                queries.append(f"""
                                    SELECT
                                        account_move_line.partner_id                                                          AS groupby,
                                        %s                                                                                    AS column_group_key,
                                        SUM(ROUND(account_move_line.debit_usd, currency_table.precision))   AS debit,
                                        SUM(ROUND(account_move_line.credit_usd, currency_table.precision))  AS credit,
                                        SUM(ROUND(account_move_line.balance_usd, currency_table.precision)) AS balance
                                    FROM {tables}
                                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                                    WHERE {where_clause}
                                    GROUP BY account_move_line.partner_id
                                """)

        return ' UNION ALL '.join(queries), params


    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = {partner_id: [] for partner_id in partner_ids}
        currency_dif = options['currency_dif'] if 'currency_dif' in options else self.env.company.currency_id.symbol
        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        directly_linked_aml_partner_params = []
        indirectly_linked_aml_partner_params = []
        indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IS NOT NULL'
        if None in partner_ids:
            directly_linked_aml_partner_clauses.append('account_move_line.partner_id IS NULL')
        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append('account_move_line.partner_id IN %s')
            directly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
            indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IN %s'
            indirectly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
        directly_linked_aml_partner_clause = '(' + ' OR '.join(directly_linked_aml_partner_clauses) + ')'

        ct_query = self.env['account.report']._get_query_currency_table(options)
        queries = []
        all_params = []
        lang = self.env.lang or get_lang(self.env).code
        journal_name = f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')" if \
            self.pool['account.journal'].name.translate else 'journal.name'
        account_name = f"COALESCE(account.name->>'{lang}', account.name->>'en_US')" if \
            self.pool['account.account'].name.translate else 'account.name'
        report = self.env.ref('account_reports.partner_ledger_report')
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(group_options, 'strict_range')

            all_params += [
                column_group_key,
                *where_params,
                *directly_linked_aml_partner_params,
                column_group_key,
                *indirectly_linked_aml_partner_params,
                *where_params,
                group_options['date']['date_from'],
                group_options['date']['date_to'],
            ]

            # For the move lines directly linked to this partner
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(f'''
                    SELECT
                        account_move_line.id,
                        account_move_line.date_maturity,
                        account_move_line.name,
                        account_move_line.ref,
                        account_move_line.company_id,
                        account_move_line.account_id,
                        account_move_line.payment_id,
                        account_move_line.partner_id,
                        account_move_line.currency_id,
                        account_move_line.amount_currency,
                        account_move_line.matching_number,
                        COALESCE(account_move_line.invoice_date, account_move_line.date)                 AS invoice_date,
                        ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                        ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                        ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                        account_move.name                                                                AS move_name,
                        account_move.move_type                                                           AS move_type,
                        account.code                                                                     AS account_code,
                        {account_name}                                                                   AS account_name,
                        journal.code                                                                     AS journal_code,
                        {journal_name}                                                                   AS journal_name,
                        %s                                                                               AS column_group_key,
                        'directly_linked_aml'                                                            AS key,
                        0                                                                                AS partial_id
                    FROM {tables}
                    JOIN account_move ON account_move.id = account_move_line.move_id
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                    LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                    LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                    LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                    WHERE {where_clause} AND {directly_linked_aml_partner_clause}
                    ORDER BY account_move_line.date, account_move_line.id
                ''')

                # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
                queries.append(f'''
                    SELECT
                        account_move_line.id,
                        account_move_line.date_maturity,
                        account_move_line.name,
                        account_move_line.ref,
                        account_move_line.company_id,
                        account_move_line.account_id,
                        account_move_line.payment_id,
                        aml_with_partner.partner_id,
                        account_move_line.currency_id,
                        account_move_line.amount_currency,
                        account_move_line.matching_number,
                        COALESCE(account_move_line.invoice_date, account_move_line.date)                    AS invoice_date,
                        CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE ROUND(
                            partial.amount * currency_table.rate, currency_table.precision
                        ) END                                                                               AS debit,
                        CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE ROUND(
                            partial.amount * currency_table.rate, currency_table.precision
                        ) END                                                                               AS credit,
                        - sign(aml_with_partner.balance) * ROUND(
                            partial.amount * currency_table.rate, currency_table.precision
                        )                                                                                   AS balance,
                        account_move.name                                                                   AS move_name,
                        account_move.move_type                                                              AS move_type,
                        account.code                                                                        AS account_code,
                        {account_name}                                                                      AS account_name,
                        journal.code                                                                        AS journal_code,
                        {journal_name}                                                                      AS journal_name,
                        %s                                                                                  AS column_group_key,
                        'indirectly_linked_aml'                                                             AS key,
                        partial.id                                                                          AS partial_id
                    FROM {tables}
                        LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id,
                        account_partial_reconcile partial,
                        account_move,
                        account_move_line aml_with_partner,
                        account_journal journal,
                        account_account account
                    WHERE
                        (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
                        AND account_move_line.partner_id IS NULL
                        AND account_move.id = account_move_line.move_id
                        AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                        AND {indirectly_linked_aml_partner_clause}
                        AND journal.id = account_move_line.journal_id
                        AND account.id = account_move_line.account_id
                        AND {where_clause}
                        AND partial.max_date BETWEEN %s AND %s
                    ORDER BY account_move_line.date, account_move_line.id
                ''')
            else:
                queries.append(f'''
                                    SELECT
                                        account_move_line.id,
                                        account_move_line.date_maturity,
                                        account_move_line.name,
                                        account_move_line.ref,
                                        account_move_line.company_id,
                                        account_move_line.account_id,
                                        account_move_line.payment_id,
                                        account_move_line.partner_id,
                                        account_move_line.currency_id,
                                        account_move_line.amount_currency,
                                        account_move_line.matching_number,
                                        COALESCE(account_move_line.invoice_date, account_move_line.date)                 AS invoice_date,
                                        ROUND(account_move_line.debit_usd, currency_table.precision)   AS debit,
                                        ROUND(account_move_line.credit_usd, currency_table.precision)  AS credit,
                                        ROUND(account_move_line.balance_usd, currency_table.precision) AS balance,
                                        account_move.name                                                                AS move_name,
                                        account_move.move_type                                                           AS move_type,
                                        account.code                                                                     AS account_code,
                                        {account_name}                                                                   AS account_name,
                                        journal.code                                                                     AS journal_code,
                                        {journal_name}                                                                   AS journal_name,
                                        %s                                                                               AS column_group_key,
                                        'directly_linked_aml'                                                            AS key,
                                        0                                                                                AS partial_id
                                    FROM {tables}
                                    JOIN account_move ON account_move.id = account_move_line.move_id
                                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                                    LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                                    LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                                    LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                                    LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                                    WHERE {where_clause} AND {directly_linked_aml_partner_clause}
                                    ORDER BY account_move_line.date, account_move_line.id
                                ''')

                # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
                queries.append(f'''
                                    SELECT
                                        account_move_line.id,
                                        account_move_line.date_maturity,
                                        account_move_line.name,
                                        account_move_line.ref,
                                        account_move_line.company_id,
                                        account_move_line.account_id,
                                        account_move_line.payment_id,
                                        aml_with_partner.partner_id,
                                        account_move_line.currency_id,
                                        account_move_line.amount_currency,
                                        account_move_line.matching_number,
                                        COALESCE(account_move_line.invoice_date, account_move_line.date)                    AS invoice_date,
                                        CASE WHEN aml_with_partner.balance_usd > 0 THEN 0 ELSE ROUND(
                                            partial.amount_usd, currency_table.precision
                                        ) END                                                                               AS debit,
                                        CASE WHEN aml_with_partner.balance_usd < 0 THEN 0 ELSE ROUND(
                                            partial.amount_usd, currency_table.precision
                                        ) END                                                                               AS credit,
                                        - sign(aml_with_partner.balance_usd) * ROUND(
                                            partial.amount_usd, currency_table.precision
                                        )                                                                                   AS balance,
                                        account_move.name                                                                   AS move_name,
                                        account_move.move_type                                                              AS move_type,
                                        account.code                                                                        AS account_code,
                                        {account_name}                                                                      AS account_name,
                                        journal.code                                                                        AS journal_code,
                                        {journal_name}                                                                      AS journal_name,
                                        %s                                                                                  AS column_group_key,
                                        'indirectly_linked_aml'                                                             AS key,
                                        partial.id                                                                          AS partial_id
                                    FROM {tables}
                                        LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id,
                                        account_partial_reconcile partial,
                                        account_move,
                                        account_move_line aml_with_partner,
                                        account_journal journal,
                                        account_account account
                                    WHERE
                                        (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
                                        AND account_move_line.partner_id IS NULL
                                        AND account_move.id = account_move_line.move_id
                                        AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                                        AND {indirectly_linked_aml_partner_clause}
                                        AND journal.id = account_move_line.journal_id
                                        AND account.id = account_move_line.account_id
                                        AND {where_clause}
                                        AND partial.max_date BETWEEN %s AND %s
                                    ORDER BY account_move_line.date, account_move_line.id
                                ''')


        query = '(' + ') UNION ALL ('.join(queries) + ')'

        if offset:
            query += ' OFFSET %s '
            all_params.append(offset)

        if limit:
            query += ' LIMIT %s '
            all_params.append(limit)

        self._cr.execute(query, all_params)
        for aml_result in self._cr.dictfetchall():
            if aml_result['key'] == 'indirectly_linked_aml':

                # Append the line to the partner found through the reconciliation.
                if aml_result['partner_id'] in rslt:
                    rslt[aml_result['partner_id']].append(aml_result)

                # Balance it with an additional line in the Unknown Partner section but having reversed amounts.
                if None in rslt:
                    rslt[None].append({
                        **aml_result,
                        'debit': aml_result['credit'],
                        'credit': aml_result['debit'],
                        'balance': -aml_result['balance'],
                    })
            else:
                rslt[aml_result['partner_id']].append(aml_result)

        return rslt


