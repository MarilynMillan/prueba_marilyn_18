# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils
from odoo.tools.misc import formatLang, format_date
from contextlib import ExitStack, contextmanager

from datetime import date, timedelta, datetime
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

from odoo.tools import (
    date_utils,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    index_exists,
    is_html_empty,
)

import ast
import json
import re
import warnings
import pytz

#forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')
#_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_number_next = fields.Char(string='Nro Invoice', copy=False, tracking=True)
    invoice_number_control = fields.Char(string='Nro Control', copy=False, tracking=True)
    invoice_number_unique = fields.Char(string='Nro Control Unique', copy=False, tracking=True)
    delivery_note_next_number = fields.Char(string='Nro. Nota de Entrega',tracking=True)
    is_delivery_note = fields.Boolean(default=False, tracking=True)
    is_manual = fields.Boolean(string='Numeracion Manual', tracking=True)
    hide_book = fields.Boolean(string='Excluir de Libros', tracking=True, default=False)
    reason = fields.Char('Referencia de Factura')
    tasa = fields.Float(compute='_compute_tasa',store=True, readonly=False,digits=(12, 4))
    hora_public = fields.Char()
    #is_branch_office = fields.Boolean(string='Tiene sucursal', tracking=True)
    nro_planilla_exportacion = fields.Char()
    image = fields.Binary(string='imagen', store=True, attachment=True)
    file_name = fields.Char('Filename')

    nro_form_impor = fields.Char()
    nro_expe_impor = fields.Char()
    operation_type = fields.Selection([
        ('national','Nacional'),
        ('international','Internacional'),
    ],default='national')
    price_ref_div_product=fields.Boolean(string='Usar precio indexado USD del producto?',default=lambda self: self.env.company.price_ref_div_product,help='Este campo si es verdadero, usa el precio de venta fijado en divisa y lo lleva a Bs según la tasa Fijada')
    #price_ref_div_product=fields.Boolean(string='Usar precio indexado USD del producto?',default=False,help='Este campo si es verdadero, usa el precio de venta fijado en divisa y lo lleva a Bs según la tasa Fijada')
    amount_total_signed_div = fields.Float(compute='_compute_total_div')
    amount_untaxed_loc_ve = fields.Monetary(compute='_compute_amunt_untaxed_ve')
    ########################### para la vista del igtf #############
    cond_fact = fields.Selection([('cont','Contado'),('cred','Credito')],default="cred")
    amount_base_imponible=fields.Monetary(compute='_compute_base_imponible')
    amount_exento=fields.Monetary(compute='_compute_exemto')
    amount_igtf = fields.Monetary(compute='_compute_igtf')
    amount_igtf_signed = fields.Float()
    igtf_ids=fields.One2many('account.payment.fact','move_id', string='Cobros IGTF')
    amount_total_aux = fields.Float(compute='_compute_total_aux')
    observacion = fields.Char()
    fact_afect = fields.Char()

    #show_update_fpos = fields.Boolean(string="Has Fiscal Position Changed", store=False)  

    def _compute_amunt_untaxed_ve(self):
        for selff in self:
            selff.amount_untaxed_loc_ve=abs(selff.amount_base_imponible+selff.amount_exento)


    def _compute_base_imponible(self):
        total_imponible=0
        for det in self.invoice_line_ids:
            if det.tax_ids.aliquot!='exempt':
                total_imponible=total_imponible+det.price_subtotal
        self.amount_base_imponible=total_imponible
