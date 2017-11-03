# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.10.23..
'''

from openerp import models, fields, api
from seged3 import str_to_date, honap_utolsonap
from datetime import date


class tarh_nullas(models.Model):
    _name = 'tarh.nullas'

    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    datum = fields.Date(string='Igazolás dátuma', default=fields.date.today())


'''Ezt majd lehet, hogy el kell innen pakolni később!'''


class tarh_bankbiz_sor(models.Model):
    _inherit = 'tarh.bankbiz.sor'

    '''
    Amennyiben változik a tarh_bankbiz_sor (létrehozzuk, javítjuk, vagy töröljük) és a 
    csekkes befizetés is változtatva van, akkor a tulajdonosnak elő kell írni, vagy törölni kell az 
    előírások közül a csekk befizetés költségét. (feltéve ha a társasháznál van ilyen előírva)
    Ezt úgy csináljuk, hogy felülírjuk a BaseModel create, write, és unlink eljárását,
    meghívjuk az eredeti eljárást, és utána megcsináljuk ami nekünk kell.
    '''

    @api.model
    def create (self, vals):
        resou = super(tarh_bankbiz_sor, self).create(vals) # meghívjuk az eredeti create eljárást
        for ertek in vals:
            if ertek == 'postai':
                _tarh_eloiras_haz = self.env['tarh.eloiras.haz']
                _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
                _eloir_fajta = self.env['eloiras.fajta']
                partner = resou.partner.id
                tarsashaz_id = resou.partner.parent_id.id
                datum = resou.erteknap
                csekkes_eloir_fajta_id = _eloir_fajta.search([('name', 'ilike', '%csekkes%')]).id
                if resou.postai:
                    van_csekkes = _tarh_eloiras_haz.search(
                        [('konyvelt_haz', '=', tarsashaz_id),
                         ('eloirfajta.name', 'ilike', 'Csekkes%'),
                         ('eloir_kezd', '<', datum),
                         ('eloir_vege', '>=', datum)])
                    if van_csekkes:
                        lako_egyszeri_eloiras(self, tarsashaz_id, partner, van_csekkes.osszeg, datum, csekkes_eloir_fajta_id)
        return resou

    ''' Ide akkor jutunk, ha javítjuk a bankbizonylat egy sorát. Megnézzük, hogy volt-e érintve a csekkes befizetés 
    (postai), ha igen akkor előírunk, vagy törlünk a változtatásnak megfelelően.
    '''
    @api.multi
    def write (self, vals):
        reso = super(tarh_bankbiz_sor, self).write(vals)  # elvégezzük a rekord kiírását
        for ertek in vals:
            if ertek == 'postai':  # ez azt jelenti, hogy van változás a csekkes befizetés jelölésében, tehát van teendő
                _res_partner = self.env['res.partner']
                _tarh_eloiras_haz = self.env['tarh.eloiras.haz']
                _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
                _eloir_fajta = self.env['eloiras.fajta']
                sor_id = self.ids[0]
                partner = self.partner.id
                tarsashaz_id = self.partner.parent_id.id
                datum = self.erteknap
                csekkes_eloir_fajta_id = _eloir_fajta.search([('name', 'ilike', '%csekkes%')]).id

                if vals['postai']:  # ha igaz, akkor most jelölték be, ezért elő kell
                    # írnunk a lakónak a csekkbefizetés költségét
                    van_csekkes = _tarh_eloiras_haz.search(
                        [('konyvelt_haz', '=', tarsashaz_id),
                         ('eloirfajta.name', 'ilike', 'Csekkes%'),
                         ('eloir_kezd', '<', datum),
                         ('eloir_vege', '>=', datum)])
                    if van_csekkes:  # van a társasházban a csekkbefizetéshez előírva a datum idején kötelezettség
                        lako_egyszeri_eloiras(self, tarsashaz_id, partner, van_csekkes.osszeg, datum,
                                              csekkes_eloir_fajta_id)
                        # át kell adni: társasház, tulajdonos, összeg, dátum, előírás fajta

                else:  # ha idefut akkor van változás a postaiban, de éppen töröljük!
                    print('else ág!')
                    ertekdatum = str_to_date(datum)
                    erteknap = ertekdatum.day
                    eloir_kezd = date(ertekdatum.year,ertekdatum.month,1)
                    eloir_vege = honap_utolsonap(ertekdatum)
                    talalat = _tarh_eloiras_lako.search(
                        [('lako', '=', partner),
                         ('eloirfajta', '=', csekkes_eloir_fajta_id),
                         ('eloir_kezd','=',eloir_kezd),
                         ('eloir_vege','=',eloir_vege),
                         ('esedekes','=',erteknap)])
                    talalat.unlink()
        print('Ez van utána')
        return reso

    @api.multi
    def unlink (self):
        _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
        _eloir_fajta = self.env['eloiras.fajta']
        partner = self.partner.id
        datum = self.erteknap
        csekkes_eloir_fajta_id = _eloir_fajta.search([('name', 'ilike', '%csekkes%')]).id
        if self.postai:
            ertekdatum = str_to_date(datum)
            erteknap = ertekdatum.day
            eloir_kezd = date(ertekdatum.year, ertekdatum.month, 1)
            eloir_vege = honap_utolsonap(ertekdatum)
            talalat = _tarh_eloiras_lako.search(
                [('lako', '=', partner),
                 ('eloirfajta', '=', csekkes_eloir_fajta_id),
                 ('eloir_kezd', '=', eloir_kezd),
                 ('eloir_vege', '=', eloir_vege),
                 ('esedekes', '=', erteknap)])
            talalat.unlink()
        res = super(tarh_bankbiz_sor, self).unlink() #végrehajtjuk az eredeti törlést
        return()


class tarh_bankbiz(models.Model):
    _inherit = 'tarh.bankbiz'
    '''Ez azért kell, mert ha a bankbiz_sort töröljük, akkor törli ugyan a hozzá tartozó
    tarh_bankbiz_sor mezőket, de ott nem fut le a tarh_bankbiz_sor unlink eljárás.
    Gondoskodni kell arról, hogy ha van a tarh_bankbiz_sor között olyan elem amiben a csekkes
    befizetés érintve van, akkor töröljük a tulajdonos csekk befizetési előírásait'''

    @api.multi
    def unlink (self):
        print('Ez van előtte törlés')
        print self.ids[0]
        res = super(tarh_bankbiz, self).unlink()
        print('Ez van utána törlés')
        return


def lako_egyszeri_eloiras (self, tarsashaz, lako, osszeg, datum, eloiras):
    erteknap = str_to_date(datum)
    eloir_kezd = date(erteknap.year, erteknap.month, 1)
    eloir_vege = honap_utolsonap(erteknap)
    _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
    sikeres = _tarh_eloiras_lako.create({
        'esedekes': erteknap.day,
        'lako': lako,
        'tarsashaz': tarsashaz,
        'eloirfajta': eloiras,
        'osszeg': osszeg,
        'eloir_kezd': eloir_kezd,
        'eloir_vege': eloir_vege,
    })
    return()

