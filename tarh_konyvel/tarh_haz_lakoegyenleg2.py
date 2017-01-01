# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2016.12.20..
'''

from seged import *
from seged3 import lakolista, tulajegyenleg
from openerp import models, fields, api, _


class tarh_haz_lakoegyenleg2(models.Model):
    '''
    ebben a lekérdezésben a kiválasztott társasház összes lakójának az egyenlegét kérdezzük le
    a kezdő és végdátum között.
    Nyomtatásnál beállítható, hogy hány hónapnyi tartozás esetén kerüljön kiírásra.
    '''

    _name = 'tarh.haz.lakoegyenleg2'

    kezdatum = fields.Date('Kezdő dátum', default="2016-01-01", required=True)
    vegdatum = fields.Date('Befejező dátum', default=fields.date.today(), required=True)
    lekerdate = fields.Date('Lekérdezés dátuma', default=fields.date.today(), required=True)
    tarsashaz = fields.Many2one('res.partner', string='Társasház', required=True,
                                domain=[('is_company', '=', True), ('name', 'ilike', 'társash')])
    min_tartozas = fields.Integer('Nyomtatás csak ekkora tartozástól', default=20000)
    min_honap = fields.Integer('Nyomtatás csak ennyi hónap tartozástól', default=3)
    sor_id = fields.One2many('tarh.haz.lakoegyenleg2.sor', 'lakoegy_id')

    @api.onchange('tarsashaz')
    def _onchange_tarsashaz(self):
        tarsashaz = self.tarsashaz
        if self.tarsashaz:
            self.vegdatum = utolso_konyvelt_datum(self, self.env.cr, self.env.uid, self.tarsashaz.id)
        return

    @api.multi
    def lekerdez(self):
        _tarsashaz = self.tarsashaz.id
        _kezdatum = self.kezdatum
        _vegdatum = self.vegdatum
        _lekerdate = self.lekerdate

        _sor_hivatkozas = self.env['tarh.haz.lakoegyenleg2.sor']
        _res_partner_hivatkozas = self.env['res.partner']
        _sajat_id = self.id

        # ha már volt ezzel a táblával lekérdezés, akkor töröljük a sorokat
        torlendok = _sor_hivatkozas.search([('lakoegy_id', '=', _sajat_id)])
        torlendok.unlink()

        tulajlista = lakolista(self, _vegdatum, _tarsashaz)
        for tulaj in tulajlista:
            tulajdonos = _res_partner_hivatkozas.search([('id', '=', tulaj)])
            tulajertek_kezd = tulajegyenleg(self, tulaj, _kezdatum)
            tulajertek_veg = tulajegyenleg(self, tulaj, _vegdatum)

            _sor_hivatkozas.create({
                'tulaj': tulajdonos.name,
                'tulajdonos': tulajdonos.id,
                'cim': tulajdonos.street2,
                'kezdoegyenleg': tulajertek_kezd[0],
                'eloirasok': tulajertek_veg[1] - tulajertek_kezd[1],
                'befizetesek': tulajertek_veg[2] - tulajertek_kezd[2],
                'zaroegyenleg': tulajertek_veg[0],
                'albetet': tulajdonos.alb_szam,
                'havi_eloiras': tulajertek_veg[3],
                'lakoegy_id': _sajat_id
            })
        return

class tarh_haz_lakoegyenleg2_sor(models.Model):
    _name = 'tarh.haz.lakoegyenleg2.sor'

    tulaj = fields.Char(string="Tulajdonos", size=128)
    tulajdonos = fields.Many2one("res.partner")
    cim = fields.Char('Emelet', size=32)
    kezdoegyenleg = fields.Integer('Nyitó egyenleg')
    eloirasok = fields.Integer('Előírások')
    befizetesek = fields.Integer('Befizetések')
    zaroegyenleg = fields.Integer('Aktuális egyenleg')
    albetet = fields.Integer('Alb.sz.')
    havi_eloiras = fields.Integer('Havonta előírás')
    lakoegy_id = fields.Many2one('tarh.haz.lakoegyenleg2', ondelete='cascade', readonly=True, string='Szöveg')

    _order = 'albetet'
