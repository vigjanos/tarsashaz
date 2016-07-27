# -*- coding: utf-8 -*-
'''
Created on 2015.05.23'''
__author__ = 'vigjani'

from openerp import osv,fields
from seged import *




class kiserlet(osv.osv):

    def _egyenleg_szamol(self,cr,uid,ids,field_name,arg,context=None):
        sajat_id=self.browse(cr,uid,ids,context).id
        tulaj=self.browse(cr,uid,ids,context=None).tulajdonos.id
        datum_kezd=str_to_date(self.browse(cr,uid,ids,context=None).kezdet)
        datum_veg=str_to_date(self.browse(cr,uid,ids,context=None).befejezes)
        #lekerdezes=lakoegyenleg2(self,cr,uid,tulaj,datum)
        lekerdezes=eloirasok2(self,cr,uid,tulaj,datum_kezd,datum_veg)
        res={}
        res[sajat_id]=lekerdezes[0]
        return res

    def gomb_nyomas(self, cr, uid, ids, context=None):
        '''tulaj=self.browse(cr,uid,ids,context=None).tulajdonos.id
        datum=self.browse(cr,uid,ids,context=None).kezdet

        print tulaj
        print datum'''
        return True

    _name='tarh.kiserlet'
    _columns = {
        'tulajdonos': fields.many2one('res.partner', 'Tulajdonos', help='', domain="[('parent_id.name','ilike','rsash')]"),
        'kezdet':fields.date('Kezdeti időpont'),
        'befejezes':fields.date('Befejezési időpont'),
        'egyenleg':fields.function(_egyenleg_szamol,string='Egyenleg',type='integer', store=False, help=''),



    }
kiserlet()

''' store= {
           'tarh.kiserlet': (lambda self, cr, uid, ids, c={}: ids, ['tulajdonos'], 10),
       },
       type='integer', help=''), '''