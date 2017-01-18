# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2016.10.31..
'''

from openerp.osv import fields, osv
from seged import *
from openerp.tools.translate import _
from openerp import tools


class tarh_egyszeribeir(osv.osv):
    _name = 'tarh.egyszeribeir'
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz',
                                     domain="[('is_company','=', True), ('name','ilike','rsash'),('active','=',True)]",
                                     required=True),
        'tulajdonos': fields.many2one('res.partner', 'Tulajdonos', required=True),
        'idopont': fields.date('Előírás időpontja', required=True),
        'eloirfajta': fields.many2one('eloiras.fajta', 'Előírás típusa', required=True),
        'osszeg': fields.integer('Előírás összege', required=True),
        'lezart': fields.boolean('Lezárva'),
        'torolt': fields.boolean('Törölve'),
        'torolte': fields.integer('ID aki törölte')
    }
    _defaults = {
        'lezart': False,
        'torolt': False,
    }

    def rogzites (self, cr, uid, ids, context):
        idopont = str_to_date(self.browse(cr, uid, ids, context).idopont)
        if self.browse(cr, uid, ids, context).tulajdonos.vizora == 'v':
            vizora = True
        else:
            vizora = False
        eredmeny = {
            'esedekes': idopont.day,
            'lako': self.browse(cr, uid, ids, context).tulajdonos.id,
            'tarsashaz': self.browse(cr, uid, ids, context).tulajdonos.parent_id.id,
            'eloirfajta': self.browse(cr, uid, ids, context).eloirfajta.id,
            'osszeg': self.browse(cr, uid, ids, context).osszeg,
            'eloir_kezd': date(idopont.year, idopont.month, 1),
            'eloir_vege': honap_utolsonap(idopont),
            'alapterulet': self.browse(cr, uid, ids, context).tulajdonos.alapterulet,
            'vizora': vizora
        }
        if self.browse(cr, uid, ids, context).lezart == False:
            sikeres = self.pool.get('tarh.eloiras.lako').create(cr, uid, eredmeny, context=None)
            if sikeres:
                leazaras = {'lezart': True,
                            'tarsashaz': eredmeny['tarsashaz'],
                            'tulajdonos': eredmeny['lako'],
                            'idopont': idopont,
                            'eloirfajta': eredmeny['eloirfajta'],
                            'osszeg': eredmeny['osszeg'],
                            }
                self.write(cr, 1, ids, leazaras, context=None)
                # beleírunk a tarh_lakoeloir_havi táblába is,de ezt majd töröljük, ha áttérünk!
                _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
                havieloiras = {'lako': self.browse(cr, uid, ids, context).tulajdonos.id,
                               'ev': idopont.year,
                               'honap': idopont.month,
                               'eloir_datum': idopont,
                               'osszeg': self.browse(cr, uid, ids, context).osszeg,
                               'eloirfajta': self.browse(cr, uid, ids, context).eloirfajta.id,
                               'tarsashaz': self.browse(cr, uid, ids, context).tulajdonos.parent_id.id,
                               }
                havi_sikeres = _tarh_lakoeloir_havi.create(cr, uid, havieloiras, context=None)
                if havi_sikeres:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Growl',
                        'params': {
                            'title': 'Figyelem',
                            'text': 'A bejegyzés sikeresen megtörtént!!!',
                            'sticky': False
                        }
                    }

                    pass
                    # _tarh_lakoeloir_havi.search(cr, uid, ids, []) majd kell a kereséshez

        else:
            # jogosultságnál szabályozom, hogy ne tudja a júzer szerkeszteni
            raise osv.except_orm(_("Figyelem!!!"), _(" Le van zarva, nem modosithato!"))

        pass

    def torles (self, cr, uid, ids, context):
        '''
        Ez az eljárás törli a bevitt előírást a tarh_eloiras_lako táblából, valamint megkeresi és törli az előírást a
        tarh_lakoeloir_havi táblából is!
        '''
        hiba1 = ''
        hiba2 = ''
        _tarh_eloiras_lako = self.pool.get('tarh.eloiras.lako')
        _tarh_lakoeloir_havi = self.pool.get('tarh.lakoeloir.havi')
        if self.browse(cr, uid, ids, context).torolt == False and self.browse(cr, uid, ids, context).lezart == True:
            # Ha még nincs törölve, de már le van zárva, akkor megkeressük a tarh_eloiras_lako
            # táblában azt a bejegyzést, amelyet ez alapján a rekord alapján jegyeztünk be
            idopont = str_to_date(self.browse(cr, uid, ids, context).idopont)
            _eloir_datum = idopont
            _esedekes = idopont.day
            _lako = self.browse(cr, uid, ids, context).tulajdonos.id
            _eloirfajta = self.browse(cr, uid, ids, context).eloirfajta.id
            _osszeg = self.browse(cr, uid, ids, context).osszeg
            _eloir_kezd = date(idopont.year, idopont.month, 1)
            _eloir_vege = honap_utolsonap(idopont)
            bejegyzesek1 = _tarh_eloiras_lako.search(cr, uid, [('esedekes', '=', _esedekes), ('lako', '=', _lako),
                                                               ('eloirfajta', '=', _eloirfajta),
                                                               ('osszeg', '=', _osszeg),
                                                               ('eloir_kezd', '=', _eloir_kezd),
                                                               ('eloir_vege', '=', _eloir_vege)], context=None)
            if bejegyzesek1:
                _tarh_eloiras_lako.unlink(cr, uid, bejegyzesek1, context=None)
            else:
                hiba1 = 'Nem találtam bejegyzést a lakó előírásai között!!'

            # megkeressük a tarh_lakoeloir_havi táblában ezt a bejegyzést, amit ez alapján a rekord alapján jegyeztünk be
            bejegyzesek2 = _tarh_lakoeloir_havi.search(cr, uid,
                                                       [('eloir_datum', '=', _eloir_datum),
                                                        ('lako', '=', _lako),
                                                        ('eloirfajta', '=', _eloirfajta),
                                                        ('osszeg', '=', _osszeg)], context=None)
            if bejegyzesek2:
                _tarh_lakoeloir_havi.unlink(cr, uid, bejegyzesek2, context=None)
            else:
                hiba2 = ' Nem találtam bejegyzést a lakó havi előírásai között!!'

            if hiba1 == '' and hiba2 == '':
                # mind a két táblából sikerült a törlés :-)
                beirni = {
                    'torolt': True,
                    'torolte': uid
                }
                self.write(cr, 1, ids, beirni)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Growl',
                    'params': {
                        'title': 'Figyelem!',
                        'text': 'A bejegyzés törlésre került!!',
                        'sticky': False
                    }
                }
            elif hiba1 != '' or hiba2 != '':
                beirni = {
                    'torolt': True,
                    'torolte': uid
                }
                self.write(cr, 1, ids, beirni)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Growl',
                    'params': {
                        'title': 'Figyelem!',
                        'text': hiba1 + hiba2 + ' Amit találtam, töröltem!',
                        'sticky': False
                    }
                }

        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Growl',
                'params': {
                    'title': 'Figyelem!',
                    'text': 'A bejegyzés már törölve van, vagy még nincs lezárva!',
                    'sticky': False
                }
            }


tarh_egyszeribeir()
