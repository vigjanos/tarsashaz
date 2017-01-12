# -*- coding: utf-8 -*-
'''
Created on 2014.06.02.

@author: vigjanos
'''
from openerp.osv import osv, fields
from datetime import date, time, datetime, timedelta
from openerp.tools.translate import _
from openerp import tools
from seged import *
import sys

reload(sys)
sys.setdefaultencoding('utf8')

class tarh_bankbiz(osv.osv):
    _name = "tarh.bankbiz"

    def amount_all (self, cr, uid, ids, field_name, arg, context=None):  #
        res = {}
        for bankbiz in self.browse(cr, uid, ids, context=context):
            res[bankbiz.id] = {
                'sum_jovairas': 0,
                'sum_terheles': 0,
                'sum_tranzakciok': 0,
            }
            val = val1 = 0
            for line in bankbiz.bankbiz_sor:
                val1 += line.terheles_ossz
                val += line.jovairas_ossz
            res[bankbiz.id]['sum_jovairas'] = val
            res[bankbiz.id]['sum_terheles'] = val1
            res[bankbiz.id]['sum_tranzakciok'] = res[bankbiz.id]['sum_jovairas'] - res[bankbiz.id]['sum_terheles']
        return res

    def _get_order (self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('tarh.bankbiz.sor').browse(cr, uid, ids, context=context):
            result[line.bankbiz_id.id] = True
        return result.keys()

    def nyitoegyenlegek (self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        osszeg = self.browse(cr, uid, ids, context).sum_tranzakciok
        bszamla_thaz = self.browse(cr, uid, ids, context).bankszamla_thaz.id
        if bszamla_thaz:
            biz_datum = self.browse(cr, uid, ids, context).biz_datum
            _nyito_hiv = self.pool.get('tarh.bszamla.nyito')
            sorszam = _nyito_hiv.search(cr, uid, [('tarh_bszamla', '=', bszamla_thaz)])
            '''meg kell nezni, hogy ha nincs egyenleg'''
            if sorszam:
                kezdoegyenleg = _nyito_hiv.browse(cr, uid, sorszam[0], context=context).egyenleg
            else:
                kezdoegyenleg = 0
            _bizonylat = self.search(cr, uid,
                                     ['&', ('biz_datum', '<', biz_datum), ('bankszamla_thaz', '=', bszamla_thaz)],
                                     context=context)
            nyitoegyenleg = kezdoegyenleg
            if _bizonylat:
                for valtozo in _bizonylat:
                    nyitoegyenleg = nyitoegyenleg + self.browse(cr, uid, valtozo, context=context).sum_tranzakciok
            zaroegyenleg = nyitoegyenleg + osszeg
            # print osszeg, bszamla_thaz, biz_datum, nyitoegyenleg, "Zaroegyenleg: " ,zaroegyenleg
            res = {}
            rekordok = self.browse(cr, uid, ids, context)
            for rekord in rekordok:
                res[rekord.id] = nyitoegyenleg
        return res

    def zaroegyenlegek (self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        osszeg = self.browse(cr, uid, ids, context).sum_tranzakciok
        bszamla_thaz = self.browse(cr, uid, ids, context).bankszamla_thaz.id
        if bszamla_thaz:
            biz_datum = self.browse(cr, uid, ids, context).biz_datum
            _nyito_hiv = self.pool.get('tarh.bszamla.nyito')
            sorszam = _nyito_hiv.search(cr, uid, [('tarh_bszamla', '=', bszamla_thaz)])
            if sorszam:
                kezdoegyenleg = _nyito_hiv.browse(cr, uid, sorszam[0], context=context).egyenleg
            else:
                kezdoegyenleg = 0
            _bizonylat = self.search(cr, uid,
                                     ['&', ('biz_datum', '<', biz_datum), ('bankszamla_thaz', '=', bszamla_thaz)],
                                     context=context)
            nyitoegyenleg = kezdoegyenleg
            if _bizonylat:
                for valtozo in _bizonylat:
                    nyitoegyenleg = nyitoegyenleg + self.browse(cr, uid, valtozo, context=context).sum_tranzakciok
            zaroegyenleg = nyitoegyenleg + osszeg
            print osszeg, bszamla_thaz, biz_datum, nyitoegyenleg, "Zaroegyenleg: ", zaroegyenleg
            res = {}
            rekordok = self.browse(cr, uid, ids, context)
            for rekord in rekordok:
                res[rekord.id] = zaroegyenleg
        return res

    _columns = {
        'th_szamlatul': fields.many2one('res.partner', 'Tarsashaz',
                                        domain="[('is_company','=',True),('name','ilike','rsash')]", required=True),
        'bankszamla_thaz': fields.many2one('res.partner.bank', 'Bankszamla tarsashaz', required=True),
        'kivonatszam': fields.char('Sorszam', size=64, required=True),
        'biz_datum': fields.date('Datum', required=True), # felesleges!!!
        'erk_datum': fields.date('Beerkezes datuma', required=True),
        'bankbiz_sor': fields.one2many('tarh.bankbiz.sor', 'bankbiz_id', 'tranzakcio sor'),
        #    'sum_jovairas':fields.integer('Osszes jovairas'),
        'sum_jovairas': fields.function(amount_all, string='Jovairasok', type='integer',
                                        store={
                                            'tarh.bankbiz': (lambda self, cr, uid, ids, c={}: ids, ['bankbiz_sor'], 10),
                                            'tarh.bankbiz.sor': (_get_order, ['terheles_ossz', 'jovairas_ossz'], 10),
                                        },
                                        multi='sums', help="Az osszes jovairas", track_visibility='always'),

        #    'sum_terheles':fields.integer('Osszes terheles'),
        'sum_terheles': fields.function(amount_all, string='Terhelesek', type='integer',
                                        store={
                                            'tarh.bankbiz': (lambda self, cr, uid, ids, c={}: ids, ['bankbiz_sor'], 10),
                                            'tarh.bankbiz.sor': (_get_order, ['terheles_ossz', 'jovairas_ossz'], 10),
                                        },
                                        multi='sums', help="Az osszes terheles", track_visibility='always'),

        #    'sum_tranzakciok':fields.integer('Tranzakciok osszege'),
        'sum_tranzakciok': fields.function(amount_all, string='Osszesen', type='integer',
                                           store={
                                               'tarh.bankbiz': (
                                               lambda self, cr, uid, ids, c={}: ids, ['bankbiz_sor'], 10),
                                               'tarh.bankbiz.sor': (_get_order, ['terheles_ossz', 'jovairas_ossz'], 10),
                                           },
                                           multi='sums', help="A tranzakciok osszege", track_visibility='always'),

        'nyitoegyenleg': fields.function(nyitoegyenlegek, type='integer', store=False, method=True,
                                         string='Nyitoegyenleg', readonly=True),
        'zaroegyenleg': fields.function(zaroegyenlegek, type='integer', store=False, method=True, string='Zaroegyenleg',
                                        readonly=True),
    }

    # columns vege


    _order = 'kivonatszam desc'

    #    _defaults = {
    #    'biz_datum':fields.date.context_today,
    #    'erk_datum':fields.date.context_today,
    #    }

    #    def onchange_sum_tranzakciok(self,cr,uid,ids,bankszamla_thaz, biz_datum, sum_tranzakciok, context=None):
    #        nyito_egyenleg= self.pool.get('tarh.bszamla.nyito').search(cr, uid, [('id', '=', bankszamla_thaz)], context=context)
    #
    #        return

    def button_dummy (self, cr, uid, ids, context=None):
        return True

    def onchange_th_szamlatul (self, cr, uid, ids, th_szamlatul, context=None):
        eredmeny = {}
        if th_szamlatul:
            #            megkeressuk a res.partner.bank tablaban azt a bankot ahol a partne.id = a tarsashazunkkal
            bankszamlak = self.pool.get('res.partner.bank').search(cr, uid, ['&', ('partner_id', '=', th_szamlatul),
                                                                             ('acc_number', 'ilike', 'zemeltet')],
                                                                   context=context)
            # listat ad vissza
            if len(bankszamlak):
                elso_szamla = bankszamlak[0]  # a lista elso eleme
                eredmeny['bankszamla_thaz'] = elso_szamla
            else:
                eredmeny['bankszamla_thaz'] = ''

        return {'value': eredmeny}

    def onchange_erk_datum (self, cr, uid, ids, erk_datum, context=None):
        eredmeny = {}
        if erk_datum:
            eredmeny['biz_datum'] = erk_datum
        else:
            eredmeny['biz_datum'] = ''
        return {'value': eredmeny}


'''TODO meg kell csinálni, hogy ha változik a dátum és már van sor rögzítve akkor az ehhez a bankbiz-hoz tartozó
összes sor elemének a erteknap-ját állítsa (kérdés, hogy el van e az már mentve --> TESZT)'''

tarh_bankbiz()


class tarh_bankbiz_sor(osv.osv):
    _name = "tarh.bankbiz.sor"

    _columns = {
        'bankbiz_id': fields.many2one('tarh.bankbiz', 'Bankbizonylat referencia', ondelete='cascade', select=True,
                                      readonly=True),
        'partner': fields.many2one('res.partner', 'partner neve', required=True),
        'partner_banksz': fields.many2one('res.partner.bank', 'Partner bankszamla'),
        'erteknap': fields.date('Erteknap', required=True),
        'jovairas': fields.boolean('Jovairas e'),
        'tarh_tranzakcio': fields.many2one('tarh.tranzakcio', 'tranzakcio megnevezes', required=True),
        'terheles_ossz': fields.integer('Terheles'),
        'jovairas_ossz': fields.integer('Jovairas'),
        'megjegyzes': fields.text('Megjegyzes'),
        'eloiras': fields.text('Eloiras'),
        'postai': fields.boolean('Csekkes befizetes'),
    }

    _defaults = {
        'jovairas': True,
    }

    def csekkes_befiz (self, cr, uid, ids, postai, lako_id, tarsashaz_id, context=None):
        ref_res_partner = self.pool.get('res.partner')
        ref_tarh_eloiras_haz = self.pool.get('tarh.eloiras.haz')
        ref_tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
        erteknap = self.browse(cr, uid, ids, context=None).erteknap

        ''' Meg kell azt is nézni, hogy a lako_id lakója-e a tarsashaz_id-nek:
        Ha nem akkor visszatérünk a return-al
        '''
        lako_parent = ref_res_partner.browse(cr, uid, lako_id, context=None).parent_id.id

        if lako_parent and lako_parent == tarsashaz_id:
            print "lakója!"

            if postai:
                '''Ha bejelölték a csekkes befizetést, akkor meg kell nézni, hogy a háznak van-e előírása erre az időszakra
                csekkes befizetésre, ezt a tarh_eloiras_haz táblában rögzítettük. 
                '''
                lista_tarh_eloiras_haz = ref_tarh_eloiras_haz.search(cr, uid, [('eloir_kezd', '<=', erteknap),
                                                                               ('eloir_vege', '>=', erteknap),
                                                                               ('konyvelt_haz', '=', tarsashaz_id),
                                                                               ('eloirfajta.name', 'ilike', 'csekkes')],
                                                                     context=None)
                if lista_tarh_eloiras_haz:
                    eloiras_szama = ref_tarh_eloiras_haz.browse(cr, uid, lista_tarh_eloiras_haz[0],
                                                                context=None).eloirfajta.id
                    '''Hurrá van előírás a csekkre, nézzük meg, hogy nem rögzítettünk-e még erre a napra a tarh_lakoeloir_havi táblában!
                    '''
                    van_mar_eloirva = ref_tarh_lakoeloir_havi.search(cr, uid, [('eloir_datum', '=', erteknap),
                                                                               ('eloirfajta', '=', eloiras_szama),
                                                                               ('lako', '=', lako_id)], context=None)
                    if van_mar_eloirva:
                        return
                    else:
                        '''nincs még erre a napra ennek a lakónak csekkbefizetési előírás, akkor rögzítsünk egyet!'''
                        szeletelt = erteknap.split("-")
                        kiirando = {}
                        kiirando['ev'] = szeletelt[0]
                        kiirando['honap'] = szeletelt[1]
                        kiirando['tarsashaz'] = tarsashaz_id
                        kiirando['lako'] = lako_id
                        kiirando['eloirfajta'] = ref_tarh_eloiras_haz.browse(cr, uid, lista_tarh_eloiras_haz[0],
                                                                             context=None).eloirfajta.id
                        kiirando['osszeg'] = ref_tarh_eloiras_haz.browse(cr, uid, lista_tarh_eloiras_haz[0],
                                                                         context=None).osszeg
                        kiirando['eloir_datum'] = erteknap
                        ref_tarh_lakoeloir_havi.create(cr, uid, kiirando, context=None)
                        pass

                print "most lett bejelolve"
            else:
                eloiras_szamai = self.pool.get('eloiras.fajta').search(cr, uid, [('name', 'ilike', 'csekkes')],
                                                                       context=None)
                van_mar_eloirva = ref_tarh_lakoeloir_havi.search(cr, uid, [('eloir_datum', '=', erteknap),
                                                                           ('eloirfajta', '=', eloiras_szamai[0]),
                                                                           ('lako', '=', lako_id)], context=None)
                if van_mar_eloirva:
                    for eloiras in van_mar_eloirva:
                        print eloiras
                        sikerult = self.pool.get('tarh.lakoeloir.havi').unlink(cr, uid, eloiras, context=context)
                        print sikerult
                print "hamis most jeloltek ki"
        return

    def onchange_tranzakcio (self, cr, uid, ids, tranzakcio_id, context=None):
        eredmeny = {}
        ''' a tranzakcio tipusanal rogzitettektol fuggoen allitjuk a jovairast vagy terhelest'''
        if self.pool.get('tarh.tranzakcio').browse(cr, uid, tranzakcio_id, context=None).jovairas:
            eredmeny['jovairas'] = True
        else:
            eredmeny['jovairas'] = False
        '''Ha a felhasználó visszaváltoztat valami másra, és az nem kozos koltsegre valtozott akkor nullazzuk a jovairast es toroljuk az eloirast'''
        valtozott = self.pool.get('tarh.tranzakcio').search(cr, uid, [
            ('name', '=', 'Közös költség befizetés')], context=context)[0]
        if valtozott != tranzakcio_id:
            eredmeny['jovairas_ossz'] = 0
            # eredmeny['eloiras'] = ''

        return {'value': eredmeny}

    '''
    A lakó kiválasztása után a tarh.eloiras.lako táblából kikeresi a lakó éppen aktuális előírásait, és megjegyzésben
    feldobja az adatrögzítőnek.
    A bankbizonylat dátumát alapértelmezésben beállítja a sor dátumához.
    '''

    def onchange_partneruj (self, cr, uid, ids, biz_datum, tulajdonos, context=None):
        eredmeny = {}
        retStr = ''
        ret_ossz = 0
        if tulajdonos:
            if self.pool.get('res.partner').browse(cr, uid, tulajdonos, context=context).is_company == False:
                ret_ossz = 0  # ebben tartjuk a fizetendo havi osszeget osszesitve
                _szoveg_eloir = []  # ebben lesznek az eloiras szovegei 
                _osszeg_eloir = []  # ebben lesznek az eloirasok osszegei 
                _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
                _eloiras_fajta = self.pool.get('eloiras.fajta')
                _res_partner = self.pool.get('res.partner')
                eloirasok = _tarh_eloiras_lako.search(cr, uid,
                                                      ['&', ('lako', '=', tulajdonos), ('eloir_vege', '>=', biz_datum),
                                                       ('eloir_kezd', '<=', biz_datum)], context=context)
                for valtozo in eloirasok:
                    szov_eloir = _tarh_eloiras_lako.browse(cr, uid, valtozo, context=context).eloirfajta.name
                    ossz_eloir = _tarh_eloiras_lako.browse(cr, uid, valtozo, context=context).osszeg
                    _szoveg_eloir.append(szov_eloir)
                    _osszeg_eloir.append(ossz_eloir)
                    ret_ossz = ret_ossz + ossz_eloir
                for szamlalo in range(0, len(_szoveg_eloir)):
                    retStr = retStr + _szoveg_eloir[szamlalo] + ' ' + str(int(_osszeg_eloir[szamlalo])) + '\n'
                retStr = retStr + 'Összesen: ' + str(int(ret_ossz))
                '''
                TODO meg kell nézni az előírás dátumát, hozzáigazítani a bizonylat dátumához KÉSZ!!!
                '''


                # az eloirast pedig alapbol beirjuk a jovairasba (kesobb figyelni kell, hogy nehogy irjon a terhelesbe,
                # meg a jovairasba is egyszerre)
                if ret_ossz:
                    '''ha van eloirt osszeg azaz a ret_ossz nem nulla, akkor a tarh_tranzakcio t beallitjuk kozos koltsegre,'''
                    _tranz_szam = self.pool.get('tarh.tranzakcio')
                    kozos_ktg_szama = _tranz_szam.search(cr, uid, [
                        ('name', '=', 'Közös költség befizetés')], context=context)
                    eredmeny['tarh_tranzakcio'] = kozos_ktg_szama[0]
                    eredmeny['jovairas_ossz'] = ret_ossz

                eredmeny['eloiras'] = retStr
            else:
                eredmeny['eloiras'] = ''

        if biz_datum:
            eredmeny['erteknap'] = biz_datum
        else:
            eredmeny['erteknap'] = ''

        return {'value': eredmeny}


tarh_bankbiz_sor()


class tarh_tranzakcio(osv.osv):
    _name = "tarh.tranzakcio"
    _columns = {
        'name': fields.char('Tranzakcio_fajtaja', size=64, required=True),
        'jovairas': fields.boolean('bevetel'),
    }
    _defaults = {
        'jovairas': True
    }
    _order = 'name'


tarh_tranzakcio()


class tarh_bszamla_nyito(osv.osv):
    _name = "tarh.bszamla.nyito"
    _columns = {
        'tarh_bszamla': fields.many2one('res.partner.bank', 'Bankszamla'),
        'egyenleg_datuma': fields.date('kezdo datum'),
        'egyenleg': fields.integer('Datumkor az egyenleg'),
    }


tarh_bszamla_nyito()


class tarh_lako_nyito(osv.osv):
    _name = "tarh.lako.nyito"
    _columns = {
        'tarh_lako': fields.many2one('res.partner', 'Lakastulajdonos'),
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz'),
        'egyenleg_datuma': fields.date('kezdo datum'),
        'egyenleg': fields.integer('Datumkor az egyenleg'),
    }
    _defaults = {
        'egyenleg_datuma': date(2014, 12, 31),
    }

    def tulaj_valt (self, cr, uid, ids, tulaj_id, context=None):
        eredmeny = {}
        eredmeny['tarsashaz'] = self.pool.get('res.partner').browse(cr, uid, tulaj_id, context=None).parent_id
        return {'value': eredmeny}


tarh_lako_nyito()


class eloiras_fajta(osv.osv):
    _name = "eloiras.fajta"
    _columns = {
        'name': fields.char('Eloiras_fajtaja', size=64, required=True),
    }
    _order = 'name'


eloiras_fajta()


class tarh_eloiras_haz(osv.osv):
    '''Ebben a táblában tároljuk az egyes házakra a közgyűlésen hozott előírásokat, a m2-re eső közös költséget,
       egy főre jutó szemétdíjat, stb'''
    _name = "tarh.eloiras.haz"
    _columns = {
        'konyvelt_haz': fields.many2one('res.partner', 'Tarsashaz', domain="[('is_company','=', True)]"),
        'eloirfajta': fields.many2one('eloiras.fajta', 'Eloiras tipusa', required=True),
        'eloir_kezd': fields.date('Eloiras kezdete'),
        'eloir_vege': fields.date('Eloiras vege'),
        'esedekes': fields.integer('Esedekesseg napja'),
        'terulet_aranyos': fields.boolean('Terulettol fugg'),
        'rendszeres': fields.boolean('Rendszeres befizetes'),
        'osszeg': fields.integer('Fizetendo osszeg', required=True),
    }
    _defaults = {
        'terulet_aranyos': True,
        'rendszeres': True,
        'eloir_kezd': "2010-01-01",
        'eloir_vege': "2050-12-31"
    }


tarh_eloiras_haz()


# Ebben tároljuk
class tarh_eloiras_lako(osv.osv):
    '''ebben a táblában tároljuk a tarh_eloiras_haz táblából számítva, hogy az egyes lakásokban vízórától, m2-től,
       lakószámtól függően mennyi a havi befizetendő összeg, mettől meddig érvényes az előírás'''
    _name = "tarh.eloiras.lako"
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz', domain="[('is_company','=', True)]", required=True),
        'lako': fields.many2one('res.partner', 'Tulajdonos'),  # view-ben majd szűrni kell!
        'eloirfajta': fields.many2one('eloiras.fajta', 'Eloiras fajta'),
        'eloir_kezd': fields.date('Eloiras kezdete', required=True),
        'eloir_vege': fields.date('Eloiras vege'),
        'esedekes': fields.integer('Esedekesseg napja'),
        'osszeg': fields.integer('Fizetendo osszeg'),
        'alapterulet': fields.float('Alapterulet'),
        'vizora': fields.boolean('Vizora')
    }
    _defaults = {
        'esedekes': 10,
        'eloir_kezd': "2010-01-01",
        'eloir_vege': "2050-12-31"
    }

    def onchange_lako (self, cr, uid, ids, lako, context=None):
        eredmeny = {}
        if lako:
            _res_partner = self.pool.get('res.partner').browse(cr, uid, lako, context=context)
            alapterulet = _res_partner.alapterulet
            if _res_partner.vizora == 'v':
                vizora = True
            else:
                vizora = False

            eredmeny['alapterulet'] = alapterulet
            eredmeny['vizora'] = vizora
        return {'value': eredmeny}

    '''
    Az alábbi eljárás a tarh.eloiras.haz-ba beírt előírásokat lakónként berögzíti a tarh.eloiras.lako adattáblába
    figyelembe véve, hogy van-e vízórája, avagy nincs, valamint ha van felújítási alap, képviseleti díj, 
    vagy szemétdíj akkor azt is.
    '''

    def button_kozos_ktg_beir (self, cr, uid, ids, context):

        def str_to_date (str_date):
            szeletelt = str_date.split("-")
            return (date(int(szeletelt[0]), int(szeletelt[1]), int(szeletelt[2])))

        sajat = self.browse(cr, uid, ids, context)
        haz = sajat.tarsashaz.id
        kezdodatum = str_to_date(sajat.eloir_kezd)
        zarodatum = str_to_date(sajat.eloir_vege)
        _res_partner = self.pool.get('res.partner')
        _eloiras_fajta = self.pool.get('eloiras.fajta')
        lakok = _res_partner.search(cr, uid, [('parent_id', '=', haz)], context=context)
        eloirasok = self.pool.get('tarh.eloiras.haz').search(cr, uid, [('konyvelt_haz', '=', haz)], context=context)
        if eloirasok:
            _eloirasok = self.pool.get('tarh.eloiras.haz').browse(cr, uid, eloirasok, context)
            '''
            ha az albetét vásárlása nagyobb mint az előírás kezdete, akkor az előírás kezdete az albetét vásárlása lesz,
            ha az albetét eladása korábbi mint az előírás vége akkor az előírás vége az albetét eladása lesz,
            be kell jegyezni az előírást, ha az albetét vétele korábbi mint az előírás vége,
            be kell jegyezni az előírást, amennyiben az albetét eladása későbbi mint az előírás kezdete
            str_to_date azért kell mert a date típust vissza kell alakítanom dátumra mivel az adatbázisból visszaolvasva string lesz!
            '''
            if lakok:
                for lakosok in lakok:
                    aktual_adat = _res_partner.browse(cr, uid, lakosok, context)
                    alapterulet = aktual_adat.alapterulet
                    lakoszam = aktual_adat.lakoszam
                    veteli_datum = aktual_adat.alb_vetel
                    utca2 = aktual_adat.street2
                    albetet = aktual_adat.alb_szam
                    parkolo = aktual_adat.parkolohely
                    if utca2:
                        pass
                    else:
                        utca2 = ""
                    if veteli_datum:
                        vetel_datum = str_to_date(veteli_datum)
                    else:
                        vetel_datum = date(2010, 1, 1)
                    eladasi_datum = aktual_adat.alb_eladas
                    if eladasi_datum:
                        eladas_datum = str_to_date(eladasi_datum)
                    else:
                        eladas_datum = date(2050, 12, 31)
                    keresett=''
                    if aktual_adat.vizora == 'v':
                        _vizora = True
                        keresett = 'vízórával'
                    else:
                        if aktual_adat.vizora == 'n':
                            _vizora = False
                            keresett = 'nélkül'
                    for eloir in _eloirasok:
                        kezdodatum = str_to_date(eloir.eloir_kezd)
                        zarodatum = str_to_date(eloir.eloir_vege)
                        if eloir.terulet_aranyos:
                            szorzo = alapterulet
                        else:
                            szorzo = 1

                        if keresett <> '' and keresett in eloir.eloirfajta.name and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:
                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if 'alapba' in eloir.eloirfajta.name and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if 'épviseleti' in eloir.eloirfajta.name and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if ('Szemétdíj' in eloir.eloirfajta.name) and lakoszam > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * lakoszam
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if ('Költség hozzájárulás' in eloir.eloirfajta.name) and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if ('Technikai' in eloir.eloirfajta.name) and alapterulet > 0 and _vizora and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if ('Lakáskassza' in eloir.eloirfajta.name) and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if ('parkol' in eloir.eloirfajta.name) and 'park' in utca2 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                        if ('gar' in eloir.eloirfajta.name) and 'gar' in utca2 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                                # ezt szurtam be 2015-3-04

                        if ('parkol' in eloir.eloirfajta.name) and parkolo == 'v' and 'gar' not in utca2 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)

                            # eddig !

                        if 'Rendk' in eloir.eloirfajta.name and vetel_datum < zarodatum and eladas_datum > kezdodatum and alapterulet > 0 and albetet > 0:
                            if kezdodatum < vetel_datum:
                                kezdodatum = vetel_datum
                            if zarodatum > eladas_datum:
                                zarodatum = eladas_datum
                            eloirasfajta = eloir.eloirfajta.id
                            osszeg = eloir.osszeg
                            fizetendo = osszeg * szorzo
                            eredmeny = {'tarsashaz': haz, 'lako': lakosok, 'eloir_kezd': kezdodatum,
                                        'eloirfajta': eloirasfajta, 'vizora': _vizora, 'alapterulet': alapterulet,
                                        'osszeg': fizetendo, 'eloir_vege': zarodatum}
                            #van_e_mar = self.search(cr, uid, [('lako', '=', lakosok), ('eloir_kezd', '=', kezdodatum),
                            van_e_mar = self.search(cr, uid, [('lako', '=', lakosok),
                                                              ('eloirfajta', '=', eloirasfajta),
                                                              ('osszeg', '=', fizetendo)], context=None)
                            if van_e_mar:
                                pass
                            else:

                                kiirt_id = self.create(cr, uid, eredmeny, context=None)


                                # print kiirt_id

        # ez itt törli azt a rekordot amivel bevittük a sorozatot
        igaze = self.unlink(cr, uid, ids, context)
        return igaze


tarh_eloiras_lako()


class tarh_lakoeloir_havi(osv.osv):
    '''
    Ebben az osztályban tároljuk a tulajdonosok tényleges havi előírásait.
    Figyeli, hogy él e még az előírás (nem adták-e el a lakást) 
    Ezt meg kell szüntetni!!!!  csak a tarh_eloiras_lako marad!
    '''
    _name = 'tarh.lakoeloir.havi'
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz', domain="[('is_company','=', True)]", required=True),
        'lako': fields.many2one('res.partner', 'Tulajdonos', domain="['|',('active','=', True),('active','=', False)]"),  # view-ben majd szűrni kell!
        'eloirfajta': fields.many2one('eloiras.fajta', 'Eloiras fajta'),
        'ev': fields.integer('Eloiras eve:', required=True),
        'honap': fields.integer('Eloiras honapja', required=True),
        'osszeg': fields.integer('Eloiras osszege'),
        'eloir_datum': fields.date('Esedekes'),

    }

    _order = 'ev desc, honap desc'

    '''
    ez az függvény beírja az adatbázisba a megadott hónap és év konkrét előírásait.
    '''

    def havi_eloir_rogzit (self, cr, uid, ids, context):
        '''
        a megadott dátumnál megkeresi a hónap utolsó napjának dátumát
        '''

        def honap_utolsonap (self, datum):
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

        '''
        Sorban végigmegyünk a tarh_eloir_lako táblán és ha még aktuális az előírás
        (nem adták el a lakást stb.) akkor az előírást felmásolja a tarh_lakoeloir_havi
        adattáblába az adott év és hónap figyelembevételével.
        '''
        ev = self.browse(cr, uid, ids, context).ev
        honap = self.browse(cr, uid, ids, context).honap
        if ev and honap:
            # for honap in range(1,13):
            most_honap = honap_utolsonap(self, date(ev, honap, 1))
            _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
            havi_eloirasok = _tarh_eloiras_lako.search(cr, uid, ['&', ('eloir_vege', '>=', most_honap),
                                                                 ('eloir_kezd', '<', most_honap)], context=context)
            for sorszam in havi_eloirasok:
                egy_eloiras = _tarh_eloiras_lako.browse(cr, uid, sorszam, context)
                if egy_eloiras:
                    ere_lako = egy_eloiras.lako.id
                    ere_eloir = egy_eloiras.eloirfajta.id
                    ere_nap = egy_eloiras.esedekes
                    # ere_datum=honap_utolsonap(self,date(ev,honap,10))
                    ere_datum = date(ev, honap, ere_nap)  # esedekes napjara irjuk elo a lakonak a befizetest!
                    eredmeny = {
                        'tarsashaz': egy_eloiras.tarsashaz.id,
                        'lako': egy_eloiras.lako.id,
                        'eloirfajta': egy_eloiras.eloirfajta.id,
                        'ev': ev,
                        'honap': honap,
                        'osszeg': egy_eloiras.osszeg,
                        # eloiras a honap utolsó napja!
                        'eloir_datum': ere_datum
                    }
                    mar_rogzitet = self.search(cr, uid, [('lako', '=', ere_lako), ('eloirfajta', '=', ere_eloir),
                                                         ('eloir_datum', '=', ere_datum)], context=None)
                    if mar_rogzitet:
                        pass
                    else:
                        kiirt_id = self.create(cr, uid, eredmeny, context=None)
                    #            print kiirt_id
        igaze = self.unlink(cr, uid, ids, context)
        return igaze
        '''TODO be kellene építeni egy vizsgálatot, hogy amennyiben már létezik ennek a lakónak erre, a hónapra ez az előírása, akkor ne rögzítse be!KÉSZ!!!!
        '''

    def havi_eloir_rogzit2 (self, cr, uid, ids, context):
        '''
        a megadott dátumnál megkeresi a hónap utolsó napjának dátumát
        '''

        def honap_utolsonap (self, datum):
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

        '''
        Ugyanaz mint az előző, de csupán a megadott lakó adatait írja be
        '''
        ev = self.browse(cr, uid, ids, context).ev
        honap = self.browse(cr, uid, ids, context).honap
        tulaj = self.browse(cr, uid, ids, context).lako.id
        if ev and honap and tulaj:
            # for honap in range(1,13):
            most_honap = honap_utolsonap(self, date(ev, honap, 1))
            _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
            havi_eloirasok = _tarh_eloiras_lako.search(cr, uid, [('eloir_vege', '>=', most_honap),
                                                                 ('eloir_kezd', '<', most_honap), ('lako', '=', tulaj)],
                                                       context=context)
            for sorszam in havi_eloirasok:
                egy_eloiras = _tarh_eloiras_lako.browse(cr, uid, sorszam, context)
                if egy_eloiras:
                    ere_lako = egy_eloiras.lako.id
                    ere_eloir = egy_eloiras.eloirfajta.id
                    ere_nap = egy_eloiras.esedekes
                    # ere_datum=honap_utolsonap(self,date(ev,honap,10))
                    ere_datum = date(ev, honap, ere_nap)  # esedekes napjara irjuk elo a lakonak a befizetest!
                    ere_osszeg = egy_eloiras.osszeg
                    eredmeny = {
                        'tarsashaz': egy_eloiras.tarsashaz.id,
                        'lako': egy_eloiras.lako.id,
                        'eloirfajta': egy_eloiras.eloirfajta.id,
                        'ev': ev,
                        'honap': honap,
                        'osszeg': ere_osszeg,
                        # eloiras a honap utolsó napja!
                        'eloir_datum': ere_datum
                    }
                    mar_rogzitett = self.search(cr, uid, [('lako', '=', ere_lako), ('eloirfajta', '=', ere_eloir),
                                                         ('eloir_datum', '=', ere_datum),('osszeg','=',ere_osszeg)], context=None)
                    if mar_rogzitett:
                        pass
                    else:
                        kiirt_id = self.create(cr, uid, eredmeny, context=None)
                    #            print kiirt_id
        igaze = self.unlink(cr, uid, ids, context)
        return igaze

    def havi_eloir_rogzit3 (self, cr, uid, ids, context):
        '''
        a megadott dátumnál megkeresi a hónap utolsó napjának dátumát
        '''

        def honap_utolsonap (self, datum):
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

        '''
        Ugyanaz mint az előző, de csupán a megadott társasház adatait írja be
        '''
        ev = self.browse(cr, uid, ids, context).ev
        honap = self.browse(cr, uid, ids, context).honap
        tarshaz = self.browse(cr, uid, ids, context).tarsashaz.id
        if ev and honap and tarshaz:
            # for honap in range(1,13):
            most_honap = honap_utolsonap(self, date(ev, honap, 1))
            _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
            havi_eloirasok = _tarh_eloiras_lako.search(cr, uid, [('eloir_vege', '>=', most_honap),
                                                                 ('eloir_kezd', '<', most_honap),
                                                                 ('tarsashaz', '=', tarshaz)], context=context)
            for sorszam in havi_eloirasok:
                egy_eloiras = _tarh_eloiras_lako.browse(cr, uid, sorszam, context)
                if egy_eloiras:
                    ere_lako = egy_eloiras.lako.id
                    ere_eloir = egy_eloiras.eloirfajta.id
                    ere_nap = egy_eloiras.esedekes
                    # ere_datum=honap_utolsonap(self,date(ev,honap,10))
                    ere_datum = date(ev, honap, ere_nap)  # esedekes napjara irjuk elo a lakonak a befizetest!
                    ere_osszeg = egy_eloiras.osszeg
                    eredmeny = {
                        'tarsashaz': egy_eloiras.tarsashaz.id,
                        'lako': egy_eloiras.lako.id,
                        'eloirfajta': egy_eloiras.eloirfajta.id,
                        'ev': ev,
                        'honap': honap,
                        'osszeg': ere_osszeg,
                        # eloiras a honap utolsó napja! VOLT DE 10-re MEGVALTOZTATTAM!!!
                        'eloir_datum': ere_datum
                    }
                    mar_rogzitett = self.search(cr, uid, [('lako', '=', ere_lako), ('eloirfajta', '=', ere_eloir),
                                                         ('eloir_datum', '=', ere_datum),('osszeg','=',ere_osszeg)], context=None)
                    if mar_rogzitett:
                        pass
                    else:
                        kiirt_id = self.create(cr, uid, eredmeny, context=None)
                    #            print kiirt_id
        igaze = self.unlink(cr, uid, ids, context)
        return igaze


