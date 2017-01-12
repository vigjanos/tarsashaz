# -*- coding: utf-8 -*-
'''
create by vigjanos on 2017.01.12.
'''

from openerp import models, fields


class tarh_lako_eves2(models.Model):
    _name = "tarh.lako.eves2"

    kezdatum = fields.Date('Kezdő dátum')
    vegdatum = fields.Date('Záró dátum')
    tarsashaz = fields.Many2one('res.partner',
                                string='Társasház',
                                domain=[('is_company', '=', True), ('name', 'ilike', 'társasház')])
    bank = fields.Char('Bank', size=64)
    tulaj_id = fields.One2many('tarh.lako.eves2.tulaj', 'tarsashaz_id')


class tarh_lako_eves2_tulaj(models.Model):
    _name = 'tarh.lako.eves2.tulaj'

    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    tarsashaz_id = fields.Many2one('tarh.lako.eves2', string='Társasház')
    eloiras_id = fields.One2many('tarh.lako.eves2.tulaj.sor', 'tulaj_id')

class tarh_lako_eves2_tulaj_sor(models.Model):
    _name = 'tarh.lako.eves2.tulaj.sor'

    eloiras_e = fields.Boolean()
    kdatum = fields.Date('Kezdő dátum')
    datum = fields.Date('Záró dátum')
    szoveg = fields.Char('Szöveg')
    osszeg = fields.Integer('Összeg')
    tul_id = fields.Many2one('tarh.lako.eves2.tulaj', string='')
    seged_id = fields.Integer('Segéd változó')
