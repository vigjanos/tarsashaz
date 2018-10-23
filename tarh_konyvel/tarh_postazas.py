# -*- coding: utf-8 -*-

'''
 Created by vigjani on 2018-08-13..
'''

from openerp import models, fields, api


class Postazas(models.Model):
    _name = 'tarh.postazas'
    _order = 'erkezett desc, id desc'

    cimzett = fields.Many2one('res.partner', string='Címzett', help='', required="True")
    bekuldo = fields.Many2one('res.partner', string='Feladó', help='', required="True")
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
    _order = 'datum desc'

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
    _order = 'datum desc'

    datum = fields.Date('Dátum', default=fields.Date.today)
    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    oldalszam = fields.Integer('Oldalszám')
    megjegyzes = fields.Char('Megjegyzés')

class Mero_ora(models.Model):
    _name = ('tarh.mero.ora')
    _order = 'tarsashaz, tulajdonos'

    name = fields.Char('Gyári szám')
    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos', required='True')
    ora_tipus = fields.Selection([('hidegviz', 'Hidegvíz'),
                                  ('melegviz','Melegvíz'),
                                  ('homenny','Hőmennyiség'),
                                  ('elekt','Elektromos')],
                                 default='hidegviz',
                                 string='Óra típus')
    felszerelve = fields.Date('Felszerelve')
    ervenyes = fields.Date('Érvényesség')
    aktiv = fields.Boolean(string='Aktív', default='True')

class Oraallas_rogzites(models.Model):
    _name = 'tarh.oraallas.rogzites'
    _order = 'datum desc'

    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    tulaj = fields.Many2one('res.partner', string='Tulajdonos', required='True')
    mero_ora = fields.Many2one('tarh.mero.ora', string='mérőóra')
    ora_allas = fields.Integer('Óraállás')
    oratipus = fields.Char('Óratípus')
    datum = fields.Date('Dátum')
    olvasott = fields.Boolean('Leolvasott érték', default='True')

    @api.onchange('mero_ora')
    def mero(self):
        print self.mero_ora.ora_tipus
        self.oratipus = self.mero_ora.ora_tipus
        pass
        return()