tarh_lakoeloir_havi()


class tarh_lakaselad(osv.osv):
    _name = 'tarh.lakaselad'
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz', domain="[('is_company','=', True)]", required=True),
        'elado': fields.many2one('res.partner', 'Elado', required=True),  # view-ben majd szűrni kell!
        'uj_tulajdonos': fields.char('Uj tulaj nev', required=True),
        'eladas_datum': fields.date('Eladas datuma', required=True),
        'vetel_datum': fields.date('Hasznalatbavetel', required=True),
        'email': fields.char('Vevo email'),
        'telefon': fields.char('Vevo telefon'),
        'mobile':fields.char('Vevo mobil'),
        'nyitott':fields.boolean('Nyitott'),

    }
    _defaults = {
        'mobile' : '',
        'nyitott':True
    }
    '''
    Amikor egy lakó eladja a lakását egy másik személynek:
    -beolvassuk az eladó összes adatát egy dict-be
    -vevő adatait beolvassuk a tarh_lakaselad tábláról
    -beállítjuk az eladónál az eladási, vevőnél a vételi dátumot,
    -létrehozzuk a társasházban ugyanarra az albetétre a vevő adatait
    
    def str_to_date(str_date):
            szeletelt=str_date.split("-")
            return(date( int(szeletelt[0]),int(szeletelt[1]),int(szeletelt[2])))
    '''

    def lakaselad_rogzit (self, cr, uid, ids, context):

        if self.browse(cr,uid,ids,context=None).nyitott:


            '''
            a megadott dátumnál megkeresi a hónap utolsó napjának dátumát
            '''

            def honap_utolsonap (self, datum):
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

            def str_to_date (str_date):
                szeletelt = str_date.split("-")
                return (date(int(szeletelt[0]), int(szeletelt[1]), int(szeletelt[2])))

            elado_valtozas = {}
            _res_partner = self.pool.get('res.partner')
            _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
            _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
            tarsashaz_name = self.browse(cr, uid, ids, context).tarsashaz.name
            tarsashaz_id = self.browse(cr, uid, ids, context).tarsashaz.id
            elado = self.browse(cr, uid, ids, context).elado.id
            uj_tulajdonos = self.browse(cr, uid, ids, context).uj_tulajdonos
            eladas_datum = str_to_date(self.browse(cr, uid, ids, context).eladas_datum)
            vetel_datum = str_to_date(self.browse(cr, uid, ids, context).vetel_datum)
            email = self.browse(cr, uid, ids, context).email
            if email:
                pass
            else:
                email=''
            telefon = self.browse(cr, uid, ids, context).telefon
            if telefon:
                pass
            else:
                telefon=''
            mobil = self.browse(cr, uid, ids, context).mobile
            elado_adatai = _res_partner.copy_data(cr, uid, elado, default=None, context=context)
            vevo_adatai = elado_adatai
            vevo_adatai['name'] = uj_tulajdonos
            vevo_adatai['display_name'] = tarsashaz_name, ', ', uj_tulajdonos
            vevo_adatai['email'] = email
            vevo_adatai['phone'] = telefon
            vevo_adatai['mobile'] = mobil
            vevo_adatai['comment'] = ''
            vevo_adatai['alb_vetel'] = vetel_datum
            vevo_adatai['postai'] = False
            vevo_adatai['levcim'] = ''

            # print sikeres
            vevo_id = _res_partner.create(cr, uid, vevo_adatai, context=None)
            # print vevo_id
            '''
            - meg kell keresni a tarh.eloiras.lako tablaban az eladó előírásait,

            ( ha az eladási dátum kisebb mint az előírás vége akkor) be kell állítani az előírás végének az eladási dátumot.
            - generálni kell az új tulajdonos részére ugyanezeket az előírásokat, a vételi dátum kezdettel

            '''
            if vevo_id:
                elado_eloiras_idk = _tarh_eloiras_lako.search(cr, uid, [('lako', '=', elado)], context=None)
                elado_eloirasai = _tarh_eloiras_lako.browse(cr, uid, elado_eloiras_idk, context=None)
                for ela_eloir in elado_eloirasai:
                    elado_eloiras_valtozas = {}
                    elado_eloiras_adatai = _tarh_eloiras_lako.copy_data(cr, uid, ela_eloir.id, default=None, context=None)
                    vevo_eloiras_adatai = elado_eloiras_adatai.copy()

                    # ha az eloiras vege nagyobb mint a vetel datuma
                    if str_to_date(ela_eloir.eloir_vege) > vetel_datum:
                        vevo_eloiras_adatai['lako'] = vevo_id
                        '''Ha az előírás kezdete későbbi mint a vételi dátum akkor a régi előírás kezdete megmarad!'''
                        if str_to_date(ela_eloir.eloir_kezd) < vetel_datum:
                            vevo_eloiras_adatai['eloir_kezd'] = vetel_datum
                        vevo_eloiras_id = _tarh_eloiras_lako.create(cr, uid, vevo_eloiras_adatai, context=None)

                    if eladas_datum < str_to_date(ela_eloir.eloir_vege):
                        elado_eloiras_valtozas['eloir_vege'] = eladas_datum
                    sikeres = _tarh_eloiras_lako.write(cr, uid, ela_eloir.id, elado_eloiras_valtozas, context=None)
                '''
                - meg kell nézni, hogy a tarh.lakoeloir.havi táblában eladás utáni dátummal a régi lakó már ne szerepeljen,
                - az eladás dátuma utáni összes hónap előírását töröljük a havi előírások közül
                '''
                elado_havi_eloirasai = _tarh_lakoeloir_havi.search(cr, uid, [('lako', '=', elado)], context=None)
                for sorszam in elado_havi_eloirasai:
                    ela_havi_eloir = _tarh_lakoeloir_havi.browse(cr, uid, sorszam, context=None)
                    if ela_havi_eloir:
                        ev = ela_havi_eloir.ev
                        honap = ela_havi_eloir.honap
                        eloiras_honapja = honap_utolsonap(self, date(ev, honap, 1))
                        '''nem értem hogy az eladás dátuma mi a picsáért string és nem date!!!'''

                        if eloiras_honapja > eladas_datum:
                            '''törölni kell a havi előírás táblájából'''
                            igaze = _tarh_lakoeloir_havi.unlink(cr, uid, ela_havi_eloir.id, context=None)

                '''
                - a vevő oldaláról meg kell nézni, hogy a vétel utáni időpontokban hány havi bejegyzés van már a havi
                  előírások között, a vevő előírásai szerepelnek-e már, ha nem akkor be kell rögzítenünk.
                '''

                ev = vetel_datum.year
                honap = vetel_datum.month
                '''amikor az aktuáTODO  be kell majd állítania vevő vételkori tartozást a tulajdonosok nyitóegyenlege
                táblában nulláralis hónapra már van bármilyen előírás akkor előírjuk a vevőnek is a havit. '''
                darab = _tarh_lakoeloir_havi.search(cr, uid, [('ev', '=', ev), ('honap', '=', honap)], limit=5,
                                                    context=None, count=True)
                while darab > 0:
                    most_datum = honap_utolsonap(self, date(ev, honap, 1))
                    '''van már a hónapra előírás, megnézzük,hogy van e már a vevőre előírás'''
                    vevo_van_e = _tarh_lakoeloir_havi.search(cr, uid, [('ev', '=', ev), ('honap', '=', honap),
                                                                       ('lako', '=', vevo_id)], context=None, count=True)
                    if vevo_van_e == 0:
                        '''nincs még havi előírás a vevőre, így akkor előírjuk
                        de csak akkor, ha az előírás dátuma passzol a beírandó dátumhoz'''
                        eloiras_sorszamok = _tarh_eloiras_lako.search(cr, uid, [('lako', '=', vevo_id)], context=None)
                        for sorszam in eloiras_sorszamok:
                            egy_eloiras = _tarh_eloiras_lako.browse(cr, uid, sorszam, context=None)
                            if egy_eloiras:
                                if most_datum > str_to_date(egy_eloiras.eloir_kezd) and most_datum <= str_to_date(
                                        egy_eloiras.eloir_vege):
                                    eredmeny = {
                                        'tarsashaz': egy_eloiras.tarsashaz.id,
                                        'lako': egy_eloiras.lako.id,
                                        'eloirfajta': egy_eloiras.eloirfajta.id,
                                        'ev': ev,
                                        'honap': honap,
                                        'osszeg': egy_eloiras.osszeg,
                                        'eloir_datum': date(ev, honap, 10)
                                        # most_datum helyett, mert ujabban 10-e az eloiras datuma!!!
                                    }
                                    kiirt_id = _tarh_lakoeloir_havi.create(cr, uid, eredmeny, context=None)
                                    print kiirt_id

                    ''' növeli egyel év-hónap'''
                    if honap == 12:
                        honap = 1
                        ev = ev + 1
                    else:
                        honap = honap + 1
                    darab = _tarh_lakoeloir_havi.search(cr, uid, [('ev', '=', ev), ('honap', '=', honap)], limit=5,
                                                        context=None, count=True)
                    print darab
                    '''itt a while vége'''

                '''létrehoznunk a vétel dátumára a vevőnek egy nullás nyitóegyenleget!'''
                _nyitoegyenleg=self.pool.get('tarh.lako.nyito')
                nyito_adatok = {
                    'tarh_lako':vevo_id,
                    'tarsashaz':tarsashaz_id,
                    'egyenleg_datuma':vetel_datum,
                    'egyenleg': 0
                }
                _nyitoegyenleg.create(cr,uid,nyito_adatok,context=None)

                elado_valtozas['alb_eladas'] = eladas_datum
                elado_valtozas['active'] = False
                sikeres = _res_partner.write(cr, uid, elado, elado_valtozas, context=None)
        self.write(cr,uid,ids,{'nyitott':False}) # ezt jól beállítjuk, hogy ne lehessen mégegyszer eladni!
        return


