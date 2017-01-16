# -*- coding: utf-8 -*-
'''
create by vigjanos on 2017.01.12.
'''

from openerp import models, fields, api
from seged3 import utolso_konyvelt_datum,lakolista,tulajegyenleg
from datetime import date



class tarh_lako_eves2(models.Model):
    _name = "tarh.lako.eves2"

    kezdatum = fields.Date('Kezdő dátum')
    vegdatum = fields.Date('Záró dátum', default='2016-12-31')
    tarsashaz = fields.Many2one('res.partner',
                                string='Társasház',
                                domain=[('is_company', '=', True), ('name', 'ilike', 'társasház')])
    bank = fields.Char('Bank', size=64)
    tulaj_id = fields.One2many('tarh.lako.eves2.tulaj', 'tarsashaz_id')

    @api.onchange('tarsashaz')
    def _onchange_tarsashaz(self):
        self.tarsashaz = self.tarsashaz.id
        self.bank = self.tarsashaz.uzemeltetesi
        most = date.today()
        self.kezdatum = date(most.year - 1, 1, 1)
        if self.tarsashaz:
            self.vegdatum = utolso_konyvelt_datum(self, self.tarsashaz.id)
        return

    @api.multi
    def lekerdez(self):
        _kezdatum = self.kezdatum
        _vegdatum = self.vegdatum
        _tarsashaz = self.tarsashaz.id

        _sajat_id = self.id
        _res_partner_hivatkozas = self.env['res.partner']
        _tulajdonos_hivatkozas = self.env['tarh.lako.eves2.tulaj']
        _tulajdonos_sor_hivatkozas = self.env['tarh.lako.eves2.tulaj.sor']

        #töröljük az ehhez a lekérdezéshez már korábban létrehozott sorokat
        torlendok = _tulajdonos_hivatkozas.search([('tarsashaz_id','=',_sajat_id)])
        torlendok.unlink()


        tulajlista = lakolista(self,_vegdatum,_tarsashaz)
        for tulaj in tulajlista:
            tulajdonos = _res_partner_hivatkozas.search([('id', '=', tulaj)])
            valami = _tulajdonos_hivatkozas.create({
                'tulajdonos' : tulajdonos.id,
                'tarsashaz_id' : _sajat_id
            })
            print valami.id
            pass


        return {
            'type': 'ir.actions.client',
            'tag': 'action_warn',
            'name': 'Semmi',
            'params': {
                'title': 'Figyelem',
                'text': 'megnyomtad a gombot!!!' ,
                'sticky': False
            }
        }


class tarh_lako_eves2_tulaj(models.Model):
    _name = 'tarh.lako.eves2.tulaj'

    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    tarsashaz_id = fields.Many2one('tarh.lako.eves2', string='Társasház', ondelete='cascade')
    eloiras_id = fields.One2many('tarh.lako.eves2.tulaj.sor', 'tul_id')

    _order = 'tulajdonos'


class tarh_lako_eves2_tulaj_sor(models.Model):
    _name = 'tarh.lako.eves2.tulaj.sor'

    erteknap = fields.Date('Könyvelés napja')
    szoveg = fields.Char('Előírás', size=64)
    eloiras = fields.Integer('Előírás')
    befizetes = fields.Integer('Befizetés')
    tul_id = fields.Many2one('tarh.lako.eves2.tulaj', string='', ondelete='cascade')

    _order = 'erteknap, id'
