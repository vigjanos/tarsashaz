# -*- coding: utf-8 -*-
'''
create by vigjanos on 2016.12.15.
'''

# from seged import *
from seged3 import tulajegyenleg, utolso_konyvelt_datum, str_to_date
from openerp import models, fields, api, exceptions, _
from datetime import date

# from openerp.exceptions import AccessError, Warning




class tarh_lakohavijel2(models.Model):
    _name = 'tarh.lakohavijel2'

    kezdatum = fields.Date('Kezdő dátum', default="2016-01-01")
    vegdatum = fields.Date('Befejező dátum', default=fields.Date.today)
    lekerdatum = fields.Date('Lekérdezés dátuma', default=fields.Date.today)
    tulaj = fields.Many2one('res.partner', string='Tulajdonos')
    tarsashaz = fields.Many2one('res.partner',
                                string='Társasház')
    bankszamla = fields.Char('Társasház üzemeltetési bankszámla')
    sor_id = fields.One2many('tarh.lakohavijel2.sor', 'havijel_id')

    @api.onchange('tulaj')
    def _onchange_tulaj(self):
        self.tarsashaz = self.tulaj.parent_id
        self.bankszamla = self.tulaj.parent_id.uzemeltetesi
        most = date.today()
        self.kezdatum = date(most.year-1, most.month, 1)
        if self.tarsashaz:
            self.vegdatum = utolso_konyvelt_datum(self, self.tulaj.parent_id.id)
        return

    @api.multi
    def lako_havijel_beir(self):
        _tulaj = self.tulaj.id
        _kezdatum = self.kezdatum
        _vegdatum = self.vegdatum
        sajat_id = self.id

        _nyito_record = self.env['tarh.lako.nyito'].search([('tarh_lako', '=', _tulaj)])

        if _nyito_record:  # van nyitóegyenleg!
            # dátumok vizsgálata
            if _kezdatum < _nyito_record[0].egyenleg_datuma:
                _kezdatum = _nyito_record[0].egyenleg_datuma

            if _vegdatum < _nyito_record[0].egyenleg_datuma:
                raise exceptions.ValidationError(_("Az időszakban még nem volt tulajdonban az ingatlant!"))

            #kezdo_lekerdezes = lakoegyenleg3(self, self.env.cr, self.env.uid, _tulaj, _kezdatum)
            #befejezo_lekerdezes = lakoegyenleg3(self, self.env.cr, self.env.uid, _tulaj, _vegdatum)
            kezdo_lekerdezes = tulajegyenleg(self,_tulaj,_kezdatum)
            befejezo_lekerdezes = tulajegyenleg(self,_tulaj,_vegdatum)

            # ha már volt ezzel a táblával lekérdezés, akkor töröljük a sorokat
            _sor_hivatkozas = self.env['tarh.lakohavijel2.sor']
            torlendok = _sor_hivatkozas.search([('havijel_id', '=', sajat_id)])
            torlendok.unlink()

            # ahol van késedelmi kamat, ott kellenek majd ezek
            kamat_kezdoidopontban=0
            kamat_vegidopontban=0

            # előállítjuk az előírás és befizetés listákat
            kezdo_eloiras = kezdo_lekerdezes[4]
            kezdo_befizetes = kezdo_lekerdezes[5]
            befejezo_eloiras = befejezo_lekerdezes[4]
            befejezo_befizetes = befejezo_lekerdezes[5]
            zaro_egyenleg = befejezo_lekerdezes[0]

            #kiszedjük a kezdő listában a már addig felszámított kamat összegét
            for elo in kezdo_eloiras:
                if elo[1] == 'Késedelmi kamat':
                    kamat_kezdoidopontban = elo[2]


            # eloiras_lista = list(set(befejezo_eloiras) - set(kezdo_eloiras)) kiszedte az ugyanarra a napra előírt
            # ugyanolyan előírásokat
            eloiras_lista = []
            for _eloiras in befejezo_eloiras:
                if not _eloiras[0] < str_to_date(_kezdatum):
                    if _eloiras[1] == 'Késedelmi kamat':
                        kamat_vegidopontban = _eloiras[2] - kamat_kezdoidopontban
                    eloiras_lista.append(_eloiras)
            #befizetes_lista = list(set(befejezo_befizetes) - set(kezdo_befizetes))  a teljesen ugyanolyan sorokat is kiveszi
            befizetes_lista = []
            for _befizetes in befejezo_befizetes:
                if not _befizetes[0] <= str_to_date(_kezdatum):
                    befizetes_lista.append(_befizetes)



            # először kiírjuk a nyitóegyenleget a sorba
            _sor_hivatkozas.create({
                'erteknap': _kezdatum,
                'szoveg': "Nyitóegyenleg",
                'eloiras': 0,
                'befizetes': kezdo_lekerdezes[0],
                'havijel_id': sajat_id
            })

            # beírjuk az időszak alatti előírásokat
            for eloiras in eloiras_lista:
                if eloiras[1] == 'Késedelmi kamat':
                    ertek = kamat_vegidopontban
                else:
                    ertek = eloiras[2]
                _sor_hivatkozas.create({
                    'erteknap': eloiras[0],
                    'szoveg': eloiras[1],
                    'eloiras': ertek,
                    'befizetes': 0,
                    'havijel_id': sajat_id
                })

            # beírjuk az időszak alatti befizetéseket
            for befizetes in befizetes_lista:
                _sor_hivatkozas.create({
                    'erteknap': befizetes[0],
                    'szoveg': befizetes[1],
                    'eloiras': 0,
                    'befizetes': befizetes[2],
                    'havijel_id': sajat_id
                })

            # rögzítjük a záróegyenleget
            _sor_hivatkozas.create({
                'erteknap': _vegdatum,
                'szoveg': 'Aktuális egyenleg',
                'eloiras': 0,
                'befizetes': zaro_egyenleg,
                'havijel_id': sajat_id
            })
        else:
            raise exceptions.ValidationError(_("Figyelem!!! Nincs nyitóegyenlege a tulajdonosnak!"))

            # todo     utolsó könyvelt dátumra beállítania végdatumot!


class tarh_lakohavijel2_sor(models.Model):
    _name = 'tarh.lakohavijel2.sor'

    erteknap = fields.Date('Könyvelés napja')
    szoveg = fields.Char('Előírás', size=64)
    eloiras = fields.Integer('Előírás')
    befizetes = fields.Integer('Befizetés')
    havijel_id = fields.Many2one('tarh.lakohavijel2', ondelete='cascade', select=True, readonly=True)

    _order = 'erteknap, id'