tarh_lakaselad()


class my_report(osv.osv):
    _name = "my.report"
    _auto = False
    _columns = {
        'th_szamlatul': fields.many2one('res.partner', 'Tarsashaz', readonly=True,\
                                        domain="[('is_company','=', True),('name','ilike','társasház')]"),
        'erteknap': fields.date('Konyveles napja', readonly=True),
        'partner': fields.many2one('res.partner', 'partner', readonly=True),
        'jovairas': fields.integer('Jovairas', readonly=True),
        'terheles': fields.integer('Terheles', readonly=True),
        'tarh_tranzakcio': fields.many2one('tarh.tranzakcio', 'tranzakcio', readonly=True),
        'megjegyzes': fields.text('Megjegyzes', readonly=True),
        'kivonatszam': fields.char('Kivonatszam', size=64, readonly=True),
        'bankszamla_thaz': fields.many2one('res.partner.bank', 'Bankszamla tarsashaz', readonly=True),
        'postan': fields.boolean('Postai befizetes', readonly=True),

    }
    _order = 'erteknap desc'

    def init (self, cr):
        tools.sql.drop_view_if_exists(cr, 'my_report')
        cr.execute("""
        
        create or replace view my_report as 
        (select  tarh_bankbiz_sor.id as id, th_szamlatul as th_szamlatul, erteknap as erteknap, 
        partner as partner, jovairas_ossz as jovairas, terheles_ossz as terheles, tarh_tranzakcio as tarh_tranzakcio,
        tarh_bankbiz_sor.megjegyzes as megjegyzes, kivonatszam as kivonatszam, bankszamla_thaz as bankszamla_thaz, postai as postan
        from tarh_bankbiz_sor join tarh_bankbiz on tarh_bankbiz_sor.bankbiz_id=tarh_bankbiz.id )
 
                    """
                   )


