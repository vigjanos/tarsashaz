# -*- coding: utf-8 -*-
'''
create by vigjanos on 2016.12.18.
'''

from seged3 import *
from openerp import models, fields, api, exceptions, _


class tarh_rendkivuli_lekerdez2(models.Model):
    _name = 'tarh.rendkivuli.lekerdez2'

    kezdatum = fields.Date('Kezdő dátum', default="2016-01-01", required=True)
    vegdatum = fields.Date('Befejező dátum', default=fields.date.today(), required=True)
    tarsashaz = fields.Many2one('res.partner', string='Társasház', required=True,
                                domain=[('is_company', '=', True), ('name', 'ilike', 'társash')])
    sor_id = fields.One2many('tarh.rendkivuli.lekerdez2.sor', 'lekerdezes_id')

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
        _sor_hivatkozas = self.env['tarh.rendkivuli.lekerdez2.sor']
        _sajat_id = self.id

        # ha már volt ezzel a táblával lekérdezés, akkor töröljük a sorokat
        torlendok = _sor_hivatkozas.search([('lekerdezes_id', '=', _sajat_id)])
        torlendok.unlink()

        tulajdonosok = lakolista(self,_vegdatum,_tarsashaz)
        for tulajdonos in tulajdonosok:
            _tulaj = self.env['res.partner'].search([('id','=',tulajdonos)])
            _tulajdonos_kezdatum = _kezdatum
            _tulajdonos_vegdatum = _vegdatum
            # nyitoegyenleg vizsgálata, ha későbbi mint a kezdatum akkor csak onnan kezdjük lekérdezni
            _nyito_record = self.env['tarh.lako.nyito'].search([('tarh_lako', '=', tulajdonos)])
            if _tulajdonos_kezdatum < _nyito_record[0].egyenleg_datuma:
                _tulajdonos_kezdatum = _nyito_record[0].egyenleg_datuma

            kezdo_lekerdezes = tulajegyenleg(self, tulajdonos, _tulajdonos_kezdatum)
            befejezo_lekerdezes = tulajegyenleg(self, tulajdonos, _tulajdonos_vegdatum)

            # előállítjuk az előírás és befizetés listákat
            sum_eloiras = 0
            sum_befizetes = 0
            kezdo_eloiras = kezdo_lekerdezes[4]
            kezdo_befizetes = kezdo_lekerdezes[5]
            print _tulaj.name
            befejezo_eloiras = befejezo_lekerdezes[4]
            befejezo_befizetes = befejezo_lekerdezes[5]
            zaro_egyenleg = befejezo_lekerdezes[0]
            eloiras_lista = list(set(befejezo_eloiras) - set(kezdo_eloiras))
            #befizetes_lista = list(set(befejezo_befizetes) - set(kezdo_befizetes))  a teljesen ugyanolyan sorokat is kiveszi
            befizetes_lista = []
            for _befizetes in befejezo_befizetes:
                if not _befizetes[0] < str_to_date(_kezdatum):
                    befizetes_lista.append(_befizetes)


            for eloiras in eloiras_lista:
                if 'endkívüli'.decode('utf-8') in eloiras[1]:
                    sum_eloiras = sum_eloiras + eloiras[2]
            for befizetes in befizetes_lista:
                if 'endk' in befizetes[1]:
                    sum_befizetes = sum_befizetes + befizetes[2]
            if sum_eloiras > 0 or sum_befizetes > 0:
                # ha volt rendkívüli előírás vagy befizetés akkor beírjuk a sorba
                _sor_hivatkozas.create({
                    'alb_szam': _tulaj.alb_szam,
                    'tulajdonos': tulajdonos,
                    'eloiras': sum_eloiras,
                    'befizetes': sum_befizetes,
                    'egyenleg': sum_befizetes - sum_eloiras,
                    'lekerdezes_id' : _sajat_id
                })
        return


class tarh_rendkivuli_lekerdez2_sor(models.Model):
    _name = 'tarh.rendkivuli.lekerdez2.sor'

    alb_szam = fields.Integer("Albetét száma")
    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    eloiras = fields.Integer('Előírás')
    befizetes = fields.Integer('Befizetés')
    egyenleg = fields.Integer('Egyenleg')
    lekerdezes_id = fields.Many2one('tarh.rendkivuli.lekerdez2', ondelete='cascade', string='Szöveg')

    _order = 'alb_szam'
