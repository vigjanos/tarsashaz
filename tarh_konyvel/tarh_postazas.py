# -*- coding: utf-8 -*-

'''
 Created by vigjani on 2018-08-13..
'''

from openerp import models, fields, api


class Postazas(models.Model):
    _name = 'tarh.postazas'

    cimzett = fields.Many2one('res.partner', string='Címzett', help='')
    bekuldo = fields.Many2one('res.partner', string='Feladó', help='')
    bejovo = fields.Boolean('Bejövő irat', default=True)
    erkezett = fields.Date('Érkezés_dátuma', default=fields.Date.today)
    elkuldve = fields.Date('Kiküldés dátuma', default=fields.Date.today)
    szamla = fields.Boolean('Számla_e?')
    felelos = fields.Many2one('res.users', string="Felelős")
    referencia = fields.Char('Referencia', help='Számlaszám, iktatószám stb.')
    status = fields.Selection([('erkezett', 'Beérkezett'),
                               ('nyomtatva','Megbízás kitöltve'),
                               ('kikuldve','Aláírásra kiküldve'),
                               ('bankba','Bankba leadva'),
                               ('fizetve','Fizetve')],
                              default='erkezett')
    szamla_osszeg = fields.Integer('Számla összege')
    tranzakcio_id = fields.Many2one('tarh.tranzakcio', string='Tranzakció')
    megjegyzes = fields.Text('Megjegyzés')
    dokumentum = fields.Many2many(comodel_name='ir.attachment', string='Dokumetum feltöltése')


class Postakoltseg(models.Model):
    _name = ('tarh.postakoltseg')

    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                   domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    cimzett = fields.Many2one('res.partner', string="Címzett")
    datum = fields.Date('Postázás dátuma', default=fields.Date.today)
    fajta = fields.Selection([('sima', 'Síma'),
                              ('ajanlott','Ajánlott'),
                              ('tertiv','Tértivevényes')
                              ], default='ajanlott', string="Levélfajta")
    osszeg = fields.Integer('Feladás díja')
    megjegyzes = fields.Text('Megjegyzés')


class Fenymasolas(models.Model):
    _name = ('tarh.fenymasolas')

    datum = fields.Date('Dátum', default=fields.Date.today)
    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    oldalszam = fields.Integer('Oldalszám')
    megjegyzes = fields.Char('Megjegyzés')