my_report()

# ez mar nem hasznalt, majd ki kell szedni!!!
"""
class tarh_haz_havijel(osv.osv):
    _name='tarh.haz.havijel'   
    _columns = {
          'kezdatum':fields.date('Kezdo datum'),
          'vegdatum':fields.date('Befejezo datum'),
          'th_szamlatul':fields.many2one('res.partner', 'Tarsashaz' ),
          'erteknap':fields.date('Konyveles napja' ),
          'partner':fields.many2one('res.partner', 'partner'),
          'jovairas':fields.integer('Jovairas'),
          'terheles':fields.integer('Terheles'),
          'terhel_min':fields.integer('Terheles minusz'),
          'tarh_tranzakcio':fields.many2one('tarh.tranzakcio', 'tranzakcio'),
          'megjegyzes':fields.text('Megjegyzes'),
          'kivonatszam':fields.char('Kivonatszam', size=64),
          'bankszamla_thaz':fields.many2one('res.partner.bank', 'Bankszamla tarsashaz')
                }
    '''
    A következő eljárásban a tranzakciók alapján csoportosítjuk a könyvelt bankszámlák sorait,
    a kezdő- és végdátum között, a megadott társasház minden bankszámlájára.
    Ezeket a sorokat beírjuk a tarh_haz_havijel táblába, amelyből így majd tudunk már aeroo reportot csinálni
    '''
    def havijel_beir(self,cr,uid,ids,context):
        '''az aktuális rekordon kívül töröljük az táblából a többi régi rekordot'''
        sajat_id=self.browse(cr, uid, ids, context=None).id
        torlendok=self.search(cr,uid,[('id','!=',sajat_id)])
        self.unlink(cr, uid, torlendok, context=None)
        '''kiolvassuk a lapról az időszakokat, a listázandó társasházat és a bankszámlát'''
        _kezdatum=self.browse(cr,uid,ids,context=None).kezdatum
        _vegdatum=self.browse(cr,uid,ids,context=None).vegdatum
        _szamlatul=self.browse(cr,uid,ids,context=None).th_szamlatul.id
        _bankszamla=self.browse(cr,uid,ids,context=None).bankszamla_thaz.id
        '''Tranzakciónként összeadjuk a tranzakciófajtákat a megadott társasház megadott 
           bankszámlájának megadott időintervallumában és beleírjuk a táblába''' 
        conn_str="select sum(terheles) as terheles, sum(my_report.jovairas) as jovairas, tarh_tranzakcio as tarh_tranzakcio_id"\
        " from my_report join tarh_tranzakcio on tarh_tranzakcio=tarh_tranzakcio.id where th_szamlatul="+str(_szamlatul)+""\
        " and erteknap between '"+_kezdatum+"' and '"+_vegdatum+"' and bankszamla_thaz="+str(_bankszamla)+" group by tarh_tranzakcio"
        cr.execute(conn_str)
        eredmeny = cr.dictfetchall()
        kiirando={}
        for row in eredmeny:
            kiirando['kezdatum']=_kezdatum
            kiirando['vegdatum']=_vegdatum
            kiirando['th_szamlatul']=_szamlatul
            kiirando['jovairas']=row['jovairas']
            kiirando['terheles']=row['terheles']
            kiirando['terhel_min']=row['terheles']*-1
            kiirando['tarh_tranzakcio']=row['tarh_tranzakcio_id']
            kiirando['bankszamla_thaz']=_bankszamla
            self.create(cr,uid,kiirando,context=None)
        '''töröljük a rekordot, amivel létrehoztuk az egészet '''
        self.unlink(cr, uid, sajat_id, context=None)
        return
    
tarh_haz_havijel()
"""


