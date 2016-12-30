# -*- coding: utf-8 -*-
'''
Created on 2015.05.23'''
__author__ = 'vigjani'

from openerp import models, fields, api, exceptions, _
from seged3 import tulajegyenleg, str_to_date
import unicodedata


class kiserlet(models.Model):
    _name = 'tarh.kiserlet'

    tulajdonos = fields.Many2one('res.partner', String='Tulajdonos', domain="[('parent_id.name','ilike','rsash')]")
    kezdet = fields.Date('Kezdeti időpont')
    befejezes = fields.Date('Befejezési időpont')

        #'egyenleg': fields.function(_egyenleg_szamol, string='Egyenleg', type='integer', store=False, help=''),




    def _egyenleg_szamol (self, cr, uid, ids, field_name, arg, context=None):
        sajat_id = self.browse(cr, uid, ids, context).id
        tulaj = self.browse(cr, uid, ids, context=None).tulajdonos.id
        datum_kezd = str_to_date(self.browse(cr, uid, ids, context=None).kezdet)
        datum_veg = str_to_date(self.browse(cr, uid, ids, context=None).befejezes)
        # lekerdezes=lakoegyenleg2(self,cr,uid,tulaj,datum)
        lekerdezes = lakoegyenleg3(self, cr, uid, tulaj, datum_kezd)
        res = {}
        res[sajat_id] = lekerdezes[0]
        return res

    def gomb_nyomas_regi (self, cr, uid, ids, context=None):
        # tulaj=self.browse(cr,uid,ids,context=None).tulajdonos.id
        datum = self.browse(cr, uid, ids, context=None).kezdet
        # print tulaj
        # print datum
        _res_partner = self.pool.get('res.partner')
        aktiv_tulajok = _res_partner.search(cr, uid,
                                            [('parent_id.name', 'ilike', 'rsash'), ('is_company', '=', False), '|',
                                             ('active', '=', False), ('active', '=', True)], context=None)

        #aktiv_tulajok = _res_partner.search(cr,uid,[('parent_id.name','ilike','rsash')],context=None)

        '''
        for tulajok in aktiv_tulajok:
            tulaj = _res_partner.browse(cr,uid,tulajok,context=None)
            if tulaj.active == False:
                print tulaj.name
        '''


        f = open('~/valamisemmi_uj.txt', 'w')
        for tulajdonos in aktiv_tulajok:
            regi_egyenleg = lakoegyenleg(self, cr, uid, tulajdonos, datum, )[0]
            uj_egyenleg = lakoegyenleg3(self, cr, uid, tulajdonos, datum, )[0]
            if regi_egyenleg != uj_egyenleg:
                nev = _res_partner.browse(cr, uid, tulajdonos, context=None).name
                tarsashaz = _res_partner.browse(cr, uid, tulajdonos, context=None).parent_id.name
                if _res_partner.browse(cr, uid, tulajdonos, context=None).active:
                    aktiv = 'Aktív'
                else:
                    aktiv = 'Eladott'
                valami = unicodedata.normalize('NFKD', tarsashaz).encode('ascii', 'ignore') +'  '+ unicodedata.normalize('NFKD', nev).encode('ascii', 'ignore')
                regi_egyenleg = str(regi_egyenleg)
                uj_egyenleg = str(uj_egyenleg)
                osszefuz = valami + ' Régi: ' + regi_egyenleg + ' Új: ' + uj_egyenleg +  '  ' + aktiv + '\n'
                f.write(osszefuz)
        f.close()



        return True

    @api.multi
    def gomb_nyomas(self):
        tulajdonos = self.tulajdonos.id
        kezdodatum = self.kezdet
        egyenleg= tulajegyenleg(self,tulajdonos,kezdodatum)
        return

    def gomb_nyomasmegregebbi (self, cr, uid, ids, context=None):
        tulajdonos=self.browse(cr,uid,ids,context=None).tulajdonos.id
        kezdodatum = self.browse(cr, uid, ids, context=None).kezdet
        vegdatum = self.browse(cr, uid, ids, context=None).befejezes
        kezdo_eloiras = lakoegyenleg3(self,cr,uid,tulajdonos,kezdodatum)[4]
        kezdo_befizetes = lakoegyenleg3(self,cr,uid,tulajdonos,kezdodatum)[5]
        befejezo_eloiras = lakoegyenleg3(self,cr,uid,tulajdonos,vegdatum)[4]
        befejezo_befizetes = lakoegyenleg3(self,cr,uid,tulajdonos,vegdatum)[5]
        nyitoegyenleg = lakoegyenleg3(self,cr,uid,tulajdonos,kezdodatum)[0]
        zaro_egyenleg = lakoegyenleg3(self,cr,uid,tulajdonos,vegdatum)[0]
        eloiras_lista = list(set(befejezo_eloiras)-set(kezdo_eloiras))
        befizetes_lista = list(set(befejezo_befizetes)-set(kezdo_befizetes))
        _res_partner = self.pool.get('res.partner')
        return()

    def gomb_nyomas_regesregi (self, cr, uid, ids, context=None):
        _res_partner = self.pool.get('res.partner')
        tarsashaz_idk = _res_partner.search(cr,uid,[('name','ilike','rsash'),
                                                    ('active','=',True),
                                                    ('is_company','=',True),
                                                    ('customer','=',True)], context=None)
        for i in tarsashaz_idk:
            nev = _res_partner.browse(cr,uid,i,context=None).name
            azon = _res_partner.browse(cr,uid,i,context=None).id
            print utolso_konyvelt_datum(self,cr,uid,azon) + ' ; ' +nev
        return ()



#kiserlet()

''' store= {
           'tarh.kiserlet': (lambda self, cr, uid, ids, c={}: ids, ['tulajdonos'], 10),
       },
       type='integer', help=''), '''
