# -*- coding: utf-8 -*-

import logging
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger("__name__")


class PeriodMonth(models.Model):
    _name = 'period.month'
    _rec_name = 'months_number'

    name = fields.Char(string='Months')
    months_number = fields.Char(string='Number')


class PeriodYear(models.Model):
    _name = 'period.year'

    name = fields.Char(string='year')


class MuniWhConcept(models.Model):
    _name = 'muni.wh.concept'

    name = fields.Char(string="Description", required=True)
    code = fields.Char(string='Activity code', required=True)
    aliquot = fields.Float(string='Aliquot', required=True)
    month_ucim = fields.Char(string='UCIM per month')
    year_ucim = fields.Char(string='UCIM per year')



class MunicipalityTaxLine(models.Model):
    _name = 'municipality.tax.line'

    concept_id = fields.Many2one('muni.wh.concept', string="Retention concept", Copy=False)
    code = fields.Char(string='Activity code', compute='_compute_code')
    aliquot = fields.Float(string='Aliquot', compute='_compute_aliquota')
    base_tax = fields.Float(string='Base Tax')
    wh_amount = fields.Float(compute="_compute_wh_amount", string='Withholding Amount', store=True)
    move_typee = fields.Selection(selection=[('purchase', 'Purchase'), ('service', 'Service'), ('dont_apply','Does not apply')],string='Type of transaction')
    municipality_tax_id = fields.Many2one('municipality.tax', string='Municipality')
    move_id = fields.Many2one(string='Account entry')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_date = fields.Date(string="Invoice Date")
    invoice_number = fields.Char(string="Invoice Number",compute='_compute_invoice_number')
    invoice_ctrl_number = fields.Char(string="Invoice Control Number", compute='_compute_invoice_number_control')

    @api.depends('invoice_id')
    def _compute_invoice_number(self):
        for selff in self:
            selff.invoice_number=selff.invoice_id.invoice_number_next

    @api.depends('invoice_id')
    def _compute_invoice_number_control(self):
        for selff in self:
            selff.invoice_ctrl_number=selff.invoice_id.invoice_number_control

    @api.depends('concept_id')
    def _compute_aliquota(self):
        for selff in self:
            selff.aliquot=selff.concept_id.aliquot


    @api.depends('concept_id')
    def _compute_code(self):
        for selff in self:
            selff.code=selff.concept_id.code

    @api.depends('base_tax', 'aliquot')
    def _compute_wh_amount(self):
        withheld_amount=0
        amount=0
        for item in self:        
            retention = ((item.base_tax * item.aliquot) / 100)
            item.wh_amount = retention
            withheld_amount = withheld_amount+item.base_tax # correccion darrell se transformo en acumulador
            amount = amount+item.wh_amount # correccion darrell se transformo en acumulador
            if item.municipality_tax_id:
                item.municipality_tax_id.write({'withheld_amount': withheld_amount, 'amount': amount})

    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result


