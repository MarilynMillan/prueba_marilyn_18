# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _ 
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger('__name__')


class AccountMove(models.Model):
    _inherit = 'account.move'

    wh_muni_id = fields.Many2one('municipality.tax', string='Retención Municipal', readonly=True, copy=False)

    def button_draft(self):
        super().button_draft()
        if self.wh_muni_id and self.move_type!='entry':
            self.wh_muni_id.action_draft()
            #self.wh_muni_id.asiento_ret_id.button_draft()
            #self.wh_muni_id.asiento_ret_id.unlink()
            self.wh_muni_id.with_context(force_delete=True).unlink()



    def action_post(self):
        """This function create municital retention voucher too."""
        invoice = super().action_post()
        if self.partner_id.muni_wh_agent==True:
            # si no existe una retencion ya
            bann=0
            bann=self.verifica_exento_muni()
            if bann>0:
                if not self.wh_muni_id:
                    self._create_muni_wh_voucher()


    def verifica_exento_muni(self):
        acum=0
        #raise UserError(_('self = %s')%self.id)
        puntero_move_line = self.env['account.move.line'].search([('move_id','=',self.id)])
        for det_puntero in puntero_move_line:
            acum=acum+det_puntero.concept_id.aliquot
        return acum



    def _create_muni_wh_voucher(self):
        muni_wh = self.env['municipality.tax']
        valss=({
            'partner_id':self.partner_id.id,
            'transaction_date':self.date,
            'move_type':self.move_type,
            'invoice_id':self.id,
            'rif':self.partner_id.doc_tipo+self.partner_id.vat,
            'address':str(self.partner_id.street)+', '+str(self.partner_id.street2),
            'city':self.partner_id.city,
            'state_id':self.partner_id.state_id.id,
            'municipality_id':self.partner_id.municipality_id.id,
            })
        muni_tax_id = muni_wh.create(valss)
        self.wh_muni_id=muni_tax_id.id
        for item in self.invoice_line_ids:
            # codigo darrell
            base_impuesto=self.conv_div_nac(item.price_subtotal)
            impuesto_mun=item.concept_id.aliquot
            concepto_nb_id=item.concept_id
            existe=self.existe_ret_mun(concepto_nb_id,self.wh_muni_id,base_impuesto)
            if existe=='no':
                volss=({
                    'concept_id':concepto_nb_id.id,
                    'base_tax':base_impuesto,
                    'municipality_tax_id':self.wh_muni_id.id,
                    'invoice_id':self.id,
                    #'invoice_number':self.invoice_number_next,
                    #'invoice_ctrl_number':self.invoice_number_control,
                    })
                self.env['municipality.tax.line'].create(volss)
            else:
                pass
        if self.move_type in ('in_invoice','in_receipt','in_refund'):
            self.wh_muni_id.action_post()

    def existe_ret_mun(self,concepto_nb_id,municipality_tax_id,base_impuesto):
        existe='no'
        busca=self.env['municipality.tax.line'].search([('concept_id','=',concepto_nb_id.id),('municipality_tax_id','=',municipality_tax_id.id)])
        if busca:
            busca.base_tax=busca.base_tax+base_impuesto
            existe='si'
        return existe



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    concept_id = fields.Many2one('muni.wh.concept', string='Municipal Tax')  