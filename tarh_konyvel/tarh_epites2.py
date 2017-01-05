# -*- coding: utf-8 -*-
'''
create by vigjanos on 2017.01.04.
'''

from openerp import models, fields, api, _

class tarh_epites2(models.Model):
    _name = 'tarh.epites2'

    tarsashaz = fields.Many2one('res.partner', string='Társasház')
    kezdatum = fields.Date('Kezdő dátum', required=True, default='2016-01-01' )
    vegdatum = fields.Date('Záró dátum', required=True, default='2016-12-01')
    lek_tranzakcio = fields.Many2one('tarh.tranzakcio', string='Kiválasztott tranzakció')
    sor_id = fields.One2many('tarh.epites2.sor', 'tarsashaz_id')

    @api.multi
    def lekerdez(self):
        _sajat_id=self.id
        _kezdatum = self.kezdatum
        _vegdatum = self.vegdatum
        _tarsashaz = self.tarsashaz.id
        _lek_tranzakcio = self.lek_tranzakcio.id
        _res_partner_hiv = self.env['res.partner']
        _tarh_tranzakcio_hiv = self.env['tarh.tranzakcio']
        _my_report_hiv = self.env['my.report']
        _tarh_epites2_sor_hiv = self.env['tarh.epites2.sor']

        torlendok = _tarh_epites2_sor_hiv.search([('tarsashaz_id', '=', _sajat_id)])
        torlendok.unlink()


        #Meg kell keresnünk a my_report táblából ahol th_szamlatul=tarsashaz az erteknap a kezdatum es vegdatum között van,
        #és a tarh_tranzakcio = lek_tranzakcio val

        talalatok = _my_report_hiv.search([('th_szamlatul', '=', _tarsashaz), ('tarh_tranzakcio', '=', _lek_tranzakcio),
                                          ('erteknap', '>=', _kezdatum), ('erteknap', '<=', _vegdatum)], order='erteknap')

        if talalatok:
            for talalat in talalatok:
                _tarh_epites2_sor_hiv.create({
                    'erteknap': talalat.erteknap,
                    'kivonatszam': talalat.kivonatszam,
                    'osszeg': talalat.terheles - talalat.jovairas,
                    'partner': talalat.partner.id,
                    'megjegyzes': talalat.megjegyzes,
                    'tarsashaz_id': _sajat_id
                })
        return()

class tarh_epites2_sor(models.Model):
    _name = 'tarh.epites2.sor'

    erteknap = fields.Date('Értéknap')
    kivonatszam = fields.Char('Kivonatszám')
    osszeg = fields.Integer('Összeg')
    partner = fields.Many2one('res.partner', string='Szállító')
    megjegyzes = fields.Text('Megjegyzés')
    tarsashaz_id = fields.Many2one('tarh.epites2', ondelete='cascade', select=True)
