# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.12.26..
 Boldog karajcsont!
''' 

from openerp import models, fields, api
from seged3 import str_to_date, honap_utolsonap
from datetime import date, timedelta


class tarh_eloiras_haz(models.Model):
    _inherit = 'tarh.eloiras.haz'

    @api.model
    def create (self, vals):

        '''Be kell olvasni a változókat a lapról'''
        _eloir_kezd = str_to_date(vals['eloir_kezd'])
        _eloir_vege = str_to_date(vals['eloir_vege'])
        _eloirfajta = vals['eloirfajta']
        _esedekes = vals['esedekes']
        _konyvelt_haz = vals['konyvelt_haz']
        _osszeg = vals['osszeg']
        _rendszeres = vals['rendszeres']
        _terulet_aranyos = vals['terulet_aranyos']
        regi_vege = _eloir_kezd - timedelta(days=1)  # az új kezdete - 1 nap lesz a régi vége

        _tarh_eloiras_haz = self.env['tarh.eloiras.haz']
        _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
        _res_partner = self.env['res.partner']

        print "beolvasás vége!"
        '''
        Meg kell nézni, hogy van-e már ilyen előírás, mert akkor
            1./ át kell állítani a régi ház-előírás végét a mostani kezdete -1 nap
            2./ meg kell keresni a tulajdonosokat, akiknek ennek az előírásnak a záródátuma 2050-12-31,
            2./a. azt is keresni kell, hogy az eladás dátuma későbbi-e mint az új előírás kezdete 
            3./ a talált tulajdonosok előírásainak záródátumát változtatni kell a mostani kezdő -1 nap
        Ha volt, ha nem volt még ilyen előírás  
            1./ Elő kell írni a tulajdonosok részére az új ház-előírást.'''

        van_eloiras = _tarh_eloiras_haz.search([('konyvelt_haz','=',_konyvelt_haz),
                                                ('eloirfajta','=',_eloirfajta),
                                                ('eloir_vege','=',_eloir_vege)])
        if len(van_eloiras) > 1:
            print 'Hiba van, több mint egy!!!! ide kell dobni egy excepsönt!'
        if van_eloiras:

            sikerult = van_eloiras[0].write({'eloir_vege':regi_vege})
            if not sikerult:
                print 'Ide kell egy excepsön, hogy félrement az írás!'
            '''Idáig tartott az 1./ jön a 2./'''


            tulajok_regi_eloirasai = _tarh_eloiras_lako.search([('eloir_vege','=',_eloir_vege),
                                                                ('eloirfajta','=', _eloirfajta),
                                                                ('tarsashaz','=',_konyvelt_haz)])
            '''most jön a 3./'''
            if tulajok_regi_eloirasai:
                for uj_eloiras in tulajok_regi_eloirasai:
                    uj_eloiras.write({'eloir_vege':regi_vege})
                    print 'átírtam ', regi_vege, 'értékre'
            '''2./a. megnézzük, hogy nem esik-e a változtatott időszakba lakás eladás'''
            eladott_ingatlanok = _res_partner.search([('parent_id','=',_konyvelt_haz),
                                                      ('alb_eladas','>',_eloir_kezd),
                                                      '|', ('active', '=', True), ('active', '=', False)])
            '''keressük, hogy ezek között volt-e olyan amelynek volt eloirfajta előírása'''
            if eladott_ingatlanok:
                for eladott_ingatlan in eladott_ingatlanok:
                    van_eladottak_kozt = _tarh_eloiras_lako.search([('lako','=',eladott_ingatlan.id),
                                                                    ('eloirfajta','=',_eloirfajta),
                                                                    ('eloir_vege','=',eladott_ingatlan.alb_eladas)])
                    '''Van az eladottak között amit korrigálni kell'''
                    if van_eladottak_kozt:
                        for eladott_eloiras in van_eladottak_kozt:
                            '''ezt az előírást módosítani kell, az eloir_vege a regi_vege kell legyen (uj kezdete -1 nap)'''
                            print eladott_eloiras.lako.name,'  ',eladott_eloiras.eloir_vege, '   ', eladott_eloiras.eloirfajta.name
                            print 'vége'
                        pass




        #res = super(tarh_eloiras_haz, self).create(vals)  # meghívjuk az eredeti create eljárást
        res = False

        return res