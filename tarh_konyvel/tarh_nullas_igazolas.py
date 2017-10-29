# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.10.23..
''' 


from openerp import models, fields, api


class tarh_nullas(models.Model):
    _name = 'tarh.nullas'

    tarsashaz = fields.Many2one('res.partner', string='Társasház', required="True",
                                   domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    tulajdonos = fields.Many2one('res.partner', string='Tulajdonos')
    datum = fields.Date(string='Igazolás dátuma', default=fields.date.today())

'''Ezt majd lehet, hogy el kell innen pakolni később!'''

class tarh_bankbiz_sor(models.Model):
    _inherit = 'tarh.bankbiz.sor'

    '''
    Amennyiben változik a tarh_bankbiz sor és a csekkes befizetés is változtatva van, akkor a
    tulajdonosnak elő kell írni, vagy törölni kell az előírások közül a csekk befizetés költségét.
    (ha a társasháznál van ilyen előírva)
    Ezt úgy csináljuk, hogy felülírjuk a BaseModel create, write, és unlink eljárását,
    meghívjuk az eredeti eljárást, de mellette megcsináljuk ami nekünk kell.
    '''

    @api.model
    def create(self, vals):
        print('Ez van előtte create')
        res = super(tarh_bankbiz_sor, self).create(vals)
        print('Ez van utána')
        return res


    @api.multi
    def write(self, vals):
        print('Ez van előtte')
        res= super(tarh_bankbiz_sor, self).write(vals)
        print('Ez van utána')
        return res

    @api.multi
    def unlink(self):
        print('Ez van előtte törlés')
        print self.ids[0]
        res = super(tarh_bankbiz_sor, self).unlink()
        print('Ez van utána törlés')
        return

class tarh_bankbiz(models.Model):
    _inherit = 'tarh.bankbiz'
    '''Ez azért kell, mert ha a bankbiz_sort töröljük, akkor törli ugyan a hozzá tartozó
    tarh_bankbiz_sor mezőket, de ott nem fut le a tarh_bankbiz_sor unlink eljárás.
    Gondoskodni kell arról, hogy ha van a tarh_bankbiz_sor között olyan elem amiben a csekkes
    befizetés érintve van, akkor töröljük a tulajdonos csekk befizetési előírásait'''

    @api.multi
    def unlink(self):
        print('Ez van előtte törlés')
        print self.ids[0]
        res = super(tarh_bankbiz, self).unlink()
        print('Ez van utána törlés')
        return