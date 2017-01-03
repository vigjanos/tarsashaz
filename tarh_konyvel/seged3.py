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

    # változók inicializálása
    lako_nyito_hiv = self.env['tarh.lako.nyito']
    eloiras_lako_hiv = self.env['tarh.eloiras.lako']
    my_report_hiv = self.env['my.report']
    eloiras_haz_hiv = self.env['tarh.eloiras.haz']
    sum_eloiras = 0
    sum_jovairas = 0
    nyito_osszege = 0
    kesedelmi_kamat = 0.0
    eloiras_list = []
    befizetes_list = []

    # ellenőrizzük, hogy a kapott dátum date formátumú-e
    if type(datum) != date:
        datum = str_to_date(datum)
    # eltesszük a dátumot
    datum_2 = datum

    tulajdonos = self.env['res.partner'].browse([lako])
    tarsashaz = tulajdonos.parent_id.id
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
        tulaj_eloirasai = eloiras_lako_hiv.search([('lako', '=', lako)])
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
        for befizetes in befizetes_lista:
            sum_jovairas = sum_jovairas + befizetes.jovairas - befizetes.terheles
            befizetes_list.append((str_to_date(befizetes.erteknap), befizetes.tarh_tranzakcio.name,
                                   befizetes.jovairas - befizetes.terheles))

        def napi_egyenleg(idopont):
            # a nyitó, az előiras és a befizetes, alapján kiszámolja, hogy aznap mennyi az egyenleg
            # ami a kamatszámításhoz kell majd
            if type(idopont) != date:
                idopont = str_to_date(idopont)
            aktualis_egyenleg = nyito_osszege
            for eloiras in eloiras_list:
                if eloiras[0] <= idopont:
                    aktualis_egyenleg = aktualis_egyenleg - eloiras[2]
            for befiz in befizetes_list:
                if befiz[0] <= idopont:
                    aktualis_egyenleg = aktualis_egyenleg + befiz[2]
            aktualis_eloiras = eloiras_haz_hiv.search([('konyvelt_haz', '=', tarsashaz),
                                                       ('eloirfajta.name', 'ilike', 'kamat'),
                                                       ('eloir_kezd', '<=', idopont),
                                                       ('eloir_vege', '>=', idopont)])
            kamatlab = aktualis_eloiras.osszeg

            return (aktualis_egyenleg, kamatlab)

        # megvizsgáljuk, hogy a társasházban írtak-e elő késedelmi kamatot a befizetésekre
        # a kamatot úgy számoljuk, hogy megvizsgáljuk, hogy a házban van-e kamat érvényben a datum időpontig
        # ha van akkor végigmegyünk a napokon, és ha tartozás van akkor kamatként felszámítjuk az éves kamat
        # 365-öd részét
        kesedelem_eloirasok = eloiras_haz_hiv.search(
            [('konyvelt_haz', '=', tarsashaz), ('eloirfajta.name', 'ilike', 'kamat'),
             ('eloir_kezd', '<', datum)])


        if kesedelem_eloirasok:
            kamat_kezdete = str_to_date(kesedelem_eloirasok[0].eloir_kezd)  # a legkorábbi kamatelőírás
            if kamat_kezdete < datum:
                # amikor ide fut a program akkor (a datum időpontban) már van a házban késedelmi kamat előírva!
                szamlalo = kamat_kezdete
                while szamlalo <= datum:
                    npi_egyenleg = napi_egyenleg(szamlalo)
                    if npi_egyenleg[0] < 0: #tartozás van!
                        kesedelmi_kamat = kesedelmi_kamat + float(npi_egyenleg[1])/100/365 * npi_egyenleg[0]
                    szamlalo = szamlalo + timedelta(days=1)
                kesedelmi_kamat = int(kesedelmi_kamat)* -1
                eloiras_list.append((datum, 'Késedelmi kamat', kesedelmi_kamat))

        egyenleg = nyito_osszege + sum_jovairas - sum_eloiras - kesedelmi_kamat

        havi_fiz = havi_fizetendo2(self, lako, datum)

        eredmeny = [egyenleg, sum_eloiras + kesedelmi_kamat, sum_jovairas, havi_fiz, eloiras_list, befizetes_list]

        return (eredmeny)


    else:  # nincs nyitóegyenleg
        eredmeny = [0, 0, 0, -1]
        return (eredmeny)


def lakolista(self, datum, tarsashaz):
    '''
    megkeressük azokat a lakókat, akik a datum időpontban tulajdonosok: nem adták el korábban a lakást.
    '''
    # ellenőrizzük, hogy a kapott dátum date formátumú-e
    if type(datum) != date:
        datum = str_to_date(datum)
    ref_res_partner = self.env['res.partner']
    eladottak = ref_res_partner.search([('parent_id', '=', tarsashaz), ('alb_eladas', '<', datum)])
    eladott_idk = []
    tulaj_idk = []
    for eladott in eladottak:
        eladott_idk.append(eladott.id)
    tulajdonosok = ref_res_partner.search([('parent_id', '=', tarsashaz), ('supplier', '=', False),
                                                    ('active', '=', True)]
                                          , order='alb_szam')
    for tulaj in tulajdonosok:
        tulaj_idk.append(tulaj.id)
    for eladva in eladott_idk :
        tulaj_idk.remove(eladva)  # eltavolitjuk a a tulajdonosok listajabol az eladottakat
    return (tulaj_idk)  # visszaterunk a tulajdonosok listajaval a datum idopontban

def havi_fizetendo2 (self, tulajdonos, datum):
    '''
    meg kell csinálni, hogy a visszatérő érték egy lista, és két integer legyen
    a listában adjuk vissza a előírások (nevét,összegét), összeget rendkívülivel és ügyvédivel, és
    a nélkül is
    '''
    _tarh_eloiras_lako = self.env['tarh.eloiras.lako']
    #_eloiras_fajta = self.pool.get('eloiras.fajta')
    lako_eloir_id = _tarh_eloiras_lako.search([('lako', '=', tulajdonos)])
    #lako_eloirasai = _tarh_eloiras_lako.browse(lako_eloir_id)
    eloirasai = 0
    for egy_eloiras in lako_eloir_id:
        if datum >= str_to_date(egy_eloiras.eloir_kezd) and datum <= str_to_date(egy_eloiras.eloir_vege):
            if 'Rendk' not in egy_eloiras.eloirfajta.name and 'gyv' not in egy_eloiras.eloirfajta.name:
                eloirasai = eloirasai + egy_eloiras.osszeg
    return eloirasai


def utolso_konyvelt_datum (self, tarsashaz):
    '''
    a társasház utolsó könyvelt dátumát kérdezi le.
    :param self:
    :param tarsashaz: társasház kódja int
    :return: a legutolsó lekönyvelt nap   date
    '''
    tarsashaz = str(tarsashaz)
    cur = self.env.cr
    conn_string = "select erteknap from tarh_bankbiz_sor join tarh_bankbiz on tarh_bankbiz.id=bankbiz_id \
                   where th_szamlatul=" + tarsashaz + " order by erteknap desc limit 1"
    cur.execute(conn_string)
    eredmeny = cur.fetchone()
    if eredmeny:
        return eredmeny[0]
    else:
        return (time.strftime("%Y-%m-%d"))  # ha nincs meg konyvelt befizetes, akkor a mai datummal terunk vissza
