# -*- coding: utf-8 -*-
__author__ = 'vigjani'

from openerp.osv import osv, fields
from datetime import date




def str_to_date(str_date):
    szeletelt=str_date.split("-")
    return(date( int(szeletelt[0]),int(szeletelt[1]),int(szeletelt[2])))

def lakoegyenleg(self,cr,uid,lako,datum):
    #kiszamolja,hogy a _lako tulajdonosnak a datum idopontban mennyi az egyenlege a nyitoegyenleg felvitele ota
    #ezt az eredmeny listaban adjuk vissza: nyito, osszes eloiras, osszes jovairas, datum honapjaban a
    #rendkivuli nelkuli eloiras formaban
    sum_eloiras=0
    sum_jovairas=0
    _nyito_osszeg=0
    havi_eloiras=0
    _tarh_lako_nyito=self.pool.get('tarh.lako.nyito')
    talalt_id=_tarh_lako_nyito.search(cr,uid,[('tarh_lako','=',lako)],context=None)
    if talalt_id: # ha van nyitoegyenleg rogzitve
        nyito_dok=_tarh_lako_nyito.browse(cr,uid,talalt_id[0],context=None)
        _nyito_datum=nyito_dok.egyenleg_datuma
        _nyito_osszeg=nyito_dok.egyenleg
        _tarh_lakoeloir_havi=self.pool.get('tarh.lakoeloir.havi')
        _eloiras_fajta=self.pool.get('eloiras.fajta')
        _my_report=self.pool.get('my.report')
        tarh_lakoeloir_havi_lista=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',lako),('eloir_datum','>',_nyito_datum),('eloir_datum','<=',datum)],context=None) #datum szures kell bele!
        my_report_lista=_my_report.search(cr,uid,[('partner','=',lako),('erteknap','>',_nyito_datum),('erteknap','<=',datum)],context=None) #datum szures kell bele!
        eloirasok=_tarh_lakoeloir_havi.browse(cr,uid,tarh_lakoeloir_havi_lista, context=None)

        #innen kezdodik a havi eloirasok kigyujtese
        aktualis_havi_eloir_lista=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',lako),('ev','=',datum.year),('honap','=',datum.month)],context=None)
        aktualis_havi_eloiras=_tarh_lakoeloir_havi.browse(cr,uid,aktualis_havi_eloir_lista,context=None)
        for havi_eloir in aktualis_havi_eloiras:
            eloirasfajta=havi_eloir.eloirfajta.id
            eloir_list= _eloiras_fajta.search(cr,uid,[('id','=',eloirasfajta)],context=None)
            eloir_neve=_eloiras_fajta.browse(cr,uid,eloir_list[0],context=None).name
            eloir_osszege=havi_eloir.osszeg
            if 'Rendk' not in eloir_neve and 'gyv' not in eloir_neve:
                havi_eloiras = havi_eloiras + eloir_osszege



        befizetesek=_my_report.browse(cr,uid,my_report_lista,context=None)
        for befizetes in befizetesek:
            _nyito_osszeg = _nyito_osszeg+befizetes.jovairas-befizetes.terheles
            sum_jovairas = sum_jovairas + befizetes.jovairas-befizetes.terheles
        for eloiras in eloirasok:
            _nyito_osszeg= _nyito_osszeg-eloiras.osszeg
            sum_eloiras = sum_eloiras + eloiras.osszeg
            #ha a kejerdezesi datum korabbi mint a nyitoegyenleg datuma, akkor a kezdeti datum a nyitoegyenleg datuma lesz
        _nyito_datum_date=str_to_date(_nyito_datum)
        if datum < _nyito_datum_date:
            datum=_nyito_datum_date

        eredmeny=[_nyito_osszeg, sum_eloiras, sum_jovairas, havi_eloiras]
        return(eredmeny)
