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
        'eloirfajta': fields.many2one('eloiras.fajta', 'Eloiras tipusa', required=True),
        'osszeg': fields.integer('Előírás összege', required=True),
        'lezart': fields.boolean(),
        'torolt': fields.boolean(),
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
                            'sticky': True
                        }
                    }

                    pass
                    # _tarh_lakoeloir_havi.search(cr, uid, ids, []) majd kell a kereséshez

        else:
            # jogosultságnál szabályozom, hogy ne tudja a júzer szerkeszteni
            raise osv.except_orm(_("Figyelem!!!"), _(" Le van zarva, nem modosithato!"))

        pass


tarh_egyszeribeir()
