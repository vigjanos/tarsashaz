# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.12.26..
 Boldog karajcsont!
'''

from openerp import models, fields, api, exceptions
from seged3 import str_to_date, honap_utolsonap
from datetime import date, timedelta


class tarh_eloiras_haz(models.Model):
    _inherit = 'tarh.eloiras.haz'



    @api.model
    def create (self, vals):

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
            return ()

        '''Be kell olvasni a változókat a lapról'''
        _eloir_kezd = str_to_date(vals['eloir_kezd'])
        _eloir_vege = str_to_date(vals['eloir_vege'])
        _eloirfajta = vals['eloirfajta']
        _esedekes = vals['esedekes']
        _konyvelt_haz = vals['konyvelt_haz']
        _osszeg = vals['osszeg']
        _rendszeres = vals['rendszeres']
        _terulet_aranyos = vals['terulet_aranyos']
        _tulhanyad_aranyos = vals['tulhanyad_aranyos']
        _legm_aranyos = vals['legm_aranyos']
        _lakoszam_aranyos = vals['lakoszam_aranyos']
        regi_vege = _eloir_kezd - timedelta(days=1)  # az új kezdete - 1 nap lesz a régi vége

        _tarh_eloiras_haz = self.env['tarh.eloiras.haz']
        _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
        _res_partner = self.env['res.partner']
        _eloiras_fajta_hiv = self.env['eloiras.fajta']
        _tarh_bankbiz_sor = self.env['tarh.bankbiz.sor']
        csekkes_eloir_fajta_id = _eloiras_fajta_hiv.search([('name', 'ilike', '%csekkes%')]).id

        print "beolvasás vége!"
        '''
        Meg kell nézni, hogy van-e már ilyen előírás, mert akkor
            1./ át kell állítani a régi ház-előírás végét a mostani kezdete -1 nap
            2./ meg kell keresni a tulajdonosokat, akiknek ennek az előírásnak a záródátuma 2050-12-31,
            2./a. azt is keresni kell, hogy az eladás dátuma későbbi-e mint az új előírás kezdete 
            3./ a talált tulajdonosok előírásainak záródátumát változtatni kell a mostani kezdő -1 nap
        Ha volt, ha nem volt még ilyen előírás  
            4./ Elő kell írni a tulajdonosok részére az új ház-előírást.'''

        van_eloiras = _tarh_eloiras_haz.search([('konyvelt_haz', '=', _konyvelt_haz),
                                                ('eloirfajta', '=', _eloirfajta),
                                                ('eloir_vege', '=', _eloir_vege)])
        mindegyforma = _tarh_eloiras_haz.search([('konyvelt_haz', '=', _konyvelt_haz),
                                                ('eloirfajta', '=', _eloirfajta),
                                                ('eloir_vege', '=', _eloir_vege),
                                                 ('eloir_kezd','=',_eloir_kezd)])
        if mindegyforma:
            raise exceptions.ValidationError(("Kéteszer nem lehet teljesen ugyanazt az előírást előírni"))

        if len(van_eloiras) > 1:
            print 'Hiba van, több mint egy!!!! ide kell dobni egy excepsönt!'
        if van_eloiras:

            sikerult = van_eloiras[0].write({'eloir_vege': regi_vege})
            if not sikerult:
                print 'Ide kell egy excepsön, hogy félrement az írás!'
            '''Idáig tartott az 1./ jön a 2./'''

            tulajok_regi_eloirasai = _tarh_eloiras_lako.search([('eloir_vege', '=', _eloir_vege),
                                                                ('eloirfajta', '=', _eloirfajta),
                                                                ('tarsashaz', '=', _konyvelt_haz)])
            '''most jön a 3./ és a 4. együtt amikor volt régebben már előírás'''
            if tulajok_regi_eloirasai:
                for uj_eloiras in tulajok_regi_eloirasai:
                    uj_eloiras.write({'eloir_vege': regi_vege})
                    print 'átírtam ', regi_vege, 'értékre'

                    osszeg = 0
                    if _terulet_aranyos:
                        negyzetmeter = uj_eloiras.lako.alapterulet
                        osszeg = _osszeg * negyzetmeter
                    elif _tulhanyad_aranyos:
                        tulhanyad = uj_eloiras.lako.tulhanyad
                        osszeg = _osszeg * tulhanyad
                    elif _legm_aranyos:
                        legm3 = uj_eloiras.lako.legm3
                        osszeg = _osszeg * legm3
                    elif _lakoszam_aranyos:
                        lakoszam = uj_eloiras.lako.lakoszam
                        osszeg = _osszeg * lakoszam
                    else:
                        osszeg = _osszeg
                    sikeres = _tarh_eloiras_lako.create({
                        'esedekes': _esedekes,
                        'lako': uj_eloiras.lako.id,
                        'tarsashaz': _konyvelt_haz,
                        'eloirfajta': uj_eloiras.eloirfajta.id,
                        'osszeg': osszeg,
                        'eloir_kezd': _eloir_kezd,
                        'eloir_vege': _eloir_vege
                    })

                    pass
            '''2./a. megnézzük, hogy nem esik-e a változtatott időszakba lakás eladás'''
            eladott_ingatlanok = _res_partner.search([('parent_id', '=', _konyvelt_haz),
                                                      ('alb_eladas', '>', _eloir_kezd),
                                                      '|', ('active', '=', True), ('active', '=', False)])
            '''keressük, hogy ezek között volt-e olyan amelynek volt eloirfajta előírása'''
            if eladott_ingatlanok:
                for eladott_ingatlan in eladott_ingatlanok:
                    van_eladottak_kozt = _tarh_eloiras_lako.search([('lako', '=', eladott_ingatlan.id),
                                                                    ('eloirfajta', '=', _eloirfajta),
                                                                    ('eloir_vege', '=', eladott_ingatlan.alb_eladas)])
                    '''Van az eladottak között amit korrigálni kell'''
                    if van_eladottak_kozt:
                        for eladott_eloiras in van_eladottak_kozt:
                            '''ezt az előírást módosítani kell, az eloir_vege a regi_vege kell legyen (uj kezdete -1 nap)'''
                            eladott_eloiras.write({'eloir_vege': regi_vege})
                            '''Ezután létrehozunk egy új előírást az eladott ingatlanra, a kezdete a most bevitt előírás
                            kezdete, vége pedig az albetét eladása lesz'''
                            osszeg = 0
                            if _terulet_aranyos:
                                negyzetmeter = eladott_ingatlan.alapterulet
                                osszeg = _osszeg * negyzetmeter
                            elif _tulhanyad_aranyos:
                                tulhanyad = eladott_ingatlan.tulhanyad
                                osszeg = _osszeg * tulhanyad
                            elif _legm_aranyos:
                                legm3 = eladott_ingatlan.legm3
                                osszeg = _osszeg * legm3
                            elif _lakoszam_aranyos:
                                lakoszam = eladott_ingatlan.lakoszam
                                osszeg = _osszeg * lakoszam
                            else:
                                osszeg = _osszeg
                            sikeres = _tarh_eloiras_lako.create({
                                'esedekes': _esedekes,
                                'lako': eladott_ingatlan.id,
                                'tarsashaz': _konyvelt_haz,
                                'eloirfajta': _eloirfajta,
                                'osszeg': osszeg,
                                'eloir_kezd': _eloir_kezd,
                                'eloir_vege': eladott_ingatlan.alb_eladas
                            })
                        pass


        # idáig tart a volt már ilyen előírás, ide jön az else ág amire akkor futunk, ha olyan előírást készítünk,
        # ami még nem volt a házban
        else:
            '''megkeressük azokat az ingatlanokat, amelyek aktívak, vagy az albetét eladása későbbi, 
            mint az előírás kezdete, és az albetét száma nagyobb mint nulla (nem bérlemény)'''
            aktiv_ingatlanok = _res_partner.search([('parent_id','=',_konyvelt_haz),
                                                    ('alb_szam','>',0)])
            eladott_ingatlanok = _res_partner.search([('parent_id','=',_konyvelt_haz),
                                                      ('active','=',False),
                                                      ('alb_eladas', '>', _eloir_kezd)])
            eloiras_neve = _eloiras_fajta_hiv.search([('id','=',_eloirfajta)]).name
            '''elkezdjük szétválogatni az előírásokat'''
            if "Csekkes" in eloiras_neve:
                print 'csekkes!'
                '''megkeressük a tarh_bankbiz_sor-ban azokat, amelyeknek az erteknap nagyobb mint az előírás kezdete,
                 bankbiz_id.th_szamlatul egyenlő a _konyvelt_haz -zal                 
                '''
                bankbiz_sorok = _tarh_bankbiz_sor.search([
                    ('bankbiz_id.th_szamlatul.id','=',_konyvelt_haz),
                    ('postai','=',True),
                    ('erteknap','>=',_eloir_kezd),
                    ('erteknap','<=',_eloir_vege)
                ])
                '''a megtalált sorok alapján a gazdáknak előírjuk az erteknap dátumra az előírásbasn szereplő 
                csekkes költséget'''
                for bankbiz_sor in bankbiz_sorok:
                    lako_egyszeri_eloiras(self,_konyvelt_haz, bankbiz_sor.partner.id, _osszeg, bankbiz_sor.erteknap, csekkes_eloir_fajta_id)
                    pass


            elif 'vízórával' in eloiras_neve:
                print 'közös költség vízórával'
            elif 'endkívüli' in eloiras_neve:
                ingatlanok = aktiv_ingatlanok + eladott_ingatlanok
                for ingatlan in ingatlanok:
                    osszeg=0
                    if ingatlan.vizora == 'v':
                        vizoras = True
                    else:
                        vizoras = False
                    alapterulet = ingatlan.alapterulet
                    if _terulet_aranyos:
                        osszeg = _osszeg * alapterulet
                    elif _tulhanyad_aranyos:
                        osszeg = _osszeg * ingatlan.tulhanyad
                    elif _lakoszam_aranyos:
                        osszeg = _osszeg * ingatlan.lakoszam
                    elif _legm_aranyos:
                        osszeg = _osszeg * ingatlan.legm3
                    else:
                        raise exceptions.ValidationError(("nincs megadva mi alapján számítódik a költség m2, légm3, lakószám stb!"))
                    sikeres = _tarh_eloiras_lako.create({
                        'esedekes': _esedekes,
                        'lako': ingatlan.id,
                        'tarsashaz': _konyvelt_haz,
                        'eloirfajta': _eloirfajta,
                        'eloir_kezd': _eloir_kezd,
                        'eloir_vege': _eloir_vege,
                        'osszeg': osszeg,
                        'alapterulet': alapterulet,
                        'vizora': vizoras
                    })
            else:
                print 'egyik sem, HIBA!!!'
            pass

        res = super(tarh_eloiras_haz, self).create(vals)  # meghívjuk az eredeti create eljárást
        #res = False
        return res
