# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.release import version_info

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
    fecha = fields.Datetime(string='Fecha', required=True, readonly=True, index=True, copy=False, default=fields.Datetime.now)
    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which sales order is created.")
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

    user_id = fields.Many2one(
        'res.users', string='Creacion orden', index=True, tracking=2, default=lambda self: self.env.user)
    cliente_id = fields.Many2one('res.partner', string='Cliente',required=True,tracking=1)
    divisa_linea_ids = fields.One2many('divisa.orden.linea','divisa_orden_id','Linea')

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

class DivisaOrdenLinea(models.Model):
    _name = "divisa.orden.linea"
    _description = "Divisa orden linea"

    divisa_orden_id = fields.Many2one('divisa.orden','Divisa orden')
    tipo = fields.Many2one('divisa.tipo_linea','Tipo')
    monto = fields.Float('Monto')

class DivisaTipoLinea(models.Model):
    _name = "divisa.tipo_linea"
    _description = "Diviso tipo linea"

    name = fields.Char('Nombre')
