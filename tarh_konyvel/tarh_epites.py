# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2016.01.12..
'''

from openerp.osv import fields, osv
from datetime import date, timedelta, datetime
from seged import *


class tarh_epites(osv.osv):
    _name = 'tarh.epites'
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Társasház',
                                     domain="[('is_company','=',True),('name','ilike','rsash')]"),
        'kezdatum': fields.date('Kezdo datum', required=True, ),
        'vegdatum': fields.date('Zaro datum', required=True, ),
        'lek_tranzakcio': fields.many2one('tarh.tranzakcio', 'Kiválasztott tranzakció'),
        'sor_id': fields.one2many('tarh.epites.sor', 'tarsashaz_id', 'kapocs2', required=False, ),

    }

    _defaults = {
        'kezdatum': '2015-01-01',
        'vegdatum': '2015-12-31',
    }

    def lekerdez (self, cr, uid, ids, context=None):
        sajat_id = self.browse(cr, uid, ids, context=None).id
        kezdatum = self.browse(cr, uid, ids, context=None).kezdatum
        vegdatum = self.browse(cr, uid, ids, context=None).vegdatum
        tarsashaz = self.browse(cr, uid, ids, context=None).tarsashaz.id
        lek_tranzakcio = self.browse(cr, uid, ids, context=None).lek_tranzakcio.id
        ref_my_report = self.pool.get('my.report')
        ref_res_partner = self.pool.get('res.partner')
        ref_tarh_tranzakcio = self.pool.get('tarh.tranzakcio')
        ref_tar_epites_sor = self.pool.get('tarh.epites.sor')

        torlendo1 = ref_tar_epites_sor.search(cr, uid, [('tarsashaz_id', '=', sajat_id)], context=None)
        ref_tar_epites_sor.unlink(cr, uid, torlendo1, context=None)

        '''
        Meg kell keresnünk a my_report táblából ahol th_szamlatul=tarsashaz az erteknap a kezdatum es vegdatum között van,
        és a tarh_tranzakcio = lek_tranzakcio val
        '''

        talalatok = ref_my_report.search(cr, uid,
                                         [('th_szamlatul', '=', tarsashaz), ('tarh_tranzakcio', '=', lek_tranzakcio),
                                          ('erteknap', '>=', kezdatum), ('erteknap', '<=', vegdatum)], order='erteknap')
        sorok = ref_my_report.browse(cr, uid, talalatok, context=None)
        for sor in sorok:
            eredmeny = {}
            eredmeny['tarsashaz_id'] = sajat_id
            eredmeny['erteknap'] = sor.erteknap
            eredmeny['kivonatszam'] = sor.kivonatszam
            eredmeny['osszeg'] = sor.terheles - sor.jovairas
            eredmeny['partner'] = sor.partner.id
            eredmeny['megjegyzes'] = sor.megjegyzes
            ref_tar_epites_sor.create(cr, uid,eredmeny,context=None)


        return


tarh_epites()


class tarh_epites_sor(osv.osv):
    _name = 'tarh.epites.sor'
    _columns = {
        'tarsashaz_id': fields.many2one('tarh.epites', 'kapocs', required=False, ondelete='cascade', select=True, ),
        'erteknap': fields.date('Értéknap'),
        'kivonatszam': fields.char('Kivonatszám', size=12),
        'osszeg': fields.integer('Összeg'),
        'partner': fields.many2one('res.partner', 'Szállító'),
        'megjegyzes': fields.text('Megjegyzés'),
    }


tarh_epites_sor()
