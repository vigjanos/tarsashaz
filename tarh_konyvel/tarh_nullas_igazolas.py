# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.10.23..
''' 


from openerp import models, fields, api


class tarh_nullas(models.Model):
    _name = 'tarh.nullas'

    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                   domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    datum = fields.Date(string='Igazolás dátuma', default=fields.date.today())


