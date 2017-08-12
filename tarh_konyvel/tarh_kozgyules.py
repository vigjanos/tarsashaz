# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.08.08..
'''

from openerp import models, fields, api


class Kozgyules(models.Model):
    _name = 'tarh.kozgyules'
    _order = 'kozgy_datum desc'

    tarsashaz_id = fields.Many2one('res.partner', string='Társasház', required="True",
                                   domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    kozgy_datum = fields.Date('Közgyűlés dátuma', required="True")
    kozgy_helye = fields.Char('Közgyűlés helye')
    feltoltes_ids = fields.Many2many(comodel_name='ir.attachment', string='Jegyzőkönyv feltöltése')
    hatarozat_ids = fields.One2many('tarh.hatarozatok', 'kozgyules_id', string='Hozott határozatok')
    hatarozatkepesseg = fields.Float(digits=(4, 2), string='Határozatképesség %')
    levezeto_id = fields.Many2one('res.partner', string='Levezető elnök', required="True")
    jkv_vezeto_id = fields.Many2one('res.partner', string='Jegyzőkönyv vezető', required="True")
    jkv_hitelesitok_ids = fields.Many2many(comodel_name='res.partner', string='Jkv. hitelesítők')
    megjegyzes = fields.Text('Megjegyzés')


# TODO meg kell majd csinálni, ha utólag változtatják a közgyűlés dátumát, vagy a társasházat,
# akkor a kapcsolódó határozatokban is változtassuk meg!

class Hatarozatok(models.Model):
    _name = 'tarh.hatarozatok'
    name = fields.Char('Határozat száma', required=True)
    tarsashaz = fields.Many2one('res.partner')
    kozgy_datuma = fields.Date('Közgyűlés dátuma')
    hat_rovid_leir = fields.Char('Határozat rövid szövege')
    hat_szovege = fields.Text('Határozat szövege:')
    vegrehajtas_datuma = fields.Date('Végrehajtás dátuma')
    felelos_id = fields.Many2one('res.users', string='Felelős')
    vegrehajtott = fields.Boolean(default=False, string='Kész')
    kozgyules_id = fields.Many2one('tarh.kozgyules', string='Közgyűlés')

    @api.onchange('name')
    def tarsashaz_keres (self):
        if not self.tarsashaz:
            self.tarsashaz = self.kozgyules_id.tarsashaz_id
        if not self.kozgy_datuma:
            self.kozgy_datuma = self.kozgyules_id.kozgy_datum
        return ()


class Parkolo_sor(models.Model):
    _name = 'tarh.parkolosor'
    _order = 'igenyles_datum'

    tarsashaz_id = fields.Many2one('res.partner', string='Társasház', required=True,
                                   domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    tulajdonos_id = fields.Many2one('res.partner', string="Igénylő", required=True,
                                    domain="[('parent_id','=',tarsashaz_id)]")
    igenyles_datum = fields.Date('Igénylés időpontja', required=True, )
    megkapta_datum = fields.Date('Teljesülés időpontja')
    megkapta_e = fields.Boolean('Parkolót kapott', default=False)
    dokumentum_ids = fields.Many2many(comodel_name='ir.attachment', string="Igénylés dokumentuma", required=True, )

    @api.onchange('megkapta_datum')
    def megkapta (self):
        if self.megkapta_datum > '1900-01-01':
            self.megkapta_e = True
        else:
            self.megkapta_e = False