class tarh_lako_havijel(osv.osv):
    _name = 'tarh.lako.havijel'
    _columns = {
        'kezdatum': fields.date('Kezdo datum', required=True),
        'vegdatum': fields.date('Befejezo datum', required=True),
        'lekerdatum': fields.date('Lekerdezes datum', required=True),
        'tulaj': fields.many2one('res.partner', 'Tulajdonos', required=True),
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz'),
        'bankszamla': fields.char('Tarsahaz uzemeltetesi szamlaja'),
        'sor_id': fields.one2many('tarh.lako.havijel.sor', 'havijel_id', 'kapocs2'),
    }
    mai_datum = fields.date.context_today
    pass

    _defaults = {
        'kezdatum': '2016-01-01',
        'vegdatum': fields.date.context_today,
        'lekerdatum': fields.date.context_today,
    }

    def onchange_tarsashaz (self, cr, uid, ids, tarsashaz, context=None):
        eredmeny = {}
        if tarsashaz:
            uzemeltetesi = self.pool.get('res.partner.bank').search(cr, uid, [('partner_id', '=', tarsashaz),
                                                                              ('state', '=', 'bank_uzem')],
                                                                    context=None)
            if uzemeltetesi[0]:
                eredmeny['bankszamla'] = self.pool.get('res.partner.bank').browse(cr, uid, uzemeltetesi[0],
                                                                                  context=None).acc_number
        return {'value': eredmeny}

    '''Ebben az eljárásban a lakó időszakra vonatkozó elszámolását tudjuk megtekinteni a kezdatum és
    vegdatum között kilistázzuk az adott időszakra vonatkozó előírásokat és a megtörtént befizetéseket.'''

    def lako_havijel_beir (self, cr, uid, ids, context=None):

        def str_to_date (str_date):
            szeletelt = str_date.split("-")
            return (date(int(szeletelt[0]), int(szeletelt[1]), int(szeletelt[2])))

        def nyitoegyenleg (self, _lako, datum):
            sum_eloiras = 0
            sum_jovairas = 0
            _tarh_lako_nyito = self.pool.get('tarh.lako.nyito')
            talalt_id = _tarh_lako_nyito.search(cr, uid, [('tarh_lako', '=', _lako)], context=context)
            if talalt_id:  # ha van nyitoegyenleg rogzitve
                nyito_dok = _tarh_lako_nyito.browse(cr, uid, talalt_id[0], context=None)
                _nyito_datum = nyito_dok.egyenleg_datuma
                _nyito_osszeg = nyito_dok.egyenleg
                # modositani kell majd, hogy a tarolt nyitoegyenleg es a lekerdezes kozotti eloirast-befizetest figyelembe vegye
                _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
                _my_report = self.pool.get('my.report')
                tarh_lakoeloir_havi_lista = _tarh_lakoeloir_havi.search(cr, uid, [('lako', '=', _lako),
                                                                                  ('eloir_datum', '>', _nyito_datum),
                                                                                  ('eloir_datum', '<=', datum)],
                                                                        context=context)  # datum szures kell bele!
                my_report_lista = _my_report.search(cr, uid, [('partner', '=', _lako), ('erteknap', '>', _nyito_datum),
                                                              ('erteknap', '<=', datum)],
                                                    context=context)  # datum szures kell bele!
                eloirasok = _tarh_lakoeloir_havi.browse(cr, uid, tarh_lakoeloir_havi_lista, context=None)
                befizetesek = _my_report.browse(cr, uid, my_report_lista, context=None)
                for befizetes in befizetesek:
                    _nyito_osszeg = _nyito_osszeg + befizetes.jovairas - befizetes.terheles
                for eloiras in eloirasok:
                    _nyito_osszeg = _nyito_osszeg - eloiras.osszeg
                # ha a kejerdezesi datum korabbi mint a nyitoegyenleg datuma, akkor a kezdeti datum a nyitoegyenleg datuma lesz
                _nyito_datum_date = str_to_date(_nyito_datum)
                if datum < _nyito_datum_date:
                    datum = _nyito_datum_date
                eredmeny = [datum, _nyito_osszeg, '']
            else:  # nincs nyitoegyenleg rögzitve
                eredmeny = [datum, 0, 'Nincs a lakóhoz nyitóegyenleg rögzítve!!!']
            return (eredmeny)

        sajat_id = self.browse(cr, uid, ids, context=None).id

        '''az aktuális rekordon kívül töröljük az táblából a többi régi rekordot
        torlendok=self.search(cr,uid,[('id','!=',sajat_id)])
        self.unlink(cr, uid, torlendok, context=None)
                
        NEM TÖRÖLJÜK MERT HA EGYSZERRE KÉT ADATLEKÉRDEZÉS FOLYIK, AKKOR EGYIK LETÖRÖLHETI A MÁSIKÉT
    
        De letöröljük a sorokat amelyek ehhez a lekérdezéshez tartoznak'''

        _havijel_sor_hiv = self.pool.get('tarh.lako.havijel.sor')
        torleno_sorok = _havijel_sor_hiv.search(cr, uid, [('havijel_id', '=', sajat_id)], context=None)
        _havijel_sor_hiv.unlink(cr, uid, torleno_sorok, context=None)

        '''Beolvassuk a lapról a kezdő és végdátumot, valamint a lakót, kiolvassuk a nyitógyenleg összegét és a dátumát'''

        _kezdatum = str_to_date(self.browse(cr, uid, ids, context=None).kezdatum)  # lekerdezes kezdete
        _vegdatum = str_to_date(self.browse(cr, uid, ids, context=None).vegdatum)  # lekerdezes vege
        _lako = self.browse(cr, uid, ids, context=None).tulaj.id  # onchange-ben majd a tarsashazat kivalsztjuk
        _tarsashaz = self.browse(cr, uid, ids, context=None).tarsashaz.id
        nyitoegy = nyitoegyenleg(self, _lako, _kezdatum)
        # kiirjuk az elso sorba a nyitoegyenleget
        kiirando = {}

        if len(nyitoegy[2]) == 0:  # nincs szoveg ,tehat volt nyitoegyenleg!
            kiirando['erteknap'] = nyitoegy[0]
            kiirando['szoveg'] = 'Nyitóegyenleg'
            kiirando['eloiras'] = 0
            kiirando['befizetes'] = nyitoegy[1]
            kiirando['havijel_id'] = sajat_id
            id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)

        else:
            kiirando['erteknap'] = nyitoegy[0]
            kiirando['szoveg'] = nyitoegy[2]
            kiirando['eloiras'] = 0
            kiirando['befizetes'] = nyitoegy[1]
            kiirando['havijel_id'] = sajat_id
            id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)
        # ha a lekerdezes bejezesi kisebb mint a nyitoegyenleg datuma akkor nincs ertekelheto adat

        if _vegdatum >= nyitoegy[0]:
            _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
            _my_report = self.pool.get('my.report')
            tarh_lakoeloir_havi_lista = _tarh_lakoeloir_havi.search(cr, uid, [('lako', '=', _lako),
                                                                              ('eloir_datum', '>', _kezdatum),
                                                                              ('eloir_datum', '<=', _vegdatum),
                                                                              ('eloir_datum', '>', nyitoegy[0])],
                                                                    context=context)
            my_report_lista = _my_report.search(cr, uid, [('partner', '=', _lako), ('erteknap', '>', _kezdatum),
                                                          ('erteknap', '<=', _vegdatum)], context=context)
            eloirasok = _tarh_lakoeloir_havi.browse(cr, uid, tarh_lakoeloir_havi_lista, context=None)
            befizetesek = _my_report.browse(cr, uid, my_report_lista, context=None)
            szumma = nyitoegy[1]

            for befizetes in befizetesek:
                # print befizetes.erteknap,' ',befizetes.tarh_tranzakcio.name,' ',befizetes.jovairas
                kiirando['erteknap'] = befizetes.erteknap
                kiirando['szoveg'] = befizetes.tarh_tranzakcio.name
                kiirando['eloiras'] = befizetes.terheles
                kiirando['befizetes'] = befizetes.jovairas
                kiirando['havijel_id'] = sajat_id
                szumma = szumma + befizetes.jovairas - befizetes.terheles
                id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)
            for eloiras in eloirasok:
                # print eloiras.eloir_datum,' ',eloiras.eloirfajta.name,' ', eloiras.osszeg
                kiirando['erteknap'] = eloiras.eloir_datum
                kiirando['szoveg'] = eloiras.eloirfajta.name
                kiirando['eloiras'] = eloiras.osszeg
                kiirando['befizetes'] = 0
                kiirando['havijel_id'] = sajat_id
                szumma = szumma - eloiras.osszeg
                id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)

            kiirando['erteknap'] = _vegdatum
            kiirando['szoveg'] = 'Aktuális egyenleg'
            kiirando['eloiras'] = 0
            kiirando['befizetes'] = szumma
            kiirando['havijel_id'] = sajat_id
            id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)
        else:
            kiirando['erteknap'] = _vegdatum
            kiirando['szoveg'] = 'Nincs az időpontra rögzített adat!!!'
            kiirando['eloiras'] = 0
            kiirando['befizetes'] = 0
            kiirando['havijel_id'] = sajat_id
            id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)

        '''töröljük a rekordot, amivel létrehoztuk az egészet'''
        #        self.unlink(cr, uid, sajat_id, context=None)

        return self.write(cr,uid,ids,{'lekerdatum':date.today()})

    def onchange_tul (self, cr, uid, ids, lako, kezdatum, vegdatum, context=None):
        '''
        megkeresi, hogy a lako melyik társasházhoz tartozik,
        ha a lakó nyitóegyenlege későbbi mint a kezdatum akkor módosítja azt,
        ha a vegdatum későbbi mint a társasház utolsó könyvelt dátuma, akkor módosítja azt
        :param cr:
        :param uid:
        :param ids:
        :param lako: tulajdonos
        :param kezdatum: eredetileg bevitt kezdődátum
        :param vegdatum: eredetileg bevitt záródátum
        :param context:
        :return:
        '''
        eredmeny = {}
        most = date.today()
        kezdo_datum = date(most.year-1,most.month,1)
        eredmeny['kezdatum'] = kezdo_datum
        if lako:
            nyito_datuma = kezdatum
            _tarh_lako_nyito = self.pool.get('tarh.lako.nyito')
            nyito_lista = _tarh_lako_nyito.search(cr,uid,[('tarh_lako','=',lako)],context=None)
            if nyito_lista:
                nyito_datuma = _tarh_lako_nyito.browse(cr,uid,nyito_lista[0], context=None).egyenleg_datuma
            _res_partner = self.pool.get('res.partner')
            tarsashaz = _res_partner.browse(cr, uid, lako, context=None).parent_id.id
            if tarsashaz:
                zarodatum= utolso_konyvelt_datum(self,cr,uid,tarsashaz)
                eredmeny['tarsashaz'] = tarsashaz
                eredmeny['vegdatum'] = zarodatum
            if kezdatum < nyito_datuma:
                eredmeny['kezdatum'] = nyito_datuma

        return {'value': eredmeny}


