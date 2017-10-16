# -*- coding: utf-8 -*-


__author__ = 'vigjani'

from openerp.osv import fields, osv
from openerp import api
from datetime import date, timedelta, datetime
from openerp.addons.tarh_konyvel import seged
from seged3 import tulajegyenleg


class tarh_felszol(osv.osv):
    _name = 'tarh.felszol'

    @api.multi
    def _egyenleg_szamol (self, field_name, arg, context=None):
        lako = self.tulaj.id
        _tarh_lako_nyito = self.env['tarh.lako.nyito']
        talalt_id = _tarh_lako_nyito.search([('tarh_lako', '=', lako)])
        if talalt_id:
            datum = date.today()
            lekerdezes = tulajegyenleg(self, lako, datum)
            res = {}
            res[self.id] = lekerdezes[0]
            return res

    def _havi_kotelezettseg(self, cr, uid, ids, field_name, arg, context=None):
        lako = self.browse(cr, uid, ids, context).tulaj.id
        datum = date.today()
        sajat_id = self.browse(cr, uid, ids, context).id
        res = {}
        res[sajat_id] = seged.havi_fizetendo2(self,cr,uid,lako,datum)
        return res

    def _last_konyvelt_nap(self,cr,uid,ids,field_name,arg,context=None):
        sajat_id = self.browse(cr, uid, ids, context).id
        tarsashaz = self.browse(cr, uid, ids, context).tulaj.parent_id.id
        last_date = seged.utolso_konyvelt_datum(self,cr,uid,tarsashaz)
        res={}
        res[sajat_id] = last_date
        return res

    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Társasház',
                                     domain="[('is_company','=',True),('name','ilike','rsash')]"),
        'tulaj': fields.many2one('res.partner', 'Tulajdonos', domain="[('parent_id.name','ilike','rsash')]"),
        'felsz_tipus': fields.selection((('felsz_kepv', 'Képviseleti felszólítás'),
                                         ('felsz_ugyv', 'Ügyvédi felszólítás'),
                                         ('fiz_mh', 'Fizetési meghagyás'),
                                         ('vhajt', 'Végrehajtás'),
                                         ('jelz', 'Jelzálogjog bejegyzés')
                                         ), 'Felszólítás típus', help='felszólítás típusa'),
        'felsz_date': fields.date('Felszólítas dátuma', help=''),
        'felsz_hatarido': fields.date('Felszólítás határideje', help=''),
        'felsz_status': fields.selection((('elind', 'Elindítva'),
                                          ('ugyvednek', 'Ügyvédnek átadni!'),
                                          ('ugyvednel', 'Ügyvédnél'),
                                          ('vh_ra', 'Jelzálog-Fmh-Végrehajtásra!'),
                                          ('ugyvednel_vh', 'Ügyvédnél vh-fmh-jelzálog'),
                                          ('reagalt', 'Válasz érkezett'),
                                          ('rend', 'Rendezve'),
                                          ('neg', 'Sikertelen')), 'Felszólítás státusza', help='felszólitás állapota'),
        'megjegyzes': fields.text('Megjegyzés'),
        'ugyved': fields.many2one('res.partner', 'Eljáró ügyvéd', domain="[('name','ilike','ügyv')]"),
        'feltoltes_ids': fields.many2many('ir.attachment', 'class_ir_attachments_rel', 'feltoltes_id', 'attachment_id',
                                          'Kapcsolódó dokumentumok:', help=''),
        'egyenleg': fields.function(_egyenleg_szamol, string='Egyenleg', type='integer', store=False, help=''),
        'havi_eloir': fields.function(_havi_kotelezettseg, string='Havi fizetendő', type='integer', store=False, help=''),
        'utso_konyv_nap':fields.function(_last_konyvelt_nap, string='Könyvelve -ig', type='date',store=False, help=''),
        'fmh_szam': fields.char('FMH száma', size=25, help=''), 
        'vegrehajto': fields.many2one('res.partner', 'Végrehajtó', domain="[('name','ilike','végrehaj')]"),
        'vh_szama': fields.char('Végrehajtás ügyszáma', size=25, help=''),
    }
    _defaults = {
        'felsz_tipus': 'felsz_kepv',
        'felsz_status': 'elind',
        'felsz_date': fields.date.context_today,
        #        'felsz_hatarido':('felsz_date'+timedelta(month=1)),
    }

    def datum_aktualizal (self, cr, uid, ids, context=None):
        eredmeny = {}
        ma = date.today()
        ujdate = ma + timedelta(days=21)
        eredmeny['felsz_hatarido'] = ujdate
        return self.write(cr, uid, ids, eredmeny)

    def onchange_tulaj (self, cr, uid, ids, tulaj, context=None):
        eredmeny = {}
        if tulaj:
            eredmeny['tarsashaz'] = self.pool.get('res.partner').browse(cr, uid, tulaj, context=None).parent_id
        return {'value': eredmeny}

    def onchange_felsz_date (self, cr, uid, ids, date, context=None):
        eredmeny = {}
        if date:
            ujdate = seged.str_to_date(date)
            eredmeny['felsz_hatarido'] = ujdate + timedelta(days=21)
        return {'value': eredmeny}


tarh_felszol()
