# -*- coding: utf-8 -*-
__author__ = 'vigjani'

from openerp.osv import osv, fields
from datetime import date, timedelta
from collections import defaultdict
import time


def str_to_date (str_date):
    '''string alakú dátumot date formátumra alakít'''
    szeletelt = str_date.split("-")
    return (date(int(szeletelt[0]), int(szeletelt[1]), int(szeletelt[2])))


def honap_utolsonap (datum):
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


def add_month (ev, honap):
    if honap == 12:
        honap = 1
        ev = ev + 1
    else:
        honap = + honap + 1
    return (ev, honap)


def lakoegyenleg3 (self, cr, uid, lako, datum):
    ''' kiszámolja, hogy a lako tulajdonosnak a datum időpontban mennyi az egyenlege a nyitóegyenleg felvitele
        óta, ezt az eredményt listában adjuk vissza: egyenleg, osszes_eloiras, osszes_jovairas, előírt osszeg a dátum
        hónapjaban rendkívüli és ügyvédi díj nélküli előíras formában.
        Visszaadja listában a
        - előírások listáját (dátum, előírás, összeg) illetve a
        - befizetéseklistáját (dátum, befizetés,összeg) formában
        Ha nincs a lakóhoz nyitóegyenleg felvéve, akkor [0,0,0,-1] -et ad vissza'''
    if type(datum) != date:
        datum = str_to_date(datum) # lehet, hogy majd ki kell szedni
    datum_2 = datum
    lako_partner = self.pool.get('res.partner').browse(cr, uid, lako, context=None)
    if lako_partner.alb_eladas:
        if str_to_date(lako_partner.alb_eladas) < datum:
            datum_2 = str_to_date(lako_partner.alb_eladas)
            # ha elobb eladtak az ingatlant, mint a kerdezett datum, akkor a datum az eladas datuma lesz
    sum_eloiras = 0
    sum_jovairas = 0
    _nyito_osszeg = 0
    havi_eloiras = 0
    _tarh_lako_nyito = self.pool.get('tarh.lako.nyito')
    talalt_id = _tarh_lako_nyito.search(cr, uid, [('tarh_lako', '=', lako)], context=None)
    if talalt_id:
        nyito_dok = _tarh_lako_nyito.browse(cr, uid, talalt_id[0], context=None)
        _nyito_datum = str_to_date(nyito_dok.egyenleg_datuma)
        _nyito_osszeg = nyito_dok.egyenleg
        if datum_2 < _nyito_datum:  # a lekerdezes datuma korabbi mint a nyitoegyenleg datuma csak eddig vesszuk az eloirasokat!
            eredmeny = [_nyito_osszeg, 0, 0, 0]
            return(eredmeny)

        nyito_egyenleg = _nyito_osszeg
        _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
        _eloiras_fajta = self.pool.get('eloiras.fajta')
        _my_report = self.pool.get('my.report')
        ev = _nyito_datum.year
        honap = _nyito_datum.month
        lako_eloir_id = _tarh_eloiras_lako.search(cr, uid, [('lako', '=', lako)], context=None)
        lako_eloirasai = _tarh_eloiras_lako.browse(cr, uid, lako_eloir_id, context=None)
        eloiras_list = []
        befizetes_list = []


        '''Itt kezdődik az előírások kigyűjtése'''

        for egy_eloiras in lako_eloirasai:
            ev = _nyito_datum.year
            honap = _nyito_datum.month
            leker_datum = _nyito_datum

            while (leker_datum <= datum):
                #print leker_datum.year, leker_datum.month, egy_eloiras.esedekes
                #ha a datumhoz nem passzol a nap pl. februar 30-ra akarnank allitani, ez csak akkor kell, ha valami
                # buzi ugyvedi v. hasonlo 31-ere lenne eloirva
                if honap_utolsonap(date(leker_datum.year,leker_datum.month,1)).day > egy_eloiras.esedekes:
                    havi_esedekesseg = date(leker_datum.year, leker_datum.month, egy_eloiras.esedekes)
                else:
                    havi_esedekesseg = honap_utolsonap(date(leker_datum.year,leker_datum.month,1))
                if leker_datum >= str_to_date(egy_eloiras.eloir_kezd) and leker_datum <= str_to_date(
                        egy_eloiras.eloir_vege) and _nyito_datum <= havi_esedekesseg and datum >= havi_esedekesseg:
                    #print havi_esedekesseg, egy_eloiras.eloirfajta.name, egy_eloiras.osszeg
                    sum_eloiras = sum_eloiras + egy_eloiras.osszeg
                    eloiras_list.append((havi_esedekesseg,egy_eloiras.eloirfajta.name,egy_eloiras.osszeg))
                novelt_datum = add_month(leker_datum.year,leker_datum.month)
                leker_datum = date(novelt_datum[0],novelt_datum[1],1)


        '''Itt kezdődik a befizetések kigyűjtése'''
        my_report_lista = _my_report.search(cr, uid, [('partner', '=', lako), ('erteknap', '>', _nyito_datum),
                                                      ('erteknap', '<=', datum)],
                                            context=None)
        befizetesek = _my_report.browse(cr, uid, my_report_lista, context=None)
        for befizetes in befizetesek:
            sum_jovairas = sum_jovairas + befizetes.jovairas - befizetes.terheles
            befizetes_list.append((str_to_date(befizetes.erteknap), befizetes.tarh_tranzakcio.name,
                                   befizetes.jovairas - befizetes.terheles))
        egyenleg = nyito_egyenleg + sum_jovairas - sum_eloiras

        havi_fiz = havi_fizetendo2(self, cr, uid, lako, datum)

        eredmeny = [egyenleg, sum_eloiras, sum_jovairas, havi_fiz, eloiras_list, befizetes_list]
