# -*- coding: utf-8 -*-

'''
 Created by vigjani on 2018-08-13..
'''

from openerp import models, fields, api


class Postazas(models.Model):
    _name = 'tarh_postazas'

    cimzett = fields.many2one('res.partner', stirng='Címzett', help='')
    bekuldo = fields.many2one('res.partner', string='Beküldő', help='')
    erkezett = fields.Date('erkezett', string='Érkezett')
    elkuldve = fields.Date('elkuldve', string='Kiküldve')
    szamla = fields.Boolean('szamla', string='Számla_e')
    felelos = fields.Many2one('felelos', string="Felelős")


