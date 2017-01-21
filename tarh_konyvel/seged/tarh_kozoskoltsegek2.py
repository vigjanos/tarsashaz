# -*- coding: utf-8 -*-
'''
create by vigjanos on 2017.01.21.
'''

from openerp import models, fields, api, exceptions, _


class tarh_kozoskoltsegek2(models.Model):
    _name = 'tarh.kozoskoltsegek2'

    eloir_datum = fields.Date('Előírás dátuma')
    tarsashaz = fields.Many2one('res.partner', string='Társasház',  required=True,
                                domain=[('is_company', '=', True), ('name', 'ilike', 'társasház')])
    tulaj_id = fields.One2many('tarh.kozoskoltsegek2.tulaj', 'tarsashaz_id')

class tarh_kozoskoltsegek2_tulaj(models.Model):
    _name = 'tarh.kozoskoltsegek2.tulaj'

    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    tarsashaz_id = fields.Many2one('tarh.kozoskoltsegek2', string='Társasház')
    eloiras_id = fields.One2many('tarh.kozoskoltsegek2.tulaj.sor', 'tul_id')


class tarh_kozoskoltsegek2_tulaj_sor(models.Model):
    _name = 'tarh.kozoskoltsegek2.tulaj.sor'

    eloiras = fields.Many2one('tarh.eloiras', string='Előírás')
    osszeg = fields.Integer("Összeg")
    kezdatum = fields.Date("Kezdődátum")
    vegdatum = fields.Date("Záró dátum")
    tul_id = fields.Many2one('tarh.kozoskoltsegek2.tulaj', string='')