#        eredmeny[0]=100
        return eredmeny


    else:  # ha nincs nyitoegyenleg
        eredmeny = [0, 0, 0, -1]
        return (eredmeny)
        # [egyenleg, oszes eloiras, osszes jovairas, havonta eloiras, eloirasok listaja, befizetesek listaja]

def lakoegyenleg (self, cr, uid, lako, datum):
    ''' kiszámolja, hogy a lako tulajdonosnak a datum időpontban mennyi az egyenlege a nyitóegyenleg felvitele
        óta, ezt az eredményt listában adjuk vissza: egyenleg, osszes_eloiras, osszes_jovairas, osszeg a dátum
        hónapjaban az előírások a rendkívüli nélküli előíras formában.
        Ha nincs a lakóhoz nyitóegyenleg felvéve, akkor [0,0,0,-1] -et ad vissza'''
    if type(datum) != date:
        datum = str_to_date(datum) # lehet, hogy majd ki kell szedni
    sum_eloiras = 0
    sum_jovairas = 0
    _nyito_osszeg = 0
    havi_eloiras = 0
    _tarh_lako_nyito = self.pool.get('tarh.lako.nyito')
    talalt_id = _tarh_lako_nyito.search(cr, uid, [('tarh_lako', '=', lako)], context=None)
    if talalt_id:  # ha van nyitoegyenleg rogzitve
        nyito_dok = _tarh_lako_nyito.browse(cr, uid, talalt_id[0], context=None)
        _nyito_datum = nyito_dok.egyenleg_datuma
        _nyito_osszeg = nyito_dok.egyenleg
        egyenleg = _nyito_osszeg
        _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
        _eloiras_fajta = self.pool.get('eloiras.fajta')
        _my_report = self.pool.get('my.report')
        tarh_lakoeloir_havi_lista = _tarh_lakoeloir_havi.search(cr, uid, [('lako', '=', lako),
                                                                          ('eloir_datum', '>', _nyito_datum),
                                                                          ('eloir_datum', '<=', datum)],
                                                                context=None)  # datum szures kell bele!
        my_report_lista = _my_report.search(cr, uid, [('partner', '=', lako), ('erteknap', '>', _nyito_datum),
                                                      ('erteknap', '<=', datum)],
                                            context=None)  # datum szures kell bele!
        eloirasok = _tarh_lakoeloir_havi.browse(cr, uid, tarh_lakoeloir_havi_lista, context=None)

        # innen kezdodik a havi eloirasok kigyujtese
        aktualis_havi_eloir_lista = _tarh_lakoeloir_havi.search(cr, uid, [('lako', '=', lako), ('ev', '=', datum.year),
                                                                          ('honap', '=', datum.month)], context=None)
        aktualis_havi_eloiras = _tarh_lakoeloir_havi.browse(cr, uid, aktualis_havi_eloir_lista, context=None)
        for havi_eloir in aktualis_havi_eloiras:
            eloirasfajta = havi_eloir.eloirfajta.id
            eloir_list = _eloiras_fajta.search(cr, uid, [('id', '=', eloirasfajta)], context=None)
            eloir_neve = _eloiras_fajta.browse(cr, uid, eloir_list[0], context=None).name
            eloir_osszege = havi_eloir.osszeg
            if 'Rendk' not in eloir_neve and 'gyv' not in eloir_neve:
                havi_eloiras = havi_eloiras + eloir_osszege

        befizetesek = _my_report.browse(cr, uid, my_report_lista, context=None)
        for befizetes in befizetesek:
            egyenleg = egyenleg + befizetes.jovairas - befizetes.terheles
            sum_jovairas = sum_jovairas + befizetes.jovairas - befizetes.terheles
        for eloiras in eloirasok:
            egyenleg = egyenleg - eloiras.osszeg
            sum_eloiras = sum_eloiras + eloiras.osszeg
            # ha a lekerdezesi datum korabbi mint a nyitoegyenleg datuma, akkor a kezdeti datum a nyitoegyenleg datuma lesz
        _nyito_datum_date = str_to_date(_nyito_datum)
        if datum < _nyito_datum_date:
            datum = _nyito_datum_date

        eredmeny = [egyenleg, sum_eloiras, sum_jovairas, havi_eloiras]
        return (eredmeny)
    else:  # ha nincs nyitoegyenleg
        eredmeny = [0, 0, 0, -1]
        return (eredmeny)
        # [egyenleg, oszes eloiras, osszes jovairas, havonta eloiras]