#aqui
    def _compute_exemto(self):
        total_exento=0
        for det in self.invoice_line_ids:
            if det.tax_ids.aliquot=='exempt' and det.linea_exenta!=True:
                total_exento=total_exento+det.price_subtotal
        self.amount_exento=total_exento

    def _compute_igtf(self):
        valor=0
        if self.igtf_ids:
            for item in self.igtf_ids:
                valor=valor+item.monto_ret_bs
        if self.company_id.currency_id.id!=self.currency_id.id:
            valor=valor/self.tasa
        self.amount_igtf=valor

    def _compute_total_aux(self):
        self.amount_total_aux=self.amount_total+self.amount_igtf

    def pago_prog(self):
        return self.env['wizard.payment.fact']\
            .with_context(active_ids=self.ids, active_model='account.move', active_id=self.id)\
            .action_register_ext_payment()




    def _compute_total_div(self):
        for selff in self:
            selff.amount_total_signed_div=selff.amount_total_signed/selff.tasa if selff.tasa!=0 else selff.amount_total_signed

    @api.onchange('partner_id')
    def function_operation_type(self):
        for selff in self:
            selff.operation_type=selff.partner_id.partner_type

    @api.depends('invoice_date','date')
    @api.onchange('invoice_date','date')
    def _compute_tasa(self):
        result=1
        for selff in self:
            if selff.invoice_date:
                lista=selff.env['res.currency.rate'].search([('currency_id','=',selff.company_id.currency_sec_id.id),('name','<=',selff.invoice_date)],order='name desc',limit=1)
            else:
                lista=selff.env['res.currency.rate'].search([('currency_id','=',selff.company_id.currency_sec_id.id),('name','<=',selff.date)],order='name desc',limit=1)
            if lista:
                result=lista.inverse_company_rate
            selff.tasa=result

    @api.onchange('journal_id')
    def function_nota_entrega(self):
        if self.journal_id.nota_entrega==True:
            self.is_delivery_note=True
            self.hide_book=True
        else:
            self.is_delivery_note=False
            self.hide_book=False

    @api.onchange('move_type')
    def _onchange_default_manual(self):
        if self.move_type in ['in_invoice', 'in_refund']:
            self.is_manual = True

    def action_post(self):
        for selff in self:
            if selff.move_type!='entry':
                selff.inserta_igtf()
            res=super().action_post()
            if selff.move_type!='entry':
                selff.valida_pagos_progra()
                selff.asig_nro_fact_control()
            selff.hora_public=  self.get_local_time()  #datetime.now().strftime('%H-4:%M:%S')   #datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            #raise UserError(_('move xx = %s ')%self)
            return res

    def get_local_time(self):

        # Obtener la hora actual en UTC y convertirla a la zona horaria local

        utc_now = datetime.now(pytz.utc)

        local_tz = pytz.timezone('America/Caracas') # Cambia esto a tu zona horaria

        local_time = utc_now.astimezone(local_tz)

        return local_time.strftime('%H:%M:%S') # Solo la hora


    def inserta_igtf(self):
        if self.amount_igtf!=0:
            if self.move_type in ('out_invoice','out_receipt','out_refund'):
                type_tax_use='sale'
            if self.move_type in ('in_invoice','in_receipt','in_refund'):
                type_tax_use='purchase'
            tax_ids=self.env['account.tax'].search([('aliquot','=','exempt'),('type_tax_use','=',type_tax_use),('company_id','=',self.company_id.id)],limit=1)
            if self.amount_igtf!=0:
                if not self.env.company.account_igtf_id.id:
                    raise UserError(_('No hay una cuanta contable para el igtf. Vaya a compañia y asigne una.'))
                vals=({
                    'name':"Registro de IGTF",
                    'quantity':1,
                    'price_unit':self.amount_igtf,
                    'tax_ids':tax_ids if tax_ids else '',
                    'move_id':self.id,
                    'account_id':self.env.company.account_igtf_id.id,
                    'linea_exenta':True,
                    })
                id_line2=self.invoice_line_ids.create(vals)

    def asig_nro_fact_control(self):
        if self.move_type!='entry':
            if self.is_delivery_note:
                if not self.delivery_note_next_number:
                    self.delivery_note_next_number = self.get_nro_nota_entrega()
                self.name=self.journal_id.code+ "/" + self.delivery_note_next_number
                self.payment_reference=self.journal_id.code+ "/" + self.delivery_note_next_number
            else:
                self.invoice_number_seq()
                self.invoice_control()
                if self.move_type in ('in_invoice','in_refund','in_receipt'):
                    # proveedor
                    pass
                    #self.name= self.name+'//'+str(self.invoice_number_next)
                    #self.name= self.invoice_number_next
                if self.move_type in ('out_invoice','out_refund','out_receipt'):
                    # cliente
                    self.name= self.journal_id.code + "/" +self.invoice_number_next
            for det_line_asiento in self.line_ids:
                if det_line_asiento.account_id.account_type in ('asset_receivable','liability_payable'):
                    det_line_asiento.name = self.journal_id.code + "/" + self.delivery_note_next_number if self.delivery_note_next_number else self.journal_id.code + "/" +self.invoice_number_next

    def valida_pagos_progra(self):
        if self.cond_fact=='cont':
            if not self.igtf_ids.search([('move_id','=',self.id)]):
                raise UserError(_('Debe registrar primero los métodos de pagos para esta factura a contado'))
            else:
                for det in self.igtf_ids.search([('move_id','=',self.id)]):
                    if self.move_type in ('out_invoice','out_receipt','in_refund'):
                        payment_type='inbound'
                        partner_type='customer'
                    if self.move_type in ('in_invoice','in_receipt','out_refund'):
                        payment_type='outbound'
                        partner_type='supplier'
                    vals=({
                        'partner_id':det.move_id.partner_id.id,
                        'currency_id':det.moneda.id,
                        'amount':det.monta_a_pagar,
                        'journal_id':det.account_journal_id.id,
                        'payment_method_line_id':det.account_payment_method_id.id,
                        'payment_type':payment_type,
                        'partner_type':partner_type,
                        'date':det.fecha,
                        })
                    id_payment=self.env['account.payment'].create(vals)
                    det.payment_id=id_payment
                    det.payment_id.action_post()
                    self.concilia_pago(id_payment) # habilitar despues
                    #raise UserError(_('xxxxx = %s ')%self)


    def concilia_pago(self, payment_id):
        factor = self.tasa
        monto = payment_id.amount
        move_pago_id = payment_id.move_id.id
        
        # 1. Determinar la cuenta contable según el tipo de movimiento
        cta_partner = False
        if self.move_type in ('out_invoice', 'in_receipt', 'in_refund'):
            cta_partner = self.partner_id.property_account_receivable_id.id
        elif self.move_type in ('in_invoice', 'out_receipt', 'out_refund'):
            cta_partner = self.partner_id.property_account_payable_id.id

        if not cta_partner:
            return # Si no hay cuenta, no se puede conciliar

        # 2. Buscar las líneas contables (Aseguramos obtener un registro único con .limit(1))
        move_line_pago_id = self.env['account.move.line'].search([
            ('move_id', '=', move_pago_id),
            ('account_id', '=', cta_partner),
            ('reconciled', '=', False) # Solo líneas no conciliadas
        ], limit=1)
        
        move_line_fact_id = self.env['account.move.line'].search([
            ('move_id', '=', self.id),
            ('account_id', '=', cta_partner),
            ('reconciled', '=', False)
        ], limit=1)

        # 3. VALIDACIÓN CRÍTICA: Si no encuentra alguna de las dos líneas, abortar
        if not move_line_pago_id or not move_line_fact_id:
            # Opcional: puedes poner un log aquí para saber por qué falló
            # print("No se encontró línea de pago o de factura para conciliar")
            return

        # 4. Lógica de montos y asignación de Débito/Crédito
        if self.move_type in ('out_invoice', 'in_receipt', 'out_refund'):
            debit_move_id = move_line_fact_id
            credit_move_id = move_line_pago_id
            credit_currency_id = payment_id.currency_id.id
            debit_currency_id = self.currency_id.id
            
            # Lógica de conversión (Simplificada para legibilidad)
            if self.currency_id != payment_id.currency_id:
                if payment_id.currency_id == self.company_id.currency_id: # Pago en Bs
                    monto_d = monto / factor if factor > 0 else monto
                    monto_c = monto
                else: # Pago en $
                    monto = payment_id.amount * factor
                    monto_d = payment_id.amount * factor
                    monto_c = payment_id.amount
            else:
                monto_d = payment_id.amount if payment_id.currency_id == self.company_id.currency_id else payment_id.amount
                monto_c = payment_id.amount
                if payment_id.currency_id != self.company_id.currency_id:
                    monto = payment_id.amount * factor

        else: # Proveedores (in_invoice, etc)
            debit_move_id = move_line_pago_id
            credit_move_id = move_line_fact_id
            credit_currency_id = self.currency_id.id
            debit_currency_id = payment_id.currency_id.id
            
            if self.currency_id != payment_id.currency_id:
                if payment_id.currency_id != self.company_id.currency_id: # Pago en $
                    monto = payment_id.amount * factor
                    monto_d = payment_id.amount
                    monto_c = payment_id.amount * factor
                else: # Pago en Bs
                    monto_d = monto
                    monto_c = monto / factor if factor > 0 else monto
            else:
                monto_d = payment_id.amount
                monto_c = payment_id.amount
                if payment_id.currency_id != self.company_id.currency_id:
                    monto = payment_id.amount * factor

        # 5. Creación del registro con datos validados
        vals = {
            'debit_move_id': debit_move_id.id,
            'credit_move_id': credit_move_id.id,
            'amount': monto,
            'debit_amount_currency': monto_d,
            'credit_amount_currency': monto_c,
            'credit_currency_id': credit_currency_id,
            'debit_currency_id': debit_currency_id,
            'max_date': max(debit_move_id.date, credit_move_id.date) # Forzamos la fecha para evitar el error
        }
        
        return self.env['account.partial.reconcile'].create(vals)



    def button_draft(self):
        for selff in self:
            super().button_draft()

            if (selff.env.user.x_llevar_borra_fact=='no' or not selff.env.user.x_llevar_borra_fact) and selff.move_type in ('out_invoice','out_refund','out_receipt'):
                raise UserError(_('Su Usuario no puede llevar esta factura a borrador'))
            if selff.env.user.x_llevar_borra_fact=='si' or selff.move_type not in ('out_invoice','out_refund','out_receipt'):
                if selff.igtf_ids:
                    for det in selff.igtf_ids.search([('move_id','=',selff.id)]):
                        if det.payment_id.state!='draft':
                            det.payment_id.action_draft()
                        det.payment_id.with_context(force_delete=True).unlink()
                busca=selff.invoice_line_ids.search([('linea_exenta','=',True),('move_id','=',selff.id)])
                #raise UserError(_('HHHH %s')%busca)
                if busca:
                    busca.unlink()


    def invoice_number_seq(self):
        if not self.is_manual:
            if self.move_type in ('out_invoice','out_refund','out_receipt','in_invoice','in_refund','in_receipt'):
                if not self.invoice_number_next or self.invoice_number_next==0:
                    #self.invoice_number_next=self.journal_id.code + "/" +self.get_invoice_nro_fact()
                    self.invoice_number_next=self.get_invoice_nro_fact()

    def get_invoice_nro_fact(self):
        name=''
        if not self.journal_id.doc_sequence_id:
            raise UserError(_('Este diario no tiene configurado el Nro de Documento. Vaya al diario, pestaña *Configuracion sec. Facturación* y en el campo *Proximo Nro Documento* agregue uno'))
        else:
            if not self.journal_id.doc_sequence_id.code:
                raise UserError(_('La secuencia del Nro documento llamado * %s * de este diario, no tiene configurada el Código se secuencias')%self.journal_id.doc_sequence_id.name)
            else:
                SEQUENCE_CODE=self.journal_id.doc_sequence_id.code
                company_id = self.company_id.id
                IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
                name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    def invoice_control(self):
        if not self.is_manual:
            if self.move_type in ('out_invoice','out_refund','out_receipt','in_invoice','in_refund','in_receipt'):
                if not self.invoice_number_control or self.invoice_number_control==0:
                    self.invoice_number_control=self.get_invoice_number_control()

    def get_invoice_number_control(self):
        name=''            
        if not self.journal_id.ctrl_sequence_id:
            raise UserError(_('Este diario no tiene configurado el Nro de control. vaya al diario, pestaña *Configuracion sec. Facturación* y en el campo *Proximo Nro control* agregue uno'))
        else:
            if not self.journal_id.ctrl_sequence_id.code:
                raise UserError(_('La secuencia del Nro control llamado * %s * de este diario, no tiene configurada el Código se secuencias')%self.journal_id.ctrl_sequence_id.name)
            else:
                SEQUENCE_CODE=self.journal_id.ctrl_sequence_id.code
                company_id = self.company_id.id
                IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
                name = IrSequence.next_by_code(SEQUENCE_CODE)

        return name

    def get_nro_nota_entrega(self):
        name=''
        if self.journal_id.nota_entrega!=True:
            raise UserError(_('Este diario no esta configurado para nota de entrega. Vaya al diario, pestaña *Configuracion sec. Facturación* y habilite el campo nota de entrega'))
        if not self.journal_id.doc_sequence_id:
            raise UserError(_('Este diario no tiene configurado el Nro de nota de entrega. Vaya al diario, pestaña *Configuracion sec. Facturación* y en el campo *Proximo Nro Documento* agregue uno'))
        else:
            if not self.journal_id.doc_sequence_id.code:
                raise UserError(_('La secuencia del Nro documento llamado * %s * de este diario, no tiene configurada el Código se secuencias')%self.journal_id.doc_sequence_id.name)
            else:
                SEQUENCE_CODE=self.journal_id.doc_sequence_id.code
                company_id = self.company_id.id
                IrSequence = self.env['ir.sequence'].with_context(force_company=company_id)
                name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name

    @api.onchange('invoice_line_ids','tasa','currency_id','price_ref_div_product')
    def actualiza_precio(self):
        if self.price_ref_div_product==True:
            if self.company_id.currency_id == self.currency_id:
                if self.invoice_line_ids:
                    linea_fact=self.invoice_line_ids
                    #raise UserError(_("aqui hay=%s")%linea_fact)
                    for det in linea_fact:
                        if det.product_id:
                            det.price_unit=self.tasa*det.price_unit_ref
                            self._onchange_partner_id()
            else:
                if self.invoice_line_ids:
                    linea_fact=self.invoice_line_ids
                    for det in linea_fact:
                        if det.product_id:
                            det.price_unit=det.product_id.lst_price2
                            self._onchange_partner_id()

    @api.onchange('tasa')
    def act_tasa(self):
        busca=self.env['res.currency.rate'].search([('currency_id','=',self.company_id.currency_sec_id.id),('name','<=',self.invoice_date)],order='name desc',limit=1)
        if busca:
            if busca.inverse_company_rate!=self.tasa:
                busca.write({'inverse_company_rate':self.tasa,})
            """self._onchange_quick_edit_line_ids()
            self._compute_tax_totals()
            self._compute_quick_encoding_vals()
            self._onchange_quick_edit_line_ids()
            container = {'records': self}
            self._check_balanced(container)
            self._onchange_partner_id()"""



    @contextmanager
    def _check_balanced(self, container):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return

        unbalanced_moves = self._get_unbalanced_moves(container)
        if unbalanced_moves:
            error_msg = _("An error has occurred.")
            for move_id, sum_debit, sum_credit in unbalanced_moves:
                move = self.browse(move_id)
                error_msg += _(
                    "\n\n"
                    "The move (%s) is not balanced.\n"
                    "The total of debits equals %s and the total of credits equals %s.\n"
                    "You might want to specify a default account on journal \"%s\" to automatically balance each move.",
                    move.display_name,
                    format_amount(self.env, sum_debit, move.company_id.currency_id),
                    format_amount(self.env, sum_credit, move.company_id.currency_id),
                    move.journal_id.name)
            #raise UserError(error_msg)


