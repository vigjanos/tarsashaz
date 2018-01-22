# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.osv import osv, fields
#from openerp.addons.tarh_konyvel.seged import *
from openerp.addons.tarh_konyvel.seged3 import tulajegyenleg
from datetime import date


class tul_hanyad(osv.osv):
    _inherit = 'res.partner'

    @api.multi
    def _egyenleg_szamol (self, field_name, arg, context=None):
        lako = self.id
        _tarh_lako_nyito = self.env['tarh.lako.nyito']
        talalt_id = _tarh_lako_nyito.search([('tarh_lako', '=', lako)])
        if talalt_id:
            datum = date.today()
            lekerdezes = tulajegyenleg(self, lako, datum)
            res = {}
            res[lako] = lekerdezes[0]
            return res

    def _felszolit_szamol (self, cr, uid, ids, field_name, arg, context=None):
        sajat_id = self.browse(cr, uid, ids, context).id
        felsz = self.pool['tarh.felszol']
        szmlal = felsz.search_count(cr, uid, [('tulaj', '=', sajat_id), ('felsz_status', '<>', 'rend')],
                                    context=context)
        res = {}
        res[sajat_id] = szmlal
        return res

    _columns = {'tulhanyad': fields.integer(string='Tul. hanyad:'),
                'th_oszto': fields.integer(string='Hanyad oszto:'),
                'alapterulet': fields.float(string='Alapterulet m2:'),
                'alb_szam': fields.integer(string='Albetet szama:'),
                'alb_vetel': fields.date('Albetet vetele'),
                'alb_eladas': fields.date('Albetet eladasa'),
                'onkormanyzati': fields.selection((('n', 'nem'), ('i', 'Igen')), 'Onkormanyzati'),
                'vizora': fields.selection((('v', 'Van'), ('n', 'Nincs')), 'Vizora'),
                'vizoras_tol': fields.date('Vízóra felszerelve:', help=''),
                'hrsz': fields.char("Helyrajzi szam", size=32),
                'parkolohely': fields.selection((('v', 'van'), ('n', 'nincs')), 'Sajat_parkolo'),
                'phely_szam': fields.char(string='Parkolohely szam:', size=32),
                'lakoszam': fields.integer(string='Lakok szama (fo)'),
                'lakoingatlan': fields.boolean(string='Lakas celjara'),
                'levcim': fields.text(string='Ertesitesi cim'),
                'postai': fields.boolean(string='Postai kezbesites'),
                'alapito_ids': fields.many2many('ir.attachment', 'class_ir_attachments_alap', 'alapito_id',
                                                'attachment_id', 'Alapító okiratok:', help=''),
                'biztositas_ids': fields.many2many('ir.attachment', 'class_ir_attachments_biztos', 'biztosito_id',
                                                   'attachment_id', 'Biztosítási kötvények:', help=''),
                'egyenleg': fields.function(_egyenleg_szamol, string='Egyenleg', type='integer', store=False, help=''),
                'uzemeltetesi': fields.char('Uzemeltetési bankszamla', size=32),
                'biztosito': fields.many2one('res.partner', 'Biztosito', help='A társasház biztosítója'),
                'bizt_kotvszam': fields.char('Biztosito kotvenyszam', size=20),
                'bizt_megj': fields.text(string='Biztositasi megjegyzes'),
                'sos_vizes': fields.many2one('res.partner', 'Vizszerelo', help='Hívható vízszerelő'),
                'sos_elektromos': fields.many2one('res.partner', 'Villanyszerelo', help='Hívható villanyszerelő'),
                'sos_lift': fields.many2one('res.partner', 'Liftszerelő', help='Hívható liftszerelő'),
                'sos_gondnok': fields.many2one('res.partner', 'Gondnok', help='Hívható gondnok'),
                'felszolitas': fields.function(_felszolit_szamol, string='Felszólítások', type='integer', store=False,
                                               help=''),
                'muszakis': fields.many2one('res.partner', 'Műszaki előadó',
                                            domain="[('parent_id.name','ilike','újlipótv')]"),
                'konyvelo': fields.many2one('res.partner', 'Könyvelő',
                                            domain="[('parent_id.name','ilike','újlipótv')]"),
                'legm3': fields.integer('Légköbméter', help=''),
                }

    _defaults = {
        'lakoingatlan': True,
        'postai': False,
        'onkormanyzati': 'n',
    }

    _order = 'alb_szam, name'


tul_hanyad()
'''
class res_bank_javitas(osv.osv):
	_inherit = 'res.partner.bank'

	def onchange_company_id(self, cr, uid, ids, company_id, context=None):
		result = {}
		if company_id:
			c = self.pool.get('res.partner').browse(cr, uid, company_id, context=context)
			if c.id:
				r = self.onchange_partner_id(cr, uid, ids, c.id, context=context)
				r['value']['partner_id'] = c.id
				r['value']['footer'] = 1
				result = r
		return result

res_bank_javitas()
'''