def lakolista (self, cr, uid, datum, tarsashaz):
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


def eloirasok (self, cr, uid, tulajdonos, kezdatum, vegdatum):
    '''
    Ez az eljárás megadja az időpontok között, hogy a tulajdonos részére milyen befizetéseket írtunk elő fajtánként
    '''
    tulaj = str(tulajdonos)
    conn_string = "select eloiras_fajta.name, sum(osszeg) from tarh_lakoeloir_havi join eloiras_fajta" \
                  " on eloirfajta = eloiras_fajta.id where lako = " + tulaj + " and eloir_datum " \
                                                                              "between '" + str(kezdatum) + "' and '" + str(vegdatum) + "' group by eloiras_fajta.name"
    cr.execute(conn_string)
    eredmeny = cr.fetchall()
    eredmeny[0]=100
    return eredmeny


def eloirasok2 (self, cr, uid, tulajdonos, kezdatum, vegdatum):
    '''
    Ez az eljárás megadja az időpontok között, hogy a tulajdonos részére milyen befizetéseket írtunk elő fajtánként
    Egy listát adunk vissza string(előírás neve),integer(előírás összesen) elemekkel
    '''
    kezdatum=str_to_date(kezdatum)
    vegdatum= str_to_date(vegdatum)
    lako_partner = self.pool.get('res.partner').browse(cr, uid, tulajdonos, context=None)
    if lako_partner.alb_eladas:
        if str_to_date(lako_partner.alb_eladas) < vegdatum:
            vegdatum = str_to_date(lako_partner.alb_eladas)
            # ha elobb eladtak az ingatlant, mint a kerdezett vegdatum, akkor a vegdatum az eladas datuma lesz
    if lako_partner.alb_vetel:
        if str_to_date(lako_partner.alb_vetel) > kezdatum:
            kezdatum = str_to_date(lako_partner.alb_vetel)
            # ha a kezdeti datum korabbi mint az ingatlan veteli datuma, akkor a kezdodatum a vetel datuma lesz
    _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
    _eloiras_fajta = self.pool.get('eloiras.fajta')
    lako_eloir_id = _tarh_eloiras_lako.search(cr, uid, [('lako', '=', tulajdonos)], context=None)
    lako_eloirasai = _tarh_eloiras_lako.browse(cr, uid, lako_eloir_id, context=None)
    eloiras_list = []


    '''Itt kezdődik az előírások kigyűjtése'''

    for egy_eloiras in lako_eloirasai:
        ev = kezdatum.year
        honap = kezdatum.month
        leker_datum = kezdatum
        sum_eloiras = 0
        while (leker_datum <= vegdatum):
            #print leker_datum.year, leker_datum.month, egy_eloiras.esedekes
            #ha a datumhoz nem passzol a nap pl. februar 30-ra akarnank allitani
            if honap_utolsonap(date(leker_datum.year,leker_datum.month,1)).day > egy_eloiras.esedekes:
                havi_esedekesseg = date(leker_datum.year, leker_datum.month, egy_eloiras.esedekes)
            else:
                havi_esedekesseg = honap_utolsonap(date(leker_datum.year,leker_datum.month,1))
            if leker_datum >= str_to_date(egy_eloiras.eloir_kezd) and leker_datum <= str_to_date(
                    egy_eloiras.eloir_vege) and kezdatum <= havi_esedekesseg and vegdatum >= havi_esedekesseg:
                #print havi_esedekesseg, egy_eloiras.eloirfajta.name, egy_eloiras.osszeg
                sum_eloiras = sum_eloiras + egy_eloiras.osszeg
            novelt_datum = add_month(leker_datum.year,leker_datum.month)
            leker_datum = date(novelt_datum[0],novelt_datum[1],1)
        if sum_eloiras != 0:
            eloiras_list.append([egy_eloiras.eloirfajta.name,sum_eloiras])


    ''' A következő huncutság azért kell, hogy az egyfajta előírásokat összeadja, és ne külön szerepeljenek, ha
    valamelyik előírásban váltás volt.    Nem túl elegáns a kód, de reméljük jó lesz!

    Ez a régi verzió:

    kimeno_list=[]
    eloiras_list.sort()
    rogzitjuk=False
    for akt_eloir in eloiras_list:
        my2_hossz=len(kimeno_list)
        if my2_hossz == 0:
            kimeno_list.append([akt_eloir[0], akt_eloir[1]])
        else:
            for my2 in kimeno_list:
                rogzitjuk=False
                if akt_eloir[0] == my2[0]:
                    my2[1]=akt_eloir[1]+my2[1]
                else:
                    rogzitjuk=True
        if rogzitjuk:
            kimeno_list.append([akt_eloir[0], akt_eloir[1]])
    '''


    '''
    Itt az új verzió !!!
    '''
    kimeno_list = defaultdict(int)
    for eloiras, value in eloiras_list:
        kimeno_list[eloiras] += value
    kimeno_list = kimeno_list.items()

    #eloiras_list[0]=100
    #return eloiras_list
    return kimeno_list