tarh_lako_havijel()


class tarh_lako_havijel_sor(osv.osv):
    _name = 'tarh.lako.havijel.sor'
    _columns = {
        'erteknap': fields.date('Konyveles napja'),
        'szoveg': fields.char('Eloiras', size=64),
        'eloiras': fields.integer('Eloiras'),
        'befizetes': fields.integer('Befizetes'),
        'havijel_id': fields.many2one('tarh.lako.havijel', 'kapocs', ondelete='cascade', select=True, readonly=True),
    }
    _order = 'erteknap, id'


tarh_lako_havijel_sor()


class phonecall_to_task(osv.osv):
    _inherit = ['crm.phonecall']

    def feladat (self, cr, uid, ids, context=None):
        print 'hellllllllllooo'
        telefonhivas = self.browse(cr, uid, ids[0], context=None)
        datum = telefonhivas.date
        szoveg = telefonhivas.name
        #raise osv.except_osv(("Figyelem!!!"),(" Hello itt egy hiba!"))
        raise osv.except_orm(_("Figyelem!!!"), _(" Ez me'g nem keszult el!!!"))
        return ()


phonecall_to_task()

"""
NAGY TODO LISTA

Meg kell csinálni, hogyha a bankbizonylaton utólag állítják át a dátumot, akkor írja át a hozzátartozó sorokon is!







WARNING_TYPES = [('warning', 'Warning'), ('info', 'Information'), ('error', 'Error')]
class warning(osv.osv_memory):
    _name = 'warning'
    _description = 'warning'
    _columns = {
    'type': fields.selection(WARNING_TYPES, string='Type', readonly=True),
    'title': fields.char(string="Title", size=100, readonly=True),
    'message': fields.text(string="Message", readonly=True),
    }
    _req_name = 'title'

    def _get_view_id(self, cr, uid):
       Get the view id
        @return: view id, or False if no view found
            
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'tarh_konyvel', 'warning_form')
        return res and res[1] or False

    def message(self, cr, uid, id, context):
        message = self.browse(cr, uid, id)
        message_type = [t[1]for t in WARNING_TYPES if message.type == t[0]][0]
        print '%s: %s' % (_(message_type), _(message.title))
        res = {
        'name': '%s: %s' % (_(message_type), _(message.title)),
        'view_type': 'form',
        'view_mode': 'form',
        'view_id': self._get_view_id(cr, uid),
        'res_model': 'warning',
        'domain': [],
        'context': context,
        'type': 'ir.actions.act_window',
        'target': 'new',
        'res_id': message.id
        }
        return res

    def warning(self, cr, uid, title, message, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'warning'})
        res = self.message(cr, uid, id, context)
        return res

    def info(self, cr, uid, title, message, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'info'})
        res = self.message(cr, uid, id, context)
        return res

    def error(self, cr, uid, title, message, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'error'})
        res = self.message(cr, uid, id, context)
        return res
    
#    def uzenet_feldob(self,cr,uid, ids, context=None):
#        valami = self.pool.get('warning')
#        ktya = valami.info(cr, uid, title='Export information', message="valami stirng Ĺitt van")
#        return ktya
"""
