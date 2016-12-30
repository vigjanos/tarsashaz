# -*- coding: utf-8 -*-
'''
create by vigjanos on 2016.12.26.
Ez a lakóegyenlegek új számításához szükséges + kamatok
'''

from openerp import models, fields, api, _
from datetime import date, timedelta
from collections import defaultdict
import time


def str_to_date(str_date):
    '''string alakú dátumot date formátumra alakít'''
    szeletelt = str_date.split("-")
    return (date(int(szeletelt[0]), int(szeletelt[1]), int(szeletelt[2])))


def honap_utolsonap(datum):
    ev = datum.year
    honap = datum.month
    nap = datum.day
    if honap == 12:
        honap = 1
        ev = ev + 1
    else:
        honap = honap + 1
    nap = 1
    ujdatum = date(ev, honap, nap)
    ujdatum = ujdatum - timedelta(days=1)
    return ujdatum


def add_month(ev, honap):
    if honap == 12:
        honap = 1
        ev = ev + 1
    else:
        honap = + honap + 1
    return (ev, honap)


def tulajegyenleg(self, lako, datum):
    ''' kiszámolja, hogy a lako tulajdonosnak a datum időpontban mennyi az egyenlege a nyitóegyenleg felvitele
            óta, ezt az eredményt listában adjuk vissza:
            - egyenleg a datum napon,
            - osszes_eloiras nyitoegyenleg napjatol a datum-ig
            - osszes_jovairas nyitoegyenleg napjatol a datum-ig,
            - havonta előírt osszeg a datum hónapjaban rendkívüli és ügyvédi díj nélküli előíras formában.
            - előírások listáját (dátum, előírás, összeg) illetve a
            - befizetéseklistáját (dátum, befizetés,összeg) formában

            Ha nincs a lakóhoz nyitóegyenleg felvéve, akkor [0,0,0,-1] -et ad vissza'''

    #változók inicializáslása
    lako_nyito_hiv = self.env['tarh.lako.nyito']
    eloiras_lako_hiv = self.env['tarh.eloiras.lako']
    eloiras_fajta_hiv = self.env['eloiras.fajta']  # nem biztos, hogy kell!
    my_report_hiv = self.env['my.report']
    sum_eloiras = 0
    sum_jovairas = 0
    nyito_osszege = 0
    havi_eloiras = 0
    eloiras_list = []
    befizetes_list = []


    # ellenőrizzük, hogy a kapott dátum date formátumú-e
    if type(datum) != date:
        datum = str_to_date(datum)
    # eltesszük a dátumot
    datum_2 = datum

    tulajdonos = self.env['res.partner'].browse([lako])
    # ha eladták az ingatlant korábban mint a kérdezett dátum, akkor az egyenleg dátuma az eladás időpontja lesz
    if tulajdonos.alb_eladas:
        if str_to_date(tulajdonos.alb_eladas) < datum:
            datum_2 = str_to_date(tulajdonos.alb_eladas)


    lako_nyito = lako_nyito_hiv.search([('tarh_lako', '=', lako)])
    if lako_nyito:  # van nyitóegyenlege a tulajdonosnak
        nyito_osszege = lako_nyito.egyenleg
        nyito_datuma = str_to_date(lako_nyito.egyenleg_datuma)
        if datum_2 < nyito_datuma:  # lekérdezés dátuma korábbi mint a nyitó dátuma, a nyitóval térünk vissza!
            eredmeny = [nyito_osszege, 0, 0, 0]
            return (eredmeny)

        # megkeressük a tulajdonos előírásait
        tulaj_eloirasai = eloiras_lako_hiv.search([('lako','=',lako)])
        for tulaj_eloiras in tulaj_eloirasai:
            # végiglépkedünk a tulajdonos előírásain
            leker_datum = nyito_datuma

            while leker_datum <= datum:
                # végigmegyünk a nyitóegyenleg dátumától a kívánt dátumig
                if honap_utolsonap(date(leker_datum.year, leker_datum.month, 1)).day > tulaj_eloiras.esedekes:
                    havi_esedekesseg = date(leker_datum.year, leker_datum.month, tulaj_eloiras.esedekes)
                    # előállítottuk az esedékesség dátumát a hónapban
                else:
                    havi_esedekesseg = honap_utolsonap(date(leker_datum.year, leker_datum.month, 1))
                    # ide csak akkor fut, ha pl esedékességnek 31-e van előírva 30 napos hónapban, ekkor a hónap utolsó
                    # napjára cseréljük az esedékesség dátumát
                if leker_datum >= str_to_date(tulaj_eloiras.eloir_kezd) and leker_datum <= str_to_date(
                        tulaj_eloiras.eloir_vege) and nyito_datuma <= havi_esedekesseg and datum >= havi_esedekesseg:
                    # print havi_esedekesseg, egy_eloiras.eloirfajta.name, egy_eloiras.osszeg
                    sum_eloiras = sum_eloiras + tulaj_eloiras.osszeg
                    eloiras_list.append((havi_esedekesseg, tulaj_eloiras.eloirfajta.name, tulaj_eloiras.osszeg))
                novelt_datum = add_month(leker_datum.year, leker_datum.month)
                leker_datum = date(novelt_datum[0], novelt_datum[1], 1)

        # megkezdjük a befizetések kigyűjtését
        befizetes_lista = my_report_hiv.search([('partner', '=', lako), ('erteknap', '>', nyito_datuma),
                                                      ('erteknap', '<=', datum)])
        #befizetesek = _my_report.browse(cr, uid, befizetes_lista, context=None)
        for befizetes in befizetes_lista:
            sum_jovairas = sum_jovairas + befizetes.jovairas - befizetes.terheles
            befizetes_list.append((str_to_date(befizetes.erteknap), befizetes.tarh_tranzakcio.name,
                                   befizetes.jovairas - befizetes.terheles))


        egyenleg = nyito_osszege + sum_jovairas - sum_eloiras

        #havi_fiz = havi_fizetendo2(self, cr, uid, lako, datum)

        #eredmeny = [egyenleg, sum_eloiras, sum_jovairas, havi_fiz, eloiras_list, befizetes_list]

        return


    else:  # nincs nyitóegyenleg
        eredmeny = [0, 0, 0, -1]
        return (eredmeny)


def lakolista(self, cr, uid, datum, tarsashaz):
    '''
    megkeressük azokat a lakókat, akik a datum időpontban tulajdonosok: nem adták el korábban a lakást.
    '''
    ref_res_partner = self.pool.get('res.partner')
    eladottak = ref_res_partner.search(cr, uid, [('parent_id', '=', tarsashaz), ('alb_eladas', '<', datum)],
                                       context=None)
    tulajdonosok = ref_res_partner.search(cr, uid, [('parent_id', '=', tarsashaz), ('supplier', '=', False),
                                                    ('active', '=', True)]
                                          , order='alb_szam', context=None)
    for eladva in eladottak:
        tulajdonosok.remove(eladva)  # eltavolitjuk a a tulajdonosok listajabol az eladottakat
    return (tulajdonosok)  # visszaterunk a tulajdonosok listajaval a datum idopontban