def havi_fizetendo2 (self, cr, uid, tulajdonos, datum):
    '''
    meg kell csinálni, hogy a visszatérő érték egy lista, és két integer legyen
    a listában adjuk vissza a előírások (nevét,összegét), összeget rendkívülivel és ügyvédivel, és
    a nélkül is
    '''
    _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
    _eloiras_fajta = self.pool.get('eloiras.fajta')
    lako_eloir_id = _tarh_eloiras_lako.search(cr, uid, [('lako', '=', tulajdonos)], context=None)
    lako_eloirasai = _tarh_eloiras_lako.browse(cr, uid, lako_eloir_id, context=None)
    eloirasai = 0
    for egy_eloiras in lako_eloirasai:
        if datum >= str_to_date(egy_eloiras.eloir_kezd) and datum <= str_to_date(egy_eloiras.eloir_vege):
            if 'Rendk' not in egy_eloiras.eloirfajta.name and 'gyv' not in egy_eloiras.eloirfajta.name:
                eloirasai = eloirasai + egy_eloiras.osszeg
    return eloirasai


def havi_fizetendo (self, cr, uid, tulajdonos, datum):
    '''
    Megadja, hogy az illető tulajdonosnak a datum hónapjában mennyi volt összesen az előrása
    rendkívüli és ügyvédi díj előírása nélkül
    '''
    _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
    _eloiras_fajta = self.pool.get('eloiras.fajta')
    aktualis_havi_eloir_lista = _tarh_lakoeloir_havi.search(cr, uid,
                                                            [('lako', '=', tulajdonos), ('ev', '=', datum.year),
                                                             ('honap', '=', datum.month)], context=None)
    aktualis_havi_eloiras = _tarh_lakoeloir_havi.browse(cr, uid, aktualis_havi_eloir_lista, context=None)
    havi_eloiras = 0
    for havi_eloir in aktualis_havi_eloiras:
        eloirasfajta = havi_eloir.eloirfajta.id
        eloir_list = _eloiras_fajta.search(cr, uid, [('id', '=', eloirasfajta)], context=None)
        eloir_neve = _eloiras_fajta.browse(cr, uid, eloir_list[0], context=None).name
        eloir_osszege = havi_eloir.osszeg
        if ('Rendk' not in eloir_neve and 'gyv' not in eloir_neve):
            havi_eloiras = havi_eloiras + eloir_osszege
    return (havi_eloiras)


