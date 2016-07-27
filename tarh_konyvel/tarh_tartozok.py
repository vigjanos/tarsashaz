# -*- coding: utf-8 -*-
__author__ = 'vigjani'

from openerp.osv import osv, fields
import seged


class tarh_tartozok(osv.osv):
    ''' Ebben a táblában kigyűjtjük az összes tartozót minden házból, hogy aztán jól
        felszólíthassuk őket!
        időpont, minimum tartozás, minimum hónap, lekérdezés dátuma'''
    _name = 'tarh.tartozok'
    _columns = {
        'egy_datum': fields.date('Egyenleg datuma', required=True),
        'min_tartozas': fields.integer('Minimum tartozas', required=True),
        'min_honap': fields.integer('Minimum honap', required=True),
        'max_honap': fields.integer('Maximum honap', required=True),
        'lekerdate': fields.date('Lekerdezes datuma', required=True),
        'sor_id': fields.one2many('tarh.tartozok.sor', 'tartozok_id', 'kapocs1')
    }
    _defaults = {'min_tartozas': 20000,
                 'min_honap': 3,
                 'max_honap':6,
                 'egy_datum': fields.date.context_today,
                 'lekerdate': fields.date.context_today,
                 }

    def tartozok (self, cr, uid, ids, context=None):
        '''
        ezt hívjuk meg a form-ban lévő gombbal, ez az eljárás tölti fel a sorokat
        '''
        sajat_id = self.browse(cr, uid, ids, context=None).id  # a főlap id-je
        ref_tartozok_sor = self.pool.get('tarh.tartozok.sor')
        '''Töröljük azokat a sorokat, melyek esetleg ehhez a lekérdezéshez tartoznak korábbról
        '''
        torlendo_sorok = ref_tartozok_sor.search(cr, uid, [('tartozok_id', '=', sajat_id)], context=None)
        if torlendo_sorok:
            ref_tartozok_sor.unlink(cr, uid, torlendo_sorok, context=None)

        egy_datum = seged.str_to_date(self.browse(cr, uid, ids, context=None).egy_datum)
        min_tartozas = self.browse(cr, uid, ids, context=None).min_tartozas
        min_honap = self.browse(cr, uid, ids, context=None).min_honap
        max_honap = self.browse(cr, uid, ids, context=None).max_honap
        ref_res_partner = self.pool.get('res.partner')
        tarsashazak = ref_res_partner.search(cr, uid, [('is_company', '=', True), ('name', 'ilike', 'rsash'),
                                                       ('active', '=', True)],
                                             context=None)

        for tarsashaz in tarsashazak:
            tulajdonosok = ref_res_partner.search(cr, uid, [('parent_id', '=', tarsashaz)], context=context)
            eladtak = ref_res_partner.search(cr, uid, [('parent_id', '=', tarsashaz), ('alb_eladas', '<', egy_datum)],
                                             context=None)
            felsz = self.pool['tarh.felszol']
            for elad in eladtak:
                tulajdonosok.remove(elad)
            for tulajdonos in tulajdonosok:
                adatok = seged.lakoegyenleg(self, cr, uid, tulajdonos, egy_datum)
                if adatok[3]==0:
                    print 'itt a hiba ', tulajdonos
                else:

                    if max_honap > min_honap:

                        if adatok[0] < -1 * min_tartozas and (-1 * adatok[0] / adatok[3]) >= min_honap and (-1 * adatok[0] / adatok[3]) < max_honap:
                            szmlal = felsz.search_count(cr, uid, [('tulaj', '=', tulajdonos),('felsz_status','<>','rend')], context=context)
                            kiirando = {}
                            kiirando['tarsashaz'] = tarsashaz
                            kiirando['tulajdonos'] = tulajdonos
                            kiirando['egyenleg'] = adatok[0]
                            kiirando['havi_eloiras'] = adatok[3]
                            kiirando['tartozok_id'] = sajat_id
                            if szmlal > 0:
                                kiirando['felszolitasok'] = szmlal
                            else:
                                kiirando['felszolitasok'] = 0
                            ref_tartozok_sor.create(cr, uid, kiirando, context=None)
                    else:
                        if adatok[0] < -1 * min_tartozas and (-1 * adatok[0] / adatok[3]) >= min_honap:
                            szmlal = felsz.search_count(cr, uid, [('tulaj', '=', tulajdonos)], context=context)
                            kiirando = {}
                            kiirando['tarsashaz'] = tarsashaz
                            kiirando['tulajdonos'] = tulajdonos
                            kiirando['egyenleg'] = adatok[0]
                            kiirando['havi_eloiras'] = adatok[3]
                            kiirando['tartozok_id'] = sajat_id
                            if szmlal > 0:
                                kiirando['felszolitasok'] = szmlal
                            else:
                                kiirando['felszolitasok'] = 0
                            ref_tartozok_sor.create(cr, uid, kiirando, context=None)



tarh_tartozok()


class tarh_tartozok_sor(osv.osv):
    ''' Ebben a táblában tartjuk soronként a tartozókat
        társasház, tulajdonos, egyenleg, havi előírás mezők kellenek
    '''
    _name = 'tarh.tartozok.sor'
    _columns = {
        'tarsashaz': fields.many2one('res.partner', 'Tarsashaz'),
        'tulajdonos': fields.many2one('res.partner', 'Tulajdonos'),
        'egyenleg': fields.integer('Egyenleg'),
        'havi_eloiras': fields.integer('Havi eloiras'),
        'felszolitasok': fields.integer('Felsz.'),
        'tartozok_id': fields.many2one('tarh.tartozok', 'kapocs', ondelete='cascade', select=True, readonly=True)
    }


tarh_tartozok_sor()
