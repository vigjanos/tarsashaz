# -*- coding: ISO-8859-2 -*-
'''
Created on 2015.02.13.

@author: vigjani
'''

from openerp.osv import osv, fields
from datetime import date, timedelta


class tarh_kozoskt_lekerdez(osv.osv):
    _name = "tarh.kozoskt.lekerdez"
    _columns = {
        'eloir_datum' : fields.date('Eloiras datum', required=True, ),
        'tarsashaz' : fields.many2one('res.partner', 'Tarsashaz', required=True, ),
        'tulaj_id' : fields.one2many('tarh.kozoskt.lekerdez.tulaj', 'tarsashaz_id', 'kapocs2', required=False, ),
        'bankszamla':fields.char('Bankszamla', size=80),
        'bank':fields.char('Bank', size=32),
        }

    def onchange_tarsashaz(self,cr,uid,ids,tarsashaz,context=None):
        eredmeny={}
        _res_partner_bank=self.pool.get('res.partner.bank')
        bankszamla_list=_res_partner_bank.search(cr,uid,[('partner_id','=',tarsashaz),('state','ilike','uzem')],context=None)
        if bankszamla_list:
            bankszamla_ref=_res_partner_bank.browse(cr,uid,bankszamla_list[0],context=None)
            bankszamla=bankszamla_ref.acc_number
            bank=bankszamla_ref.bank_name
            eredmeny['bankszamla']=bankszamla
            eredmeny['bank']=bank

        return {'value': eredmeny}

    def lekerdez(self,cr,uid,ids,context=None):
        sajat_id=self.browse(cr, uid, ids, context=None).id
        eloir_datum=self.browse(cr, uid, ids, context=None).eloir_datum
        szeletelt=eloir_datum.split("-")
        ev=int(szeletelt[0])
        honap=int(szeletelt[1])
        honap2=honap
        ev2=ev

        #honap utolsonapja
        if honap2==12:
            honap2=1
            ev2=ev2+1
        else:
            honap2=honap2+1
        nap=1
        ujdatum=date(ev2,honap2,nap)

        ujdatum=ujdatum-timedelta(days=1)
        utsonap=str(ujdatum)

        tarsashaz=self.browse(cr, uid, ids, context=None).tarsashaz.id
        _res_partner=self.pool.get('res.partner')
        _tarh_kozoskt_lekerdez_tulaj=self.pool.get('tarh.kozoskt.lekerdez.tulaj')
        _tarh_kozoskt_lekerdez_tulaj_eloiras=self.pool.get('tarh.kozoskt.lekerdez.tulaj.eloiras')
        _tarh_lakoeloir_havi=self.pool.get('tarh.lakoeloir.havi')



        '''
        Töröljük az ehhez a sajat_id-hez tartozó bejegyzéseket a tarh_kozoskt_lekerdez_tulaj és a
        tarh_kozoskt_lekerdez_tulaj_eloiras táblából (a felhasználó rányomott a lekérdez gombra mégegyszer)
        '''
        torlendo1=_tarh_kozoskt_lekerdez_tulaj.search(cr,uid,[('tarsashaz_id','=',sajat_id)],context=None)
        _tarh_kozoskt_lekerdez_tulaj.unlink(cr,uid,torlendo1,context=None)

        torlendo2=_tarh_kozoskt_lekerdez_tulaj_eloiras.search(cr,uid,[('seged_id','=',sajat_id)],context=None)
        _tarh_kozoskt_lekerdez_tulaj_eloiras.unlink(cr,uid,torlendo2,context=None)
        '''
        megkeressük azokat a lakokat, akik a lekérdezés pillanatában tulajdonosok: nem adták el korábban a lakást.
        '''
        eladottak=_res_partner.search(cr,uid,[('parent_id','=',tarsashaz),('alb_eladas','<',ujdatum)],context=None)
        tulajdonosok=_res_partner.search(cr,uid,[('parent_id','=',tarsashaz)],context=None)

        for eladva in eladottak:
            tulajdonosok.remove(eladva) #eltavolitjuk a a tulajdonosok listajabol az eladottakat

        for tulaj in tulajdonosok:
            kiirando={}
            kiirando['tulajdonos']=tulaj
            kiirando['tarsashaz_id']=sajat_id
            tul_id=_tarh_kozoskt_lekerdez_tulaj.create(cr,uid,kiirando,context=None)
            eloirasok=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',tulaj),('ev','=',ev),('honap','=',honap)],context=None)
            if tul_id:
                for eloiras in eloirasok:
                    kiirando2={}
                    konkr_eloiras=_tarh_lakoeloir_havi.browse(cr,uid,eloiras,context=None)
                    kiirando2['eloiras']=konkr_eloiras.eloirfajta.id
                    kiirando2['osszeg']=konkr_eloiras.osszeg
                    kiirando2['tul_id']=tul_id
                    kiirando2['seged_id']=sajat_id # ez csak azert kell, hogy majd torolni tudjuk a sajat_id-hez tartozo rekordokat
                    _tarh_kozoskt_lekerdez_tulaj_eloiras.create(cr,uid,kiirando2,context=None)
        return ()

tarh_kozoskt_lekerdez()


class tarh_kozoskt_lekerdez_tulaj(osv.osv):
    _name = "tarh.kozoskt.lekerdez.tulaj"
    _columns = {
        'tulajdonos' : fields.many2one('res.partner', 'Tulajdonos', required=False, ),
        'tarsashaz_id' : fields.many2one('tarh.kozoskt.lekerdez', 'kapocs', required=False, ondelete='cascade', select=True, ),
        'eloiras_id' : fields.one2many('tarh.kozoskt.lekerdez.tulaj.eloiras', 'tul_id', 'kapocs4', required=False, ),
        }
tarh_kozoskt_lekerdez_tulaj()

class tarh_kozoskt_lekerdez_tulaj_eloiras(osv.osv):
    _name = "tarh.kozoskt.lekerdez.tulaj.eloiras"
    _columns = {
        'eloiras' : fields.many2one('eloiras.fajta', 'Eloiras fajta', required=False, ),
        'osszeg':fields.integer('Fizetendo osszeg'),
        'tul_id' : fields.many2one('tarh.kozoskt.lekerdez.tulaj','kapocs3', required=False, ondelete='cascade', select=True, ),
        'seged_id': fields.integer('Seged valtozo'),
    }
tarh_kozoskt_lekerdez_tulaj_eloiras()