def utolso_konyvelt_datum (self, cr, uid, tarsashaz):
    '''
    a társasház utolsó könyvelt dátumát kérdezi le.
    :param self:
    :param cr:
    :param uid:
    :param tarsashaz: társasház kódja int
    :return:
    '''
    tarsashaz = str(tarsashaz)
    conn_string = "select erteknap from tarh_bankbiz_sor join tarh_bankbiz on tarh_bankbiz.id=bankbiz_id \
                   where th_szamlatul=" + tarsashaz + " order by erteknap desc limit 1"
    cr.execute(conn_string)
    eredmeny = cr.fetchone()
    if eredmeny:
        return eredmeny[0]
    else:
        return (time.strftime("%Y-%m-%d"))  # ha nincs meg konyvelt befizetes, akkor a mai datummal terunk vissza

def bankegyenleg(self,cr,uid,bankszamla,datum):
    '''
    A bankegyenleget ez az eljárás nem a bankbizonylatok összesen eltárolt adatai alapján számolja, hanem a sorok összegével
    Kiolvassuk, hogy milyen nyitóérték és dátum van eltárolva a bankszámlához
    '''
    bszamla_nyito=self.pool.get('tarh.bszamla.nyito').search(cr,uid,[('tarh_bszamla','=',bankszamla)],context=None)
    if bszamla_nyito:
        nyito_ertek=self.pool.get('tarh.bszamla.nyito').browse(cr,uid,bszamla_nyito[0],context=None).egyenleg
        nyito_datum=str_to_date(self.pool.get('tarh.bszamla.nyito').browse(cr,uid,bszamla_nyito[0],context=None).egyenleg_datuma)
    else:
        nyito_ertek=0
    '''megkeressük azokat a bejegyzéseket a tarh_bankbiz táblában amelyeknél biz_datum nagyobb mint a nyito_datum, ÉS
    kisebb vagy egyenlő mint a datum ÉS a bankszamla_thaz = bankszamla'''
    osszesen=nyito_ertek
    ref_bankbiz=self.pool.get('tarh.bankbiz')
    ref_bankbiz_sor = self.pool.get('tarh.bankbiz.sor')
    #talalt_elemek=ref_bankbiz.search(cr,uid,[('bankszamla_thaz','=',bankszamla),('biz_datum','>',nyito_datum),('biz_datum','<=',datum)],context=None)
    talalt_elemek=ref_bankbiz.search(cr,uid,[('bankszamla_thaz','=',bankszamla)],context=None)
    if talalt_elemek:#ha talalt megfelelo bankbizonylatot akkor vegigmegyunk a sorokon
        talalt_sorok=ref_bankbiz_sor.search(cr,uid,[('bankbiz_id','in',talalt_elemek),('erteknap','>',nyito_datum),('erteknap','<=',datum)],context=0)
        if talalt_sorok:
            for sor in talalt_sorok:
                rec_elem= ref_bankbiz_sor.browse(cr,uid,sor,context=None)
                osszesen = osszesen + rec_elem.jovairas_ossz - rec_elem.terheles_ossz
    return(osszesen)

