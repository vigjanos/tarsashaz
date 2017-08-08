# -*- coding: utf-8 -*-
'''
 Created by vigjani on 2017.08.08..
'''

from openerp import models, fields, api


class Kozgyules(models.Model):
    _name = 'tarh.kozgyules'

    tarsashaz_id = fields.Many2one('res.partner', string='Társasház',
                                   domain="[('is_company','=',True),('name','ilike','%rsash%')]")
    kozgy_datum = fields.Date('Közgyűlés dátuma')
    kozgy_helye = fields.Char('Közgyűlés helye')
    feltoltes_ids = fields.Many2many(comodel_name='ir.attachment', string='Jegyzőkönyv feltöltése')
    hatarozat_ids = fields.One2many('tarh.hatarozatok', 'kozgyules_id', string='Hozott határozatok')
    hatarozatkepesseg = fields.Float(digits=(4, 2), string='Határozatképesség %')
    levezeto_id = fields.Many2one('res.partner', string='Levezető elnök')
    jkv_vezeto_id = fields.Many2one('res.partner', string='Jegyzőkönyv vezető')
    jkv_hitelesitok_ids = fields.Many2many(comodel_name='res.partner', string='Jkv. hitelesítők')
    megjegyzes = fields.Text('Megjegyzés')


class Hatarozatok(models.Model):
    _name = 'tarh.hatarozatok'
    name = fields.Char('Határozat száma')
    hat_rovid_leir = fields.Char('Határozat rövid szövege')
    hat_szovege = fields.Text('Határozat szövege:')
    vegrehajtas_datuma = fields.Date('Végrehajtás dátuma')
    felelos_id = fields.Many2one('res.users', string='Felelős')
    vegrehajtott = fields.Boolean(default=False, string='Kész')
    kozgyules_id = fields.Many2one('tarh.kozgyules', string='Közgyűlés')

