# -*- coding: ISO-8859-2 -*-
'''
Created on 2015.04.20.

@author: vigjani
'''


from openerp.osv import osv, fields
from datetime import date, timedelta



class tarh_rendkivuli_lekerdez(osv.osv):
    _name = 'tarh.rendkivuli.lekerdez'
    _description = 'rendkivuli lekerdezese'

    _columns = {
        'kezddatum': fields.date('Kezdo datum', help='Indulo datum'),
        'vegdatum': fields.date('Veg datum', help='Veg datum'),
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz'),
        'sor_ids': fields.one2many('tarh.rendkivuli.lekerdez.sor', 'lekerdezes_id', 'kapcs2'),

    }
    def lekerdez(self,cr,uid,ids,context=None):
        sajat_id=self.browse(cr, uid, ids, context=None).id
        kezdo_datum=self.browse(cr, uid, ids, context=None).kezddatum
        veg_datum=self.browse(cr, uid, ids, context=None).vegdatum
        tarsashaz=self.browse(cr, uid, ids, context=None).tarsashaz.id


        szeletelt_kezdo=kezdo_datum.split("-")
        ev_kezd=int(szeletelt_kezdo[0])
        ho_kezd=int(szeletelt_kezdo[1])
        nap_kezd=int(szeletelt_kezdo[2])
        kezdo_date=date(ev_kezd,ho_kezd,nap_kezd)

        szeletelt_veg=veg_datum.split("-")
        ev_veg=int(szeletelt_veg[0])
        ho_veg=int(szeletelt_veg[1])
        nap_veg=int(szeletelt_veg[2])
        veg_date=date(ev_veg,ho_veg,nap_veg)

        _res_partner=self.pool.get('res.partner')
        _tarh_lakoeloir_havi=self.pool.get('tarh.lakoeloir.havi')
        _tarh_rendkivuli_lekerdez_sor=self.pool.get('tarh.rendkivuli.lekerdez.sor')
        _my_report=self.pool.get('my.report')

        '''
        Töröljük az ehhez a sajat_id-hez tartozó bejegyzéseket a tarh_rendkivuli_lekerdez_sor
        táblából (a felhasználó rányomott a lekérdez gombra mégegyszer)
        '''
        torlendo1=_tarh_rendkivuli_lekerdez_sor.search(cr,uid,[('lekerdezes_id','=',sajat_id)],context=None)
        _tarh_rendkivuli_lekerdez_sor.unlink(cr,uid,torlendo1,context=None)

        '''Megkeressük a tulajdonosok listáját, akik a házban laknak'''

        tulajdonosok=_res_partner.search(cr,uid,[('parent_id','=',tarsashaz)],order='alb_szam' ,context=None)

        '''Végiglépkedünk a tulajokon, a kezdő- és végidőpontok között, egy-egy változóban összegyűjtjük a rendkívüli
        előírásokat, és a befizetéseket'''

        for tulaj in tulajdonosok:
            ossz_eloir=0
            ossz_befiz=0
            alb_szam=_res_partner.browse(cr, uid, tulaj,context=None).alb_szam
            eloirasok=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',tulaj),('eloir_datum','<=',veg_date),
                                                          ('eloir_datum','>=',kezdo_date),('eloirfajta.name','ilike','rendk%befiz')]
                                                  ,context=None)

            befizetesek=_my_report.search(cr,uid,[('partner','=',tulaj),('erteknap','<=',veg_date),
                                                          ('erteknap','>=',kezdo_date),('tarh_tranzakcio.name','ilike','rendk%befiz')],context=None)


            if eloirasok:
                kiirando={}
                for eloiras in eloirasok:
                    ossz_eloir = ossz_eloir + _tarh_lakoeloir_havi.browse(cr,uid,eloiras,context=None).osszeg
                if befizetesek:
                    for befizetes in befizetesek:
                        ossz_befiz = ossz_befiz + _my_report.browse(cr,uid,befizetes,context=None).jovairas - _my_report.browse(cr,uid,befizetes,context=None).terheles
                kiirando['alb_szam']=alb_szam
                kiirando['tulajdonos']=tulaj
                kiirando['eloiras']=ossz_eloir
                kiirando['befizetes']=ossz_befiz
                kiirando['egyenleg']=ossz_befiz-ossz_eloir
                kiirando['lekerdezes_id']=sajat_id
                _tarh_rendkivuli_lekerdez_sor.create(cr,uid,kiirando,context=None)
        return()

tarh_rendkivuli_lekerdez()


class tarh_rendkivuli_lekerdez_sor(osv.osv):
    _name = 'tarh.rendkivuli.lekerdez.sor'
    _columns = {
        'alb_szam': fields.integer('Albetet szama'),
        'tulajdonos': fields.many2one('res.partner', 'Tulajdonos'),
        'eloiras': fields.integer('Eloiras'),
        'befizetes': fields.integer('Befizetes'),
        'egyenleg': fields.integer('Egyenleg'),
        'lekerdezes_id': fields.many2one('tarh.rendkivuli.lekerdez', 'kapcs1',required=False, ondelete='cascade', select=True,),

    }


tarh_rendkivuli_lekerdez_sor()




