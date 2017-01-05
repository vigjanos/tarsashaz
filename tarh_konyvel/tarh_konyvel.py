# -*- coding: ISO-8859-2 -*-
'''
Created on 2014.06.02.

@author: vigjanos
'''
from openerp.osv import osv, fields
from datetime import date, time, datetime, timedelta
from openerp.tools.translate import _
from openerp import tools
from seged import *

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


'''TODO meg kell csin�lni, hogy ha v�ltozik a d�tum �s m�r van sor r�gz�tve akkor az ehhez a bankbiz-hoz tartoz�
�sszes sor elem�nek a erteknap-j�t �ll�tsa (k�rd�s, hogy el van e az m�r mentve --> TESZT)'''

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

        ''' Meg kell azt is n�zni, hogy a lako_id lak�ja-e a tarsashaz_id-nek:
        Ha nem akkor visszat�r�nk a return-al
        '''
        lako_parent = ref_res_partner.browse(cr, uid, lako_id, context=None).parent_id.id

        if lako_parent and lako_parent == tarsashaz_id:
            print "lak�ja!"

            if postai:
                '''Ha bejel�lt�k a csekkes befizet�st, akkor meg kell n�zni, hogy a h�znak van-e el��r�sa erre az id�szakra
                csekkes befizet�sre, ezt a tarh_eloiras_haz t�bl�ban r�gz�tett�k. 
                '''
                lista_tarh_eloiras_haz = ref_tarh_eloiras_haz.search(cr, uid, [('eloir_kezd', '<=', erteknap),
                                                                               ('eloir_vege', '>=', erteknap),
                                                                               ('konyvelt_haz', '=', tarsashaz_id),
                                                                               ('eloirfajta.name', 'ilike', 'csekkes')],
                                                                     context=None)
                if lista_tarh_eloiras_haz:
                    eloiras_szama = ref_tarh_eloiras_haz.browse(cr, uid, lista_tarh_eloiras_haz[0],
                                                                context=None).eloirfajta.id
                    '''Hurr� van el��r�s a csekkre, n�zz�k meg, hogy nem r�gz�tett�nk-e m�g erre a napra a tarh_lakoeloir_havi t�bl�ban!
                    '''
                    van_mar_eloirva = ref_tarh_lakoeloir_havi.search(cr, uid, [('eloir_datum', '=', erteknap),
                                                                               ('eloirfajta', '=', eloiras_szama),
                                                                               ('lako', '=', lako_id)], context=None)
                    if van_mar_eloirva:
                        return
                    else:
                        '''nincs m�g erre a napra ennek a lak�nak csekkbefizet�si el��r�s, akkor r�gz�ts�nk egyet!'''
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
        '''Ha a felhaszn�l� visszav�ltoztat valami m�sra, �s az nem kozos koltsegre valtozott akkor nullazzuk a jovairast es toroljuk az eloirast'''
        valtozott = self.pool.get('tarh.tranzakcio').search(cr, uid, [
            ('name', '=', ('K�z�s k�lts�g befizet�s').decode('ISO-8859-2'))], context=context)[0]
        if valtozott != tranzakcio_id:
            eredmeny['jovairas_ossz'] = 0
            # eredmeny['eloiras'] = ''

        return {'value': eredmeny}

    '''
    A lak� kiv�laszt�sa ut�n a tarh.eloiras.lako t�bl�b�l kikeresi a lak� �ppen aktu�lis el��r�sait, �s megjegyz�sben
    feldobja az adatr�gz�t�nek.
    A bankbizonylat d�tum�t alap�rtelmez�sben be�ll�tja a sor d�tum�hoz.
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
                retStr = retStr + ('�sszesen: ').decode('ISO-8859-2') + str(int(ret_ossz))
                '''
                TODO meg kell n�zni az el��r�s d�tum�t, hozz�igaz�tani a bizonylat d�tum�hoz K�SZ!!!
                '''


                # az eloirast pedig alapbol beirjuk a jovairasba (kesobb figyelni kell, hogy nehogy irjon a terhelesbe,
                # meg a jovairasba is egyszerre)
                if ret_ossz:
                    '''ha van eloirt osszeg azaz a ret_ossz nem nulla, akkor a tarh_tranzakcio t beallitjuk kozos koltsegre,'''
                    _tranz_szam = self.pool.get('tarh.tranzakcio')
                    kozos_ktg_szama = _tranz_szam.search(cr, uid, [
                        ('name', '=', ('K�z�s k�lts�g befizet�s').decode('ISO-8859-2'))], context=context)
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
    '''Ebben a t�bl�ban t�roljuk az egyes h�zakra a k�zgy�l�sen hozott el��r�sokat, a m2-re es� k�z�s k�lts�get,
       egy f�re jut� szem�td�jat, stb'''
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


# Ebben t�roljuk
class tarh_eloiras_lako(osv.osv):
    '''ebben a t�bl�ban t�roljuk a tarh_eloiras_haz t�bl�b�l sz�m�tva, hogy az egyes lak�sokban v�z�r�t�l, m2-t�l,
       lak�sz�mt�l f�gg�en mennyi a havi befizetend� �sszeg, mett�l meddig �rv�nyes az el��r�s'''
    _name = "tarh.eloiras.lako"
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz', domain="[('is_company','=', True)]", required=True),
        'lako': fields.many2one('res.partner', 'Tulajdonos'),  # view-ben majd sz�rni kell!
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
    Az al�bbi elj�r�s a tarh.eloiras.haz-ba be�rt el��r�sokat lak�nk�nt ber�gz�ti a tarh.eloiras.lako adatt�bl�ba
    figyelembe v�ve, hogy van-e v�z�r�ja, avagy nincs, valamint ha van fel�j�t�si alap, k�pviseleti d�j, 
    vagy szem�td�j akkor azt is.
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
            ha az albet�t v�s�rl�sa nagyobb mint az el��r�s kezdete, akkor az el��r�s kezdete az albet�t v�s�rl�sa lesz,
            ha az albet�t elad�sa kor�bbi mint az el��r�s v�ge akkor az el��r�s v�ge az albet�t elad�sa lesz,
            be kell jegyezni az el��r�st, ha az albet�t v�tele kor�bbi mint az el��r�s v�ge,
            be kell jegyezni az el��r�st, amennyiben az albet�t elad�sa k�s�bbi mint az el��r�s kezdete
            str_to_date az�rt kell mert a date t�pust vissza kell alak�tanom d�tumra mivel az adatb�zisb�l visszaolvasva string lesz!
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
                        keresett = ('v�z�r�val').decode('ISO-8859-2')
                    else:
                        if aktual_adat.vizora == 'n':
                            _vizora = False
                            keresett = ('n�lk�l').decode('ISO-8859-2')
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

                        if ('�pviseleti').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('Szem�td�j').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and lakoszam > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('K�lts�g hozz�j�rul�s').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('Technikai').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and alapterulet > 0 and _vizora and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('Lak�skassza').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and alapterulet > 0 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('parkol').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and 'park' in utca2 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('gar').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and 'gar' in utca2 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                        if (('parkol').decode(
                                'ISO-8859-2') in eloir.eloirfajta.name) and parkolo == 'v' and 'gar' not in utca2 and vetel_datum < zarodatum and eladas_datum > kezdodatum:
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

                                # TODO meg kell csin�lni, hogy a r�gi el��r�s v�gd�tuma = legyen a mostani kezdete -1 nap
                                # print kiirt_id

        # ez itt t�rli azt a rekordot amivel bevitt�k a sorozatot
        igaze = self.unlink(cr, uid, ids, context)
        return igaze


tarh_eloiras_lako()


class tarh_lakoeloir_havi(osv.osv):
    '''
    Ebben az oszt�lyban t�roljuk a tulajdonosok t�nyleges havi el��r�sait.
    Figyeli, hogy �l e m�g az el��r�s (nem adt�k-e el a lak�st) 
    Ezt meg kell sz�ntetni!!!!  csak a tarh_eloiras_lako marad!
    '''
    _name = 'tarh.lakoeloir.havi'
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz', domain="[('is_company','=', True)]", required=True),
        'lako': fields.many2one('res.partner', 'Tulajdonos', domain="['|',('active','=', True),('active','=', False)]"),  # view-ben majd sz�rni kell!
        'eloirfajta': fields.many2one('eloiras.fajta', 'Eloiras fajta'),
        'ev': fields.integer('Eloiras eve:', required=True),
        'honap': fields.integer('Eloiras honapja', required=True),
        'osszeg': fields.integer('Eloiras osszege'),
        'eloir_datum': fields.date('Esedekes'),

    }

    _order = 'ev desc, honap desc'

    '''
    ez az f�ggv�ny be�rja az adatb�zisba a megadott h�nap �s �v konkr�t el��r�sait.
    '''

    def havi_eloir_rogzit (self, cr, uid, ids, context):
        '''
        a megadott d�tumn�l megkeresi a h�nap utols� napj�nak d�tum�t
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
        Sorban v�gigmegy�nk a tarh_eloir_lako t�bl�n �s ha m�g aktu�lis az el��r�s
        (nem adt�k el a lak�st stb.) akkor az el��r�st felm�solja a tarh_lakoeloir_havi
        adatt�bl�ba az adott �v �s h�nap figyelembev�tel�vel.
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
                        # eloiras a honap utols� napja!
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
        '''TODO be kellene �p�teni egy vizsg�latot, hogy amennyiben m�r l�tezik ennek a lak�nak erre, a h�napra ez az el��r�sa, akkor ne r�gz�tse be!K�SZ!!!!
        '''

    def havi_eloir_rogzit2 (self, cr, uid, ids, context):
        '''
        a megadott d�tumn�l megkeresi a h�nap utols� napj�nak d�tum�t
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
        Ugyanaz mint az el�z�, de csup�n a megadott lak� adatait �rja be
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
                        # eloiras a honap utols� napja!
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
        a megadott d�tumn�l megkeresi a h�nap utols� napj�nak d�tum�t
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
        Ugyanaz mint az el�z�, de csup�n a megadott t�rsash�z adatait �rja be
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
                        # eloiras a honap utols� napja! VOLT DE 10-re MEGVALTOZTATTAM!!!
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
        'elado': fields.many2one('res.partner', 'Elado', required=True),  # view-ben majd sz�rni kell!
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
    Amikor egy lak� eladja a lak�s�t egy m�sik szem�lynek:
    -beolvassuk az elad� �sszes adat�t egy dict-be
    -vev� adatait beolvassuk a tarh_lakaselad t�bl�r�l
    -be�ll�tjuk az elad�n�l az elad�si, vev�n�l a v�teli d�tumot,
    -l�trehozzuk a t�rsash�zban ugyanarra az albet�tre a vev� adatait
    
    def str_to_date(str_date):
            szeletelt=str_date.split("-")
            return(date( int(szeletelt[0]),int(szeletelt[1]),int(szeletelt[2])))
    '''

    def lakaselad_rogzit (self, cr, uid, ids, context):

        if self.browse(cr,uid,ids,context=None).nyitott:


            '''
            a megadott d�tumn�l megkeresi a h�nap utols� napj�nak d�tum�t
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
            - meg kell keresni a tarh.eloiras.lako tablaban az elad� el��r�sait,

            ( ha az elad�si d�tum kisebb mint az el��r�s v�ge akkor) be kell �ll�tani az el��r�s v�g�nek az elad�si d�tumot.
            - gener�lni kell az �j tulajdonos r�sz�re ugyanezeket az el��r�sokat, a v�teli d�tum kezdettel

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
                        '''Ha az el��r�s kezdete k�s�bbi mint a v�teli d�tum akkor a r�gi el��r�s kezdete megmarad!'''
                        if str_to_date(ela_eloir.eloir_kezd) < vetel_datum:
                            vevo_eloiras_adatai['eloir_kezd'] = vetel_datum
                        vevo_eloiras_id = _tarh_eloiras_lako.create(cr, uid, vevo_eloiras_adatai, context=None)

                    if eladas_datum < str_to_date(ela_eloir.eloir_vege):
                        elado_eloiras_valtozas['eloir_vege'] = eladas_datum
                    sikeres = _tarh_eloiras_lako.write(cr, uid, ela_eloir.id, elado_eloiras_valtozas, context=None)
                '''
                - meg kell n�zni, hogy a tarh.lakoeloir.havi t�bl�ban elad�s ut�ni d�tummal a r�gi lak� m�r ne szerepeljen,
                - az elad�s d�tuma ut�ni �sszes h�nap el��r�s�t t�r�lj�k a havi el��r�sok k�z�l
                '''
                elado_havi_eloirasai = _tarh_lakoeloir_havi.search(cr, uid, [('lako', '=', elado)], context=None)
                for sorszam in elado_havi_eloirasai:
                    ela_havi_eloir = _tarh_lakoeloir_havi.browse(cr, uid, sorszam, context=None)
                    if ela_havi_eloir:
                        ev = ela_havi_eloir.ev
                        honap = ela_havi_eloir.honap
                        eloiras_honapja = honap_utolsonap(self, date(ev, honap, 1))
                        '''nem �rtem hogy az elad�s d�tuma mi a pics��rt string �s nem date!!!'''

                        if eloiras_honapja > eladas_datum:
                            '''t�r�lni kell a havi el��r�s t�bl�j�b�l'''
                            igaze = _tarh_lakoeloir_havi.unlink(cr, uid, ela_havi_eloir.id, context=None)

                '''
                - a vev� oldal�r�l meg kell n�zni, hogy a v�tel ut�ni id�pontokban h�ny havi bejegyz�s van m�r a havi
                  el��r�sok k�z�tt, a vev� el��r�sai szerepelnek-e m�r, ha nem akkor be kell r�gz�ten�nk.
                '''

                ev = vetel_datum.year
                honap = vetel_datum.month
                '''amikor az aktu�TODO  be kell majd �ll�tania vev� v�telkori tartoz�st a tulajdonosok nyit�egyenlege
                t�bl�ban null�ralis h�napra m�r van b�rmilyen el��r�s akkor el��rjuk a vev�nek is a havit. '''
                darab = _tarh_lakoeloir_havi.search(cr, uid, [('ev', '=', ev), ('honap', '=', honap)], limit=5,
                                                    context=None, count=True)
                while darab > 0:
                    most_datum = honap_utolsonap(self, date(ev, honap, 1))
                    '''van m�r a h�napra el��r�s, megn�zz�k,hogy van e m�r a vev�re el��r�s'''
                    vevo_van_e = _tarh_lakoeloir_havi.search(cr, uid, [('ev', '=', ev), ('honap', '=', honap),
                                                                       ('lako', '=', vevo_id)], context=None, count=True)
                    if vevo_van_e == 0:
                        '''nincs m�g havi el��r�s a vev�re, �gy akkor el��rjuk
                        de csak akkor, ha az el��r�s d�tuma passzol a be�rand� d�tumhoz'''
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

                    ''' n�veli egyel �v-h�nap'''
                    if honap == 12:
                        honap = 1
                        ev = ev + 1
                    else:
                        honap = honap + 1
                    darab = _tarh_lakoeloir_havi.search(cr, uid, [('ev', '=', ev), ('honap', '=', honap)], limit=5,
                                                        context=None, count=True)
                    print darab
                    '''itt a while v�ge'''

                '''l�trehoznunk a v�tel d�tum�ra a vev�nek egy null�s nyit�egyenleget!'''
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
        self.write(cr,uid,ids,{'nyitott':False}) # ezt j�l be�ll�tjuk, hogy ne lehessen m�gegyszer eladni!
        return


tarh_lakaselad()


class my_report(osv.osv):
    _name = "my.report"
    _auto = False
    _columns = {
        'th_szamlatul': fields.many2one('res.partner', 'Tarsashaz', readonly=True,\
                                        domain="[('is_company','=', True),('name','ilike','rsash')]"),
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
    A k�vetkez� elj�r�sban a tranzakci�k alapj�n csoportos�tjuk a k�nyvelt banksz�ml�k sorait,
    a kezd�- �s v�gd�tum k�z�tt, a megadott t�rsash�z minden banksz�ml�j�ra.
    Ezeket a sorokat be�rjuk a tarh_haz_havijel t�bl�ba, amelyb�l �gy majd tudunk m�r aeroo reportot csin�lni
    '''
    def havijel_beir(self,cr,uid,ids,context):
        '''az aktu�lis rekordon k�v�l t�r�lj�k az t�bl�b�l a t�bbi r�gi rekordot'''
        sajat_id=self.browse(cr, uid, ids, context=None).id
        torlendok=self.search(cr,uid,[('id','!=',sajat_id)])
        self.unlink(cr, uid, torlendok, context=None)
        '''kiolvassuk a lapr�l az id�szakokat, a list�zand� t�rsash�zat �s a banksz�ml�t'''
        _kezdatum=self.browse(cr,uid,ids,context=None).kezdatum
        _vegdatum=self.browse(cr,uid,ids,context=None).vegdatum
        _szamlatul=self.browse(cr,uid,ids,context=None).th_szamlatul.id
        _bankszamla=self.browse(cr,uid,ids,context=None).bankszamla_thaz.id
        '''Tranzakci�nk�nt �sszeadjuk a tranzakci�fajt�kat a megadott t�rsash�z megadott 
           banksz�ml�j�nak megadott id�intervallum�ban �s bele�rjuk a t�bl�ba''' 
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
        '''t�r�lj�k a rekordot, amivel l�trehoztuk az eg�szet '''
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

    '''Ebben az elj�r�sban a lak� id�szakra vonatkoz� elsz�mol�s�t tudjuk megtekinteni a kezdatum �s
    vegdatum k�z�tt kilist�zzuk az adott id�szakra vonatkoz� el��r�sokat �s a megt�rt�nt befizet�seket.'''

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
            else:  # nincs nyitoegyenleg r�gzitve
                eredmeny = [datum, 0, 'Nincs a lak�hoz nyit�egyenleg r�gz�tve!!!']
            return (eredmeny)

        sajat_id = self.browse(cr, uid, ids, context=None).id

        '''az aktu�lis rekordon k�v�l t�r�lj�k az t�bl�b�l a t�bbi r�gi rekordot
        torlendok=self.search(cr,uid,[('id','!=',sajat_id)])
        self.unlink(cr, uid, torlendok, context=None)
                
        NEM T�R�LJ�K MERT HA EGYSZERRE K�T ADATLEK�RDEZ�S FOLYIK, AKKOR EGYIK LET�R�LHETI A M�SIK�T
    
        De let�r�lj�k a sorokat amelyek ehhez a lek�rdez�shez tartoznak'''

        _havijel_sor_hiv = self.pool.get('tarh.lako.havijel.sor')
        torleno_sorok = _havijel_sor_hiv.search(cr, uid, [('havijel_id', '=', sajat_id)], context=None)
        _havijel_sor_hiv.unlink(cr, uid, torleno_sorok, context=None)

        '''Beolvassuk a lapr�l a kezd� �s v�gd�tumot, valamint a lak�t, kiolvassuk a nyit�gyenleg �sszeg�t �s a d�tum�t'''

        _kezdatum = str_to_date(self.browse(cr, uid, ids, context=None).kezdatum)  # lekerdezes kezdete
        _vegdatum = str_to_date(self.browse(cr, uid, ids, context=None).vegdatum)  # lekerdezes vege
        _lako = self.browse(cr, uid, ids, context=None).tulaj.id  # onchange-ben majd a tarsashazat kivalsztjuk
        _tarsashaz = self.browse(cr, uid, ids, context=None).tarsashaz.id
        nyitoegy = nyitoegyenleg(self, _lako, _kezdatum)
        # kiirjuk az elso sorba a nyitoegyenleget
        kiirando = {}

        if len(nyitoegy[2]) == 0:  # nincs szoveg ,tehat volt nyitoegyenleg!
            kiirando['erteknap'] = nyitoegy[0]
            kiirando['szoveg'] = 'Nyit�egyenleg'
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
            kiirando['szoveg'] = 'Aktu�lis egyenleg'
            kiirando['eloiras'] = 0
            kiirando['befizetes'] = szumma
            kiirando['havijel_id'] = sajat_id
            id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)
        else:
            kiirando['erteknap'] = _vegdatum
            kiirando['szoveg'] = 'Nincs az id�pontra r�gz�tett adat!!!'
            kiirando['eloiras'] = 0
            kiirando['befizetes'] = 0
            kiirando['havijel_id'] = sajat_id
            id_je = _havijel_sor_hiv.create(cr, uid, kiirando, context=None)

        '''t�r�lj�k a rekordot, amivel l�trehoztuk az eg�szet'''
        #        self.unlink(cr, uid, sajat_id, context=None)

        return self.write(cr,uid,ids,{'lekerdatum':date.today()})

    def onchange_tul (self, cr, uid, ids, lako, kezdatum, vegdatum, context=None):
        '''
        megkeresi, hogy a lako melyik t�rsash�zhoz tartozik,
        ha a lak� nyit�egyenlege k�s�bbi mint a kezdatum akkor m�dos�tja azt,
        ha a vegdatum k�s�bbi mint a t�rsash�z utols� k�nyvelt d�tuma, akkor m�dos�tja azt
        :param cr:
        :param uid:
        :param ids:
        :param lako: tulajdonos
        :param kezdatum: eredetileg bevitt kezd�d�tum
        :param vegdatum: eredetileg bevitt z�r�d�tum
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

Meg kell csin�lni, hogyha a bankbizonylaton ut�lag �ll�tj�k �t a d�tumot, akkor �rja �t a hozz�tartoz� sorokon is!







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
#        ktya = valami.info(cr, uid, title='Export information', message="valami stirng őitt van")
#        return ktya
"""