class MUnicipalityTax(models.Model):
    _name = 'municipality.tax'

   
    name = fields.Char(string='Voucher number', default='00000000')
    state = fields.Selection(selection=[
            ('draft', 'Borrador'),
            ('posted', 'Publicado'),
            ('cancel', 'Cancelado')
        ], string='Status', readonly=True, copy=False, tracking=True,
        default='draft')
    transaction_date = fields.Date(string='Transacción Date', default=datetime.now())
    #period fields
    date_start = fields.Many2one('period.month', string='Date start')
    date_end = fields.Many2one('period.year', string='Date end')
    rif = fields.Char(string='RIF')
    #rif = fields.Char(related='invoice_id.rif',string='RIF')
    # address
    address = fields.Char(string='Dirección')
    # partner data
    partner_id = fields.Many2one('res.partner', string='Partner')
    act_code_ids = fields.One2many('municipality.tax.line', 'municipality_tax_id', string='Activities code')
    # campos de ubicacion politico territorial
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State', tracking=True)
    municipality_id = fields.Many2one('res.country.state.municipality', string='Municipality')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    amount = fields.Float(string='Amount', compute='_compute_amount')
    withheld_amount = fields.Float(string='Withheld Amount', compute='_compute_withheld_amount')
    move_type = fields.Selection(selection=[
        ('out_invoice', 'Factura cliente'),
        ('in_invoice','Factura Proveedor'),
        ('in_refund','Suplier Refund'),
        ('out_refund','Customer Refund'),
        ('in_receipt','Nota Debito cliente'),
        ('out_receipt','Nota Debito proveedor'),
        ('na','N/A'),
        ], string="Type invoice", store=True, default='na')
    
    # We need this field for the reports
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    move_id = fields.Many2one('account.move', string='Id del movimiento')
    invoice_number=fields.Char(string='Nro de Factura')
    asiento_ret_id=fields.Many2one('account.move')

    def _compute_amount(self):
        acom1=0
        for det in self.act_code_ids:
            acom1=acom1+det.wh_amount
        self.amount=acom1

    def _compute_withheld_amount(self):
        acom2=0
        for det in self.act_code_ids:
            acom2=acom2+det.base_tax
        self.withheld_amount=acom2

    @api.onchange('invoice_id')
    def move_types(self):
        for selff in self:
            if selff.invoice_id:
                selff.move_type=selff.invoice_id.move_type
                selff.invoice_number=selff.invoice_id.invoice_number_next


    def get_name(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_ve_cuenta_retencion_iva'''

        self.ensure_one()
        SEQUENCE_CODE = 'l10n_ve_cuenta_retencion_municipal'
        company_id = self.env.company.id
        IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': 'RET_MUN/',
                'name': 'Localización Venezolana Retenciones Municipales %s' % self.env.company.name,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': company_id,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name


    def consecutivo_name(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_ve_cuenta_retencion_iva'''

        self.ensure_one()
        SEQUENCE_CODE = 'l10n_ve_consecutivo_retencion_municipal'
        company_id = self.env.company.id
        IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': '',
                'name': 'Localización Venezolana consecutivo Retenciones Municipales %s' % self.env.company.name,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': company_id,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    def action_draft(self):
        self.state='draft'
        if self.asiento_ret_id.state=='posted':
            self.asiento_ret_id.button_draft()
        if self.asiento_ret_id:
            self.asiento_ret_id.with_context(force_delete=True).unlink()




    def action_post(self):
        if not self.transaction_date:
            raise ValidationError("Debe establecer una fecha de Transacción")
        self.state='posted'
        nombre_ret_municipal = self.get_name()
        if self.name=='00000000' or not self.name:
            self.name=self.consecutivo_name()
        id_move=self.registro_movimiento_retencion_mun(nombre_ret_municipal)
        idv_move=id_move.id
        valor=self.registro_movimiento_linea_retencion_mun(idv_move,nombre_ret_municipal)
        moves= self.env['account.move'].search([('id','=',idv_move)])
        ###moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
        self.asiento_ret_id=moves.id
        moves._post(soft=False)

    def registro_movimiento_retencion_mun(self,consecutivo_asiento):
        name = consecutivo_asiento
        signed_amount_total=0
        #raise UserError(_('self.move_id.name = %s')%self.invoice_id.name)
        if self.move_type=="in_invoice":
            signed_amount_total=self.amount #self.conv_div_extranjera(self.amount)
        if self.move_type=="out_invoice":
            signed_amount_total=-1*self.amount #(-1*self.conv_div_extranjera(self.amount))

        if self.move_type=="out_invoice" or self.move_type=="out_refund" or self.move_type=="out_receipt":
            id_journal=self.partner_id.diario_jrl_id.id
        if self.move_type=="in_invoice" or self.move_type=="in_refund" or self.move_type=="in_receipt":
            id_journal=self.partner_id.diario_jrl_id.id
            """if self.company_id.confg_ret_proveedores=="c":
                id_journal=self.company_id.partner_id.diario_jrl_id.id
            if self.company_id.confg_ret_proveedores=="p":
                id_journal=self.partner_id.diario_jrl_id.id"""

        value = {
            'name': name,
            'date': self.transaction_date,#listo
            #'amount_total':self.vat_retentioned,# LISTO
            'partner_id': self.partner_id.id, #LISTO
            'journal_id':id_journal,
            'ref': "Retencion del Impuesto Municipal de la Factura %s" % (self.invoice_id.name),
            #'amount_total':self.vat_retentioned,# LISTO
            #'amount_total_signed':signed_amount_total,# LISTO
            'move_type': "entry",# estte campo es el que te deja cambiar y almacenar valores
            #'type':"entry",
            'wh_muni_id': self.id,
        }
        move_obj = self.env['account.move']
        move_id = move_obj.create(value)    
        return move_id


    def registro_movimiento_linea_retencion_mun(self,id_movv,consecutivo_asiento):
        name = consecutivo_asiento
        valores = self.amount #self.conv_div_extranjera(self.amount) #VALIDAR CONDICION
        cero = 0.0
        if self.move_type=="out_invoice" or self.move_type=="out_refund" or self.move_type=="out_receipt":
            cuenta_ret_cliente=self.partner_id.account_ret_muni_receivable_id.id# cuenta retencion cliente
            cuenta_ret_proveedor=self.partner_id.account_ret_muni_payable_id.id#cuenta retencion proveedores
            cuenta_clien_cobrar=self.partner_id.property_account_receivable_id.id
            cuenta_prove_pagar = self.partner_id.property_account_payable_id.id

        if self.move_type=="in_invoice" or self.move_type=="in_refund" or self.move_type=="in_receipt":
            """if self.company_id.confg_ret_proveedores=="c":
                cuenta_ret_cliente=self.company_id.partner_id.account_ret_muni_receivable_id.id# cuenta retencion cliente
                cuenta_ret_proveedor=self.company_id.partner_id.account_ret_muni_payable_id.id#cuenta retencion proveedores
                cuenta_clien_cobrar=self.company_id.partner_id.property_account_receivable_id.id
                cuenta_prove_pagar = self.company_id.partner_id.property_account_payable_id.id"""
            #if self.company_id.confg_ret_proveedores=="p":
            cuenta_ret_cliente=self.partner_id.account_ret_muni_receivable_id.id# cuenta retencion cliente
            cuenta_ret_proveedor=self.partner_id.account_ret_muni_payable_id.id#cuenta retencion proveedores
            cuenta_clien_cobrar=self.partner_id.property_account_receivable_id.id
            cuenta_prove_pagar = self.partner_id.property_account_payable_id.id

        tipo_empresa=self.move_type
        #raise UserError(_('darrell = %s')%tipo_empresa)
        if tipo_empresa=="in_invoice" or tipo_empresa=="in_receipt":#aqui si la empresa es un proveedor
            cuenta_haber=cuenta_ret_proveedor
            cuenta_debe=cuenta_prove_pagar
            #raise UserError(_(' pantalla 1'))
            #raise UserError(_('cuentas = %s')%cuenta_debe)

        if tipo_empresa=="in_refund":
            cuenta_haber=cuenta_prove_pagar
            cuenta_debe=cuenta_ret_proveedor
            #raise UserError(_(' pantalla 2'))

        if tipo_empresa=="out_invoice" or tipo_empresa=="out_receipt":# aqui si la empresa es cliente
            cuenta_haber=cuenta_clien_cobrar
            cuenta_debe=cuenta_ret_cliente
            #raise UserError(_(' pantalla 3'))

        if tipo_empresa=="out_refund":
            cuenta_haber=cuenta_ret_cliente
            cuenta_debe=cuenta_clien_cobrar
            #raise UserError(_(' pantalla 4'))
        balances=cero-valores
        #raise UserError(_('cuenta = %s')%cuenta_ret_cliente)
        value = {
             'name': name,
             'ref' : "Retencion Impuesto Municipal de la Factura %s" % (self.invoice_id.name),
             'move_id': int(id_movv),
             'date': self.transaction_date,
             'partner_id': self.partner_id.id,
             'account_id': cuenta_haber,
             #'amount_currency': 0.0,
             #'date_maturity': False,
             'credit': valores,
             'debit': 0.0, # aqi va cero   EL DEBITO CUNDO TIENE VALOR, ES QUE EN ACCOUNT_MOVE TOMA UN VALOR
             'balance':-valores, # signo negativo
             'price_unit':balances,
             'price_subtotal':balances,
             'price_total':balances,

        }
        move_line_obj = self.env['account.move.line']
        move_line_id1 = move_line_obj.create(value)

        balances=valores-cero
        value['account_id'] = cuenta_debe
        value['credit'] = 0.0 # aqui va cero
        value['debit'] = valores
        value['balance'] = valores
        value['price_unit'] = balances
        value['price_subtotal'] = balances
        value['price_total'] = balances


        move_line_id2 = move_line_obj.create(value)

    
    def comprobante(self):
        return self.env.ref('municipal_retention.action_report_retencion_muni').report_action(self)

    def float_format2(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result
