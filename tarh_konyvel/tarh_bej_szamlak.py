# -*- coding: utf-8 -*-
__author__ = 'vigjanos'


from openerp.osv import fields, osv


class tarh_bej_szamlak(osv.osv):
    _name='tarh.bejszamlak'
    _columns={
        'tarsashaz':fields.many2one('res.partner', 'Társasház - Vevő', help='A számla befogadója',
                        domain="[('is_company','=',True),('name','ilike','rsash')]"),
        'beszallito':fields.many2one('res.partner', 'Beszállító', help='A számla kiállítója',
                        domain="[('is_company','=',True),('supplier','=',True)]"),
        'tarh_tranzakcio':fields.many2one('tarh.tranzakcio', 'Tranzakció megnevezése', required=True),
        'szamla_osszeg':fields.integer('Fizetendő'),
        'erk_datum': fields.date('Érkezés dátuma', help=''),
        'fiz_hatarido':fields.date('Fizetési határidő'),
        'referencia':fields.char('Referencia', size=64, help='számlaszám stb., info az átutaláson'),
        'megjegyzes': fields.text('Megjegyzés', help='Bármilyen információ írható ide'),
        'status': fields.selection((('erkezett','Beérkezett'),
                                     ('nyomtatva','Megbízás kinyomtatva'),
                                     ('bekuldve','Bankba beküldve'),
                                     ('fizetve','Kiegyenlítve'),
                                     ),
                                    'Számla státusza', help=''),
    }
    _defaults = {
        'erk_datum' :fields.date.context_today,
        'status':'erkezett',

    }




tarh_bej_szamlak()