# -*- coding: utf-8 -*-
'''
Created on 2015.10.15'''

__author__ = 'vigjani'

from openerp.osv import osv, fields
from datetime import date, timedelta
from seged import str_to_date



class portal_user_havijel(osv.osv):
    _name='portal.user.havijel'
    _columns = {
        'tulaj':fields.many2one('res.partner', 'Tulajdonos',default=lambda self: self.env.user.partner_id, readonly=True ),
        'kezdatum':fields.date('Kezdo datum', required=True),
        'vegdatum':fields.date('Befejezo datum', required=True),
        'tarsashaz':fields.many2one('res.partner', 'Tarsashaz'),
        'bankszamla':fields.char('Tarsahaz uzemeltetesi szamlaja'),
        'sor_id':fields.one2many('portal.user.havijel.sor','havijel_id','kapocs2'),
                }
    _defaults = {
    'kezdatum':'2015-01-01',
    'vegdatum':fields.date.context_today


                }

    def onchange_tul(self,cr, uid, ids, context=None):
        eredmeny={}
        _res_partner=self.pool.get('res.partner')
        tulaj=self.pool.get('res.users').browse(cr,uid,uid,context=None).partner_id.id
        tarsashaz=_res_partner.browse(cr,uid,tulaj,context=None).parent_id
        if tarsashaz:
            eredmeny['tarsashaz']=tarsashaz
        return {'value':eredmeny}



    def onchange_tarsashaz(self,cr,uid,ids,tarsashaz, context=None):
        eredmeny={}
        if tarsashaz:
            uzemeltetesi=self.pool.get('res.partner.bank').search(cr,uid,[('partner_id','=',tarsashaz),
                                                                          ('state','=','bank_uzem')],context=None)

            if uzemeltetesi:
                if uzemeltetesi[0]:
                    eredmeny['bankszamla']=self.pool.get('res.partner.bank').browse(cr,uid,
                                                                        uzemeltetesi[0],context=None).acc_number
        return {'value': eredmeny}



    def lekerdezes(self,cr,uid,ids,context=None):#ez tesszuk majd a gombra,ami indittya

        '''Beolvassuk az adatokat a lapról '''
        _kezdatum=str_to_date(self.browse(cr,uid,ids,context=None).kezdatum)#lekerdezes kezdete
        _vegdatum=str_to_date(self.browse(cr,uid,ids,context=None).vegdatum)#lekerdezes vege
        _tarsashaz=self.browse(cr,uid,ids,context=None).tarsashaz.id
        _tulaj=self.browse(cr,uid,ids,context=None).tulaj.id
        #_tulaj=205
        _sajat_id=self.browse(cr, uid, ids, context=None).id


        def nyitoegyenleg(self,_lako,datum):
            sum_eloiras=0
            sum_jovairas=0
            _tarh_lako_nyito=self.pool.get('tarh.lako.nyito')
            talalt_id=_tarh_lako_nyito.search(cr,uid,[('tarh_lako','=',_lako)],context=context)
            if talalt_id: # ha van nyitoegyenleg rogzitve
                nyito_dok=_tarh_lako_nyito.browse(cr,uid,talalt_id[0],context=None)
                _nyito_datum=nyito_dok.egyenleg_datuma
                _nyito_osszeg=nyito_dok.egyenleg
                #modositani kell majd, hogy a tarolt nyitoegyenleg es a lekerdezes kozotti eloirast-befizetest figyelembe vegye
                _tarh_lakoeloir_havi=self.pool.get('tarh.lakoeloir.havi')
                _my_report=self.pool.get('my.report')
                tarh_lakoeloir_havi_lista=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',_lako),('eloir_datum','>',_nyito_datum),('eloir_datum','<=',datum)],context=context) #datum szures kell bele!
                my_report_lista=_my_report.search(cr,uid,[('partner','=',_lako),('erteknap','>',_nyito_datum),('erteknap','<=',datum)],context=context) #datum szures kell bele!
                eloirasok=_tarh_lakoeloir_havi.browse(cr,uid,tarh_lakoeloir_havi_lista, context=None)
                befizetesek=_my_report.browse(cr,uid,my_report_lista,context=None)
                for befizetes in befizetesek:
                    _nyito_osszeg= _nyito_osszeg+befizetes.jovairas-befizetes.terheles
                for eloiras in eloirasok:
                    _nyito_osszeg= _nyito_osszeg-eloiras.osszeg
                #ha a kejerdezesi datum korabbi mint a nyitoegyenleg datuma, akkor a kezdeti datum a nyitoegyenleg datuma lesz
                _nyito_datum_date=str_to_date(_nyito_datum)
                if datum < _nyito_datum_date:
                    datum=_nyito_datum_date
                eredmeny=[datum,_nyito_osszeg,'']
            else: # nincs nyitoegyenleg rögzitve
                eredmeny=[datum,0,'Nincs a lakóhoz nyitóegyenleg rögzítve!!!']
            return(eredmeny)



        nyitoegy=nyitoegyenleg(self,_tulaj,_kezdatum)
        _havijel_sor_hiv=self.pool.get('portal.user.havijel.sor')
        torleno_sorok=_havijel_sor_hiv.search(cr,uid,[('havijel_id','=',_sajat_id)],context=None)
        _havijel_sor_hiv.unlink(cr,uid,torleno_sorok,context=None)


        kiirando={}

        if len(nyitoegy[2]) == 0: # nincs szoveg ,tehat volt nyitoegyenleg!
            kiirando['erteknap'] = nyitoegy[0]
            kiirando['szoveg']= 'Nyitóegyenleg'
            kiirando['eloiras']= 0
            kiirando['befizetes']= nyitoegy[1]
            kiirando['havijel_id'] = _sajat_id
            id_je=_havijel_sor_hiv.create(cr,uid,kiirando,context=None)

        else:
            kiirando['erteknap'] = nyitoegy[0]
            kiirando['szoveg']= nyitoegy[2]
            kiirando['eloiras']= 0
            kiirando['befizetes']= nyitoegy[1]
            kiirando['havijel_id'] = _sajat_id
            id_je=_havijel_sor_hiv.create(cr,uid,kiirando,context=None)
        #ha a lekerdezes bejezesi kisebb mint a nyitoegyenleg datuma akkor nincs ertekelheto adat

        if _vegdatum >= nyitoegy[0]:
            _tarh_lakoeloir_havi=self.pool.get('tarh.lakoeloir.havi')
            _my_report=self.pool.get('my.report')
            tarh_lakoeloir_havi_lista=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',_tulaj),('eloir_datum','>',_kezdatum),('eloir_datum','<=',_vegdatum),('eloir_datum','>',nyitoegy[0])],context=context)
            my_report_lista=_my_report.search(cr,uid,[('partner','=',_tulaj),('erteknap','>',_kezdatum),('erteknap','<=',_vegdatum)],context=context)
            eloirasok=_tarh_lakoeloir_havi.browse(cr,uid,tarh_lakoeloir_havi_lista, context=None)
            befizetesek=_my_report.browse(cr,uid,my_report_lista,context=None)
            szumma=nyitoegy[1]

            for befizetes in befizetesek:
                #print befizetes.erteknap,' ',befizetes.tarh_tranzakcio.name,' ',befizetes.jovairas
                kiirando['erteknap'] = befizetes.erteknap
                kiirando['szoveg']= befizetes.tarh_tranzakcio.name
                kiirando['eloiras']= befizetes.terheles
                kiirando['befizetes']= befizetes.jovairas
                kiirando['havijel_id'] = _sajat_id
                szumma = szumma + befizetes.jovairas - befizetes.terheles
                id_je=_havijel_sor_hiv.create(cr,uid,kiirando,context=None)
            for eloiras in eloirasok:
                #print eloiras.eloir_datum,' ',eloiras.eloirfajta.name,' ', eloiras.osszeg
                kiirando['erteknap'] = eloiras.eloir_datum
                kiirando['szoveg']= eloiras.eloirfajta.name
                kiirando['eloiras']= eloiras.osszeg
                kiirando['befizetes']= 0
                kiirando['havijel_id'] = _sajat_id
                szumma = szumma - eloiras.osszeg
                id_je=_havijel_sor_hiv.create(cr,uid,kiirando,context=None)

            kiirando['erteknap'] = _vegdatum
            kiirando['szoveg']= 'Aktuális egyenleg'
            kiirando['eloiras']= 0
            kiirando['befizetes']= szumma
            kiirando['havijel_id'] = _sajat_id
            id_je=_havijel_sor_hiv.create(cr,uid,kiirando,context=None)
        else:
            kiirando['erteknap'] = _vegdatum
            kiirando['szoveg']= 'Nincs az időpontra rögzített adat!!!'
            kiirando['eloiras']= 0
            kiirando['befizetes']= 0
            kiirando['havijel_id'] = _sajat_id
            id_je=_havijel_sor_hiv.create(cr,uid,kiirando,context=None)










portal_user_havijel()


class portal_user_havijel_sor(osv.osv):
    _name='portal.user.havijel.sor'
    _columns = {
          'erteknap':fields.date('Konyveles napja' ),
          'szoveg':fields.char('Eloiras', size=64),
          'eloiras':fields.integer('Eloiras'),
          'befizetes':fields.integer('Befizetes'),
          'havijel_id':fields.many2one('portal.user.havijel','kapocs', ondelete='cascade', select=True, readonly=True),
                }
    _order = 'erteknap, id'

portal_user_havijel_sor()