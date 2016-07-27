# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2016.02.08..
'''

from openerp.osv import fields, osv


class tarh_bankbiz(osv.osv):
    _inherit = 'tarh.bankbiz'

    def belso_penzmozgas (self, cr, uid, ids, context=None):
        '''
        Itt figyeljük, hogy a társasház számlái között történt-e pénzmozgás.
        Ehhez az éppen rögzített bankbizonylat adatait beolvassuk, majd megnézzük, hogy van-e olyan sor, ahol a
        társasház és a partner ugyanaz, és a tranzakció pedig valamilyen belső pénzmozgás
        '''
        bankbiz_obj = self.pool.get('tarh.bankbiz')
        bankbiz_sor_obj = self.pool.get('tarh.bankbiz.sor')
        sajat_id = ids[0]
        sorok_lista = bankbiz_sor_obj.search(cr, uid, [('bankbiz_id', '=', sajat_id)])
        bankbiz = bankbiz_obj.browse(cr, uid, sajat_id, context=None)[0]
        tarsashaz_id = bankbiz.th_szamlatul.id
        bankszamla_id = bankbiz.bankszamla_thaz.id
        bank_kod = bankbiz.bankszamla_thaz.state
        kivonatszam = bankbiz.kivonatszam
        erk_datum = bankbiz.erk_datum
        sorok = bankbiz_sor_obj.browse(cr, uid, sorok_lista, context=None)
        for sor in sorok:
            partner_id = sor.partner.id
            erteknap = sor.erteknap
            tranzakcio_nev = sor.tarh_tranzakcio.name
            partner_bank_id = sor.partner_banksz.id
            terheles = sor.terheles_ossz
            jovairas = sor.jovairas_ossz
            '''
            Amennyiben belső pénzmozgásról van szó, megegyezik a főlapon és a soron a társasház és a partner, valamint
            az üzemeltetési számlát könyveljük
            '''
            if ('Belső pénzmozgás').decode(
                    ('UTF-8')) in tranzakcio_nev and tarsashaz_id == partner_id and bank_kod == 'bank_uzem':
                '''
                Először megnézzük, hogy a sor értéknapjára van-e már létrehozva olyan bankbizonylat ahol a sor bankja
                megegyezik a bankbizonylat bankszámlájával és a kivonatszámmal
                '''
                van_mar_bizonylat = bankbiz_obj.search(cr, uid, [('erk_datum', '=', erteknap),
                                                           ('bankszamla_thaz', '=', partner_bank_id),('kivonatszam','=',kivonatszam)], context=None)
                if van_mar_bizonylat:
                    '''
                    Van már erre a napra bizonylat,megnézzük, hogy a sor is rögzítve van-e
                    '''
                    van_mar_sor = bankbiz_sor_obj.search(cr,uid,[('bankbiz_id','=',van_mar_bizonylat[0] )],context=None)
                    if van_mar_sor:
                        '''
                        Van már ilyen sor rögzítve, akkor végiglépkedünk a sorokon, és megnézzük, hogy az eredeti bejegyzésnek
                        megfelelő sor van-e már
                        '''
                        for ujsor in van_mar_sor:
                            van_mi_sorunk=bankbiz_sor_obj.browse(cr,uid,ujsor,context=None)[0]
                            a = van_mi_sorunk.partner_banksz
                            b = van_mi_sorunk.tarh_tranzakcio.name
                            c = van_mi_sorunk.terheles_ossz
                            d = van_mi_sorunk.jovairas_ossz
                            if van_mi_sorunk.partner_banksz.id == bankszamla_id and (c == jovairas or d == terheles):
                                print 'egyezik!!!'
                                pass

        pass

        return


tarh_bankbiz()