class  AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    #balance_aux=fields.Float(compute='_compute_balance_conversion')
    credit_div=fields.Float(compute='_compute_contravalor_credit')
    debit_div=fields.Float(compute='_compute_contravalor_debit')
    price_unit_ref = fields.Float(compute='_compute_price_unit_ref',store=True, readonly=0,digits=(12, 4))
    linea_exenta = fields.Boolean(default=False)

    def _compute_contravalor_credit(self):
        valor=0
        for selff in self:
            valor=selff.credit/selff.move_id.tasa if selff.move_id.tasa!=0 else selff.credit
            selff.credit_div=valor

    def _compute_contravalor_debit(self):
        valor=0
        for selff in self:
            valor=selff.debit/selff.move_id.tasa if selff.move_id.tasa!=0 else selff.debit
            selff.debit_div=valor

    @api.depends('product_id')
    def _compute_price_unit_ref(self):
        for selff in self:
            selff.price_unit_ref=selff.product_id.lst_price2

class AccountPagosFacturas(models.Model):
    _name = 'account.payment.fact'

    move_id = fields.Many2one('account.move')#
    tasa = fields.Float(digits=(12, 4))#
    porcentage = fields.Float(compute='_compute_porcentage')#
    monta_a_pagar = fields.Float()#
    monta_a_pagar_bs = fields.Float(compute='_compute_eq_bs')#
    monto_ret_bs = fields.Float(compute='_compute_ret')#
    moneda = fields.Many2one('res.currency')#
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    account_journal_id = fields.Many2one('account.journal',string="Diario")#
    account_payment_method_id = fields.Many2one('account.payment.method.line')#
    payment_id=fields.Many2one('account.payment')
    asiento_igtf=fields.Many2one('account.move',help='Aqui se refleja el asiento del igtf solo si el pago se realiza a credito')
    fecha=fields.Date()

    @api.onchange('monta_a_pagar')
    @api.depends('monta_a_pagar')
    def _compute_eq_bs(self):
        for selff in self:
            if selff.moneda.id!=selff.company_id.currency_id.id:
                valor=selff.tasa*selff.monta_a_pagar
            else:
                valor=selff.monta_a_pagar
            selff.monta_a_pagar_bs=valor

    def _compute_ret(self):
        for selff in self:
            if selff.move_id.journal_id.nota_entrega!=True and selff.move_id.journal_id.tipo_doc!='ne':
                valor=selff.monta_a_pagar_bs*selff.porcentage/100
                selff.monto_ret_bs=valor
            else:
                selff.monto_ret_bs=0


    def _compute_porcentage(self):
        for selff in self:
            if selff.moneda.id!=selff.company_id.currency_id.id:
                valor=selff.company_id.percentage_cli_igtf
            else:
                valor=0
            if selff.move_id.journal_id.nota_entrega==True or selff.move_id.journal_id.tipo_doc=='ne':
                valor=0
            selff.porcentage=valor