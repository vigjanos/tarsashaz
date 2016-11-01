# -*- coding: ISO-8859-2 -*-
'''
Created on 2015.12.31.
@author: vigjani
'''

from openerp.osv import osv, fields
import seged


class tarh_lako_eves(osv.osv):
    _name = "tarh.lako.eves"
    _columns = {
        'kezdatum': fields.date('Kezdo datum', required=True, ),
        'vegdatum': fields.date('Zaro datum', required=True, ),
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz', required=True, ),
        'bank':fields.char('Bank', size=64),
        'tulaj_id': fields.one2many('tarh.lako.eves.tulaj', 'tarsashaz_id', 'kapocs2', required=False, ),
    }
    _defaults = {
        'kezdatum':'2015-01-01',
        'vegdatum':'2015-12-31',
    }

    def onchange_tarsashaz(self,cr,uid,ids,tarsashaz,context=None):
        eredmeny={}
        _res_partner_bank=self.pool.get('res.partner.bank')
        bankszamla_list=_res_partner_bank.search(cr,uid,[('partner_id','=',tarsashaz),('state','ilike','uzem')],context=None)
        if bankszamla_list:
            bankszamla_ref=_res_partner_bank.browse(cr,uid,bankszamla_list[0],context=None)
            bank=bankszamla_ref.bank_name
            eredmeny['bank']=bank

        return {'value': eredmeny}

    def lekerdez (self, cr, uid, ids, context=None):
        '''
        Ez az eljárás végzi az adattáblákba való beírást, a beállított társasháznál a beállított időszakban a megfelelő
        táblákba beírja a nyitóegyenlegeket, az előírásokat típusonként összegezve, valamint az időszak alatti
        befizetéseket.
        '''
        sajat_id = self.browse(cr, uid, ids, context=None).id
        kezdatum = self.browse(cr, uid, ids, context=None).kezdatum
        vegdatum = self.browse(cr, uid, ids, context=None).vegdatum
        tarsashaz = self.browse(cr, uid, ids, context=None).tarsashaz.id
        ref_lako_eves_tulaj = self.pool.get('tarh.lako.eves.tulaj')
        ref_lako_eves_tulaj_sor = self.pool.get('tarh.lako.eves.tulaj.sor')
        ref_tarh_lako_nyito = self.pool.get('tarh.lako.nyito')
        ref_my_report = self.pool.get('my.report')
        ref_tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')

        torlendo1 = ref_lako_eves_tulaj.search(cr, uid, [('tarsashaz_id', '=', sajat_id)], context=None)
        ref_lako_eves_tulaj.unlink(cr, uid, torlendo1, context=None)
        tulajdonosok = seged.lakolista(self, cr, uid, vegdatum, tarsashaz)
        for tulajdonos in tulajdonosok:
            kiirando = {}
            kiirando['tulajdonos'] = tulajdonos
            kiirando['tarsashaz_id'] = sajat_id
            tul_id = ref_lako_eves_tulaj.create(cr, uid, kiirando, context=None)
            if ref_tarh_lako_nyito.search(cr, uid, [('tarh_lako', '=', tulajdonos)],context=None) :

                tul_nyito = ref_tarh_lako_nyito.browse(cr, uid,
                                                       ref_tarh_lako_nyito.search(cr, uid, [('tarh_lako', '=', tulajdonos)],
                                                                                  context=None)[0], context=None)
                nyitorekord = {}
                if tul_nyito.egyenleg_datuma < vegdatum and tul_nyito.egyenleg_datuma > kezdatum:
                    nyitorekord['datum'] = tul_nyito.egyenleg_datuma
                else:
                    nyitorekord['datum'] = kezdatum
                # ha az időszak alatt vette a tulajdont, akkor a nyitóegyenleg dátumat rögzitjük, egyébkent az időszak
                # kezdetét
                nyitoegyenleg = seged.lakoegyenleg(self, cr, uid, tulajdonos, seged.str_to_date(kezdatum))[0]
                nyitorekord['eloiras_e'] = False
                nyitorekord['szoveg'] = 'Nyitóegyenleg:'
                nyitorekord['osszeg'] = nyitoegyenleg
                nyitorekord['tul_id'] = tul_id
                ref_lako_eves_tulaj_sor.create(cr, uid, nyitorekord, context=None)

                # idáig a nyítórekord, nézzük az időszak alatti összes előírásokat!

                #kotelezettsegek = seged.eloirasok2(self, cr, uid, tulajdonos, kezdatum, vegdatum)
                kotelezettsegek = seged.eloirasok(self, cr, uid, tulajdonos, kezdatum, vegdatum)
                for kotelezettseg in kotelezettsegek:
                    beirando = {}
                    beirando['eloiras_e'] = True
                    beirando['kdatum'] = '1900-01-01'
                    beirando['datum'] = vegdatum
                    beirando['szoveg'] = kotelezettseg[0]
                    beirando['osszeg'] = kotelezettseg[1]
                    beirando['tul_id'] = tul_id
                    ref_lako_eves_tulaj_sor.create(cr, uid, beirando, context=None)
            else:
                    print tulajdonos


            # rögzítettük az előírásokat fajtánként, most a befizetéseket keressük meg dátum és fajta szerint

            my_report_lista = ref_my_report.search(cr, uid, [('partner', '=', tulajdonos), ('erteknap', '>', kezdatum),
                                                      ('erteknap', '<=', vegdatum)], order='erteknap', context=None)
            befizetesek = ref_my_report.browse(cr,uid,my_report_lista,context=None)
            for befizetes in befizetesek:
                eredmeny={}
                eredmeny['eloiras_e'] = False
                eredmeny['datum'] = befizetes.erteknap
                eredmeny['szoveg'] = befizetes.tarh_tranzakcio.name
                eredmeny['osszeg'] = befizetes.jovairas - befizetes.terheles
                eredmeny['tul_id'] = tul_id
                ref_lako_eves_tulaj_sor.create(cr, uid, eredmeny, context=None)

            # rögzítsük, hogy mennyi volt a havonta fizetendő előírás
            eloir_idk = ref_tarh_eloiras_lako.search(cr,uid,[('lako','=',tulajdonos)],context=None)
            eloirasok=ref_tarh_eloiras_lako.browse(cr,uid,eloir_idk,context=None)
            for eloiras in eloirasok:
                if (eloiras.eloir_kezd < kezdatum < eloiras.eloir_vege) or (eloiras.eloir_kezd < vegdatum < eloiras.eloir_vege)\
                        or (kezdatum < eloiras.eloir_kezd < vegdatum ) or (kezdatum < eloiras.eloir_vege < vegdatum):
                    eredmeny={}
                    eredmeny['eloiras_e'] = True
                    eredmeny['kdatum'] = eloiras.eloir_kezd
                    eredmeny['datum'] = eloiras.eloir_vege
                    eredmeny['szoveg'] = eloiras.eloirfajta.name
                    eredmeny['osszeg'] = eloiras.osszeg
                    eredmeny['tul_id'] = tul_id
                    ref_lako_eves_tulaj_sor.create(cr, uid, eredmeny, context=None)

        return # lekerdez visszatérése

tarh_lako_eves()


class tarh_lako_eves_tulaj(osv.osv):
    _name = "tarh.lako.eves.tulaj"
    _columns = {
        'tulajdonos': fields.many2one('res.partner', 'Tulajdonos'),
        'tarsashaz_id': fields.many2one('tarh.lako.eves', 'kapocs', required=False, ondelete='cascade', select=True, ),
        'eloiras_id': fields.one2many('tarh.lako.eves.tulaj.sor', 'tul_id', 'kapocs4', required=False, ),
    }

tarh_lako_eves_tulaj()


class tarh_lako_eves_tulaj_sor(osv.osv):
    _name = "tarh.lako.eves.tulaj.sor"
    _columns = {
        'eloiras_e': fields.boolean(),
        'kdatum': fields.date('Datum', ),
        'datum': fields.date('Datum', ),
        'szoveg': fields.char('Szoveg'),
        'osszeg': fields.integer('Osszeg'),
        'tul_id': fields.many2one('tarh.lako.eves.tulaj', 'kapocs3', required=False, ondelete='cascade', select=True, ),
        'seged_id': fields.integer('Seged valtozo'),
    }

tarh_lako_eves_tulaj_sor()
