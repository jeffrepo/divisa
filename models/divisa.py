# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.release import version_info
from datetime import datetime, timezone
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.exceptions import UserError, AccessError
import logging

class DivisaConfiguracion(models.Model):
    _name = "divisa.configuracion"
    _description = "Configuracion de tasas"

    fecha = fields.Date('Fecha',required=True)
    tipo = fields.Selection([
        ('compra_dolares', 'COMPRA DE DOLARES'),
        ('venta_dolares', 'VENTA DE DOLARES'),
        ('compra_euros', 'COMPRA DE EUROS'),
        ('venta_euros', 'VENTA DE EUROS'),
        ('compra_euros_en_d', 'COMPRA DE EUROS EN $'),
        ('venta_euros_en_d', 'VENTA DE EUROS EN $'),
        ('venta_euros_en_d', 'VENTA DE EUROS EN $'),
    ], required=True,
        help="Escoja el tipo de divisa")
    linea_ids = fields.One2many('divisa.configuracion.linea','config_id','Lineas')
    interes = fields.Float('% Interés', required=True, default=10)

class DivisaConfiguracion(models.Model):
    _name = "divisa.configuracion.linea"
    _description = "Lineas de divisa"

    config_id = fields.Many2one('divisa.configuracion','Configuracion divisa')
    tipo = fields.Many2one('divisa.tipo_linea','Tipo')
    tasa = fields.Float('Tasa')

class DivisaOrden(models.Model):
    _name = "divisa.orden"
    _description = "Orden de divisa"

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    fecha = fields.Datetime(string='Fecha', required=True, index=True, copy=False, default=fields.Datetime.now)
    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which sales order is created.")
    tipo = fields.Selection([
        ('compra_dolares', 'COMPRA DE DOLARES'),
        ('venta_dolares', 'VENTA DE DOLARES'),
        ('compra_euros', 'COMPRA DE EUROS'),
        ('venta_euros', 'VENTA DE EUROS'),
        ('compra_euros_en_d', 'COMPRA DE EUROS EN $'),
        ('venta_euros_en_d', 'VENTA DE EUROS EN $'),
    ], required=True,
        help="Escoja el tipo de divisa")

    user_id = fields.Many2one(
        'res.users', string='Creacion orden', index=True, tracking=2, default=lambda self: self.env.user)
    cliente_id = fields.Many2one('res.partner', string='Cliente',required=True,tracking=1)
    divisa_linea_ids = fields.One2many('divisa.orden.linea','divisa_orden_id','Linea')
    interes = fields.Float('Interés')
    total = fields.Float('Total')
    moneda_monto_id = fields.Many2one('res.currency','Moneda monto')
    moneda_valor_id = fields.Many2one('res.currency','Moneda valor')
    currency_id = fields.Many2one('res.currency','Moneda')
    status = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('hecho','hecho'),
    ], string='Status', help='Estado',readonly=True, default='nuevo')


    @api.onchange('tipo')
    def onchange_tipo(self):
        if self.tipo:
            self.currency_id = self.env['res.currency'].search([('name','=','GTQ')]).id
            if self.tipo in ['compra_dolares','venta_dolares']:
                self.moneda_monto_id = self.env['res.currency'].search([('name','=','USD')]).id
                self.moneda_valor_id = self.env['res.currency'].search([('name','=','GTQ')]).id
            if self.tipo in ['compra_euros','venta_euros']:
                self.moneda_monto_id = self.env['res.currency'].search([('name','=','EUR')]).id
                self.moneda_valor_id = self.env['res.currency'].search([('name','=','GTQ')]).id
            if self.tipo in ['compra_euros_en_d','venta_euros_en_d']:
                self.moneda_monto_id = self.env['res.currency'].search([('name','=','EUR')]).id
                self.moneda_valor_id = self.env['res.currency'].search([('name','=','USD')]).id

    def pasar_nuevo(self):
        for divisa in self:
            divisa.status = 'nuevo'
        return True

    def unlink(self):
        for divisa in self:
            if not divisa.status == 'nuevo':
                raise UserError(_('No puede eliminar divisa'))
        return super(DivisaOrden, self).unlink()

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'fecha' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['fecha']))
            vals['name'] = self.env['ir.sequence'].next_by_code('divisa.orden', sequence_date=seq_date) or _('New')

        result = super(DivisaOrden, self).create(vals)
        return result

    def calcular_divisa(self):
        for divisa in self:
            total = 0
            interes = 0
            if divisa.divisa_linea_ids:
                logging.warning(fields.Date.to_string(divisa.fecha))
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                display_date_result = datetime.strftime(pytz.utc.localize(datetime.strptime(str(divisa.fecha),
                DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%d/%m/%Y")
                logging.warning(display_date_result)
                tasa_id = self.env['divisa.configuracion'].search([('fecha','=',display_date_result),('tipo','=', divisa.tipo)])
                if tasa_id:
                    if len(tasa_id) > 1:
                        raise UserError(_('Tiene dos tasas con la misma fecha'))

                    if tasa_id.linea_ids:
                        for linea_divisa in divisa.divisa_linea_ids:
                            for linea_tasa in tasa_id.linea_ids:
                                if linea_divisa.tipo.id == linea_tasa.tipo.id:
                                    linea_divisa.tasa = linea_tasa.tasa
                                    linea_divisa.valor = linea_divisa.monto * linea_tasa.tasa
                                    total += linea_divisa.valor

                    if tasa_id.interes > 0:
                        interes = (total * (tasa_id.interes/100)) if total > 0 else 0
            divisa.interes = interes
            divisa.total = total
            if total > 0:
                divisa.status = 'hecho'
        return True

class DivisaOrdenLinea(models.Model):
    _name = "divisa.orden.linea"
    _description = "Divisa orden linea"

    divisa_orden_id = fields.Many2one('divisa.orden','Divisa orden')
    tipo = fields.Many2one('divisa.tipo_linea','Tipo')
    monto = fields.Float('Monto')
    tasa = fields.Float('Tasa')
    valor = fields.Float('Valor')

class DivisaTipoLinea(models.Model):
    _name = "divisa.tipo_linea"
    _description = "Diviso tipo linea"

    name = fields.Char('Nombre')
