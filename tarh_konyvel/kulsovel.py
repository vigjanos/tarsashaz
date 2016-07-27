# -*- coding: utf-8 -*-
from datetime import date
import odoorpc

__author__ = 'vigjanos'

odoo = odoorpc.ODOO()
odoo.login('ujlipot_benti','szilassy','196101')

def str_to_date(str_date):
    szeletelt=str_date.split("-")
    return(date( int(szeletelt[0]),int(szeletelt[1]),int(szeletelt[2])))


lako=2993
datum = str_to_date('2015-10-31')
Nyitoegyenlegek= odoo.env['tarh.lako.nyito']
nyitoegyenleg = Nyitoegyenlegek.search([('tarh_lako','=',lako)])
if nyitoegyenleg: #van nyitoegyenleg!
    lako_nyito = Nyitoegyenlegek.browse(nyitoegyenleg)
    _nyito_datum = lako_nyito.egyenleg_datuma
    _nyito_osszeg = lako_nyito.egyenleg
    _tarh_lakoeloir_havi=odoo.env['tarh.lakoeloir.havi']
    _eloiras_fajta=odoo.env['eloiras.fajta']
    _my_report=odoo.env['my.report']
    ossz_eloiras=0
    ossz_befizetes=0

    tarh_lakoeloir_havi_lista=_tarh_lakoeloir_havi.search([('lako','=',lako),('eloir_datum','>',str(_nyito_datum)),('eloir_datum','<=',str(datum))])
    my_report_lista=_my_report.search([('partner','=',lako),('erteknap','>',str(_nyito_datum)),('erteknap','<=',str(datum))]) #datum szures kell bele!
    eloirasok=_tarh_lakoeloir_havi.browse(tarh_lakoeloir_havi_lista)
    befizetesek=_my_report.browse(my_report_lista)

    for eloiras in eloirasok:
        ossz_eloiras=ossz_eloiras+eloiras.osszeg
        #print eloiras.eloir_datum,'    ',eloiras.eloirfajta.name,'   ',eloiras.osszeg
    for befizetes in befizetesek:
        ossz_befizetes=ossz_befizetes+befizetes.jovairas-befizetes.terheles
    egyenleg=_nyito_osszeg+ossz_befizetes-ossz_eloiras

    print lako_nyito.tarh_lako.name, '    ',lako_nyito.egyenleg_datuma,'  ',lako_nyito.egyenleg,'   ', egyenleg




pass


