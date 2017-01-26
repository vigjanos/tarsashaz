# -*- coding: utf-8 -*-
'''
create by vigjanos on 2017.01.12.
Az eljárás lekérdezi a megadott társasház záróidőpontban aktív tulajdonosainak folyószámláját
a kezdeti és záró időpontok között és kinyomtatja tulajdonosonként
Alapból a kezdő dátumnak a tavalyi év január 01-et állítja be
Végdátumnak az utolsó könyvet dátumot, de ha az már idei, akkor az
előző év december 31-et.
'''

from openerp import models, fields, api, exceptions, _
from seged3 import utolso_konyvelt_datum,lakolista,tulajegyenleg,str_to_date
from datetime import date


class tarh_lako_eves2(models.Model):
    _name = "tarh.lako.eves2"

    kezdatum = fields.Date('Kezdő dátum')
    vegdatum = fields.Date('Záró dátum', default='2016-12-31')
    tarsashaz = fields.Many2one('res.partner',
                                string='Társasház', required=True,
                                domain=[('is_company', '=', True), ('name', 'ilike', 'társasház')])
    bank = fields.Char('Bank', size=64)
    tulaj_id = fields.One2many('tarh.lako.eves2.tulaj', 'tarsashaz_id')

    @api.onchange('tarsashaz')
    def _onchange_tarsashaz(self):
        self.tarsashaz = self.tarsashaz.id
        self.bank = self.tarsashaz.uzemeltetesi
        most = date.today()
        self.kezdatum = date(most.year - 1, 1, 1)
        if self.tarsashaz:  # hogy első hívásnál ne dobjon hibát
            uts_konyv_dat= str_to_date(utolso_konyvelt_datum(self, self.tarsashaz.id))
            if uts_konyv_dat > date(most.year-1,12,31):
                self.vegdatum = date(most.year-1,12,31)
            else:
                self.vegdatum = uts_konyv_dat
        return

    @api.multi
    def lekerdez(self):
        _kezdatum = self.kezdatum
        _vegdatum = self.vegdatum
        _tarsashaz = self.tarsashaz.id

        if _kezdatum > _vegdatum:
            raise exceptions.ValidationError(_("A befejező időpont nem lehet korábbi mint a kezdő időpont!!!"))

        _sajat_id = self.id
        _res_partner_hivatkozas = self.env['res.partner']
        _tulajdonos_hivatkozas = self.env['tarh.lako.eves2.tulaj']
        _tulajdonos_sor_hivatkozas = self.env['tarh.lako.eves2.tulaj.sor']

        #töröljük az ehhez a lekérdezéshez már korábban létrehozott sorokat
        torlendok = _tulajdonos_hivatkozas.search([('tarsashaz_id','=',_sajat_id)])
        torlendok.unlink()


        tulajlista = lakolista(self,_vegdatum,_tarsashaz)
        for tulaj in tulajlista:
            tul_datum=_kezdatum
            tulajdonos = _res_partner_hivatkozas.search([('id', '=', tulaj)])
            most_rogzitve = _tulajdonos_hivatkozas.create({
                'tulajdonos' : tulajdonos.id,
                'alb_szam': tulajdonos.alb_szam,
                'tarsashaz_id' : _sajat_id
            })
            sajat_id=most_rogzitve.id

            _nyito_record = self.env['tarh.lako.nyito'].search([('tarh_lako', '=', tulaj)])

            if _nyito_record:  # van nyitóegyenleg!
                # dátumok vizsgálata
                if tul_datum < _nyito_record[0].egyenleg_datuma:
                    tul_datum = _nyito_record[0].egyenleg_datuma

                if _vegdatum < _nyito_record[0].egyenleg_datuma:
                    raise exceptions.ValidationError(_("Az időszakban még nem volt tulajdonban az ingatlant!"))

                kezdo_lekerdezes = tulajegyenleg(self, tulaj, tul_datum)
                befejezo_lekerdezes = tulajegyenleg(self, tulaj, _vegdatum)

                # ha már volt ezzel a táblával lekérdezés, akkor töröljük a sorokat

                torlendok = _tulajdonos_sor_hivatkozas.search([('tul_id', '=', sajat_id)])
                torlendok.unlink()

                # előállítjuk az előírás és befizetés listákat
                kezdo_eloiras = kezdo_lekerdezes[4]
                kezdo_befizetes = kezdo_lekerdezes[5]
                befejezo_eloiras = befejezo_lekerdezes[4]
                befejezo_befizetes = befejezo_lekerdezes[5]
                zaro_egyenleg = befejezo_lekerdezes[0]
                eloiras_lista = list(set(befejezo_eloiras) - set(kezdo_eloiras))
                befizetes_lista = list(set(befejezo_befizetes) - set(kezdo_befizetes))

                # először kiírjuk a nyitóegyenleget a sorba
                _tulajdonos_sor_hivatkozas.create({
                    'erteknap': tul_datum,
                    'szoveg': "Nyitóegyenleg",
                    'eloiras': 0,
                    'befizetes': kezdo_lekerdezes[0],
                    'tul_id': sajat_id
                })

                # beírjuk az időszak alatti előírásokat
                for eloiras in eloiras_lista:
                    _tulajdonos_sor_hivatkozas.create({
                        'erteknap': eloiras[0],
                        'szoveg': eloiras[1],
                        'eloiras': eloiras[2],
                        'befizetes': 0,
                        'tul_id': sajat_id
                    })

                # beírjuk az időszak alatti befizetéseket
                for befizetes in befizetes_lista:
                    _tulajdonos_sor_hivatkozas.create({
                        'erteknap': befizetes[0],
                        'szoveg': befizetes[1],
                        'eloiras': 0,
                        'befizetes': befizetes[2],
                        'tul_id': sajat_id
                    })

                # rögzítjük a záróegyenleget
                _tulajdonos_sor_hivatkozas.create({
                    'erteknap': _vegdatum,
                    'szoveg': 'Aktuális egyenleg',
                    'eloiras': 0,
                    'befizetes': zaro_egyenleg,
                    'tul_id': sajat_id
                })
            else:
                raise exceptions.ValidationError(_("Figyelem!!! Nincs nyitóegyenlege " + tulajdonos.name + " tulajdonosnak!"))

        return {
            'type': 'ir.actions.client',
            'tag': 'action_warn',
            'name': 'Semmi',
            'params': {
                'title': 'Figyelem',
                'text': 'A leválogatás elkészült!!!',
                'sticky': False
            }
        }


class tarh_lako_eves2_tulaj(models.Model):
    _name = 'tarh.lako.eves2.tulaj'

    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    alb_szam = fields.Integer('Albetét szám')
    tarsashaz_id = fields.Many2one('tarh.lako.eves2', string='Társasház', ondelete='cascade')
    eloiras_id = fields.One2many('tarh.lako.eves2.tulaj.sor', 'tul_id')

    _order = 'alb_szam'


class tarh_lako_eves2_tulaj_sor(models.Model):
    _name = 'tarh.lako.eves2.tulaj.sor'

    erteknap = fields.Date('Könyvelés napja')
    szoveg = fields.Char('Szöveg', size=64)
    eloiras = fields.Integer('Előírás')
    befizetes = fields.Integer('Befizetés')
    tul_id = fields.Many2one('tarh.lako.eves2.tulaj', string='', ondelete='cascade')

    _order = 'erteknap, id'
