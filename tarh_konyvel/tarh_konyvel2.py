# -*- coding: ISO-8859-2 -*-
'''
Created on 2015.02.13.

@author: vigjani
megtisztítva a tarh_lakoeloir_havi használattól!
'''
from openerp.osv import osv, fields
from datetime import date,time,datetime,timedelta
from seged import *
from openerp.tools.translate import _
from openerp import tools

    
class tarh_havijel_haz(osv.osv):
    _name='tarh.havijel.haz'
    _columns={
        'kezdatum':fields.date('Kezdo datum',required=True),
        'vegdatum':fields.date('Befejezo datum',required=True),
        'th_szamlatul':fields.many2one('res.partner', 'Tarsashaz' ,required=True),
        'sor_id':fields.one2many('tarh.havijel.haz.sor','havijel_id', 'kapocs2'),
        }
    
    def kiszamol(self,cr,uid,ids,context=None):

        def str_to_date(str_date):
            szeletelt=str_date.split("-")
            return(date( int(szeletelt[0]),int(szeletelt[1]),int(szeletelt[2])))
        


        
        sajat_id=self.browse(cr, uid, ids, context=None).id
        _kezdatum=self.browse(cr,uid,ids,context=None).kezdatum
        _vegdatum=self.browse(cr,uid,ids,context=None).vegdatum
        _szamlatul=self.browse(cr,uid,ids,context=None).th_szamlatul.id
        ref_jelentes_sor=self.pool.get('tarh.havijel.haz.sor')
        
        '''Töröljük azokat a sorokat, melyek esetleg ehhez a lekérdezéshez tartoznak 
        '''
        torlendo_sorok=ref_jelentes_sor.search(cr,uid,[('havijel_id','=',sajat_id)],context=None)
        if torlendo_sorok:
            ref_jelentes_sor.unlink(cr,uid,torlendo_sorok,context=None)

        '''
        Megkeressük az összes bankszámláját a társasháznak
        '''
        bankszamlak=self.pool.get('res.partner.bank').search(cr,uid,[('partner_id','=',_szamlatul)],context=None)
        for bankszamla in bankszamlak:
            '''Megkeressük a kezdodatum idejen a nyitóegyenleget (-1 nap!!!) és beírjuk az első sorba  '''
            nyitoegyenleg=bankegyenleg(self, cr, uid, bankszamla, str_to_date(_kezdatum)-timedelta(days=1))
            kiirando={}
            kiirando['bankszamla_thaz']=bankszamla
            kiirando['tranzakcio']='szla_nyito'
            kiirando['jovairas']=nyitoegyenleg
            kiirando['terheles']=0
            kiirando['adat']=False
            kiirando['havijel_id']=sajat_id
            ref_jelentes_sor.create(cr,uid,kiirando,context=None)
            
            
            '''Tranzakciónként összeadjuk a tranzakciófajtákat a megadott társasház megadott 
            bankszámlájának megadott időintervallumában és beleírjuk a táblába''' 
            conn_str="select sum(terheles) as terheles, sum(my_report.jovairas) as jovairas, tarh_tranzakcio.name as tarh_tranzakcio"\
            " from my_report join tarh_tranzakcio on tarh_tranzakcio=tarh_tranzakcio.id where th_szamlatul="+str(_szamlatul)+""\
            " and erteknap between '"+_kezdatum+"' and '"+_vegdatum+"' and bankszamla_thaz="+str(bankszamla)+" group by tarh_tranzakcio.name order by tarh_tranzakcio.name"
            cr.execute(conn_str)
            eredmeny = cr.dictfetchall()
            if eredmeny:
                kiirando={}
                for row in eredmeny:
                    #kiirando['kezdatum']=_kezdatum
                    #kiirando['vegdatum']=_vegdatum
                    #kiirando['th_szamlatul']=_szamlatul
                    kiirando['bankszamla_thaz']=bankszamla
                    kiirando['tranzakcio']=row['tarh_tranzakcio']
                    kiirando['jovairas']=row['jovairas']
                    kiirando['terheles']=row['terheles']
                    kiirando['adat']=True
                    kiirando['havijel_id']=sajat_id
                    ref_jelentes_sor.create(cr,uid,kiirando,context=None)
            
            
            zaroegyenleg=bankegyenleg(self, cr, uid, bankszamla, str_to_date(_vegdatum))
            kiirando={}
            kiirando['bankszamla_thaz']=bankszamla
            kiirando['tranzakcio']='szla_zaro'
            kiirando['jovairas']=zaroegyenleg
            kiirando['terheles']=0
            kiirando['adat']=False
            kiirando['havijel_id']=sajat_id
            ref_jelentes_sor.create(cr,uid,kiirando,context=None)
   
        
        return
    
    
tarh_havijel_haz   

class tarh_havijel_haz_sor(osv.osv):
    _name = 'tarh.havijel.haz.sor'
    _columns ={
        'jovairas':fields.integer('Jovairas'),
        'terheles':fields.integer('Terheles'),
        'tranzakcio': fields.char('Tranzakcio fajta', size=64),
        'bankszamla_thaz':fields.many2one('res.partner.bank', 'Bankszamla tarsashaz'),
        'adat':fields.boolean('Adat-e'),
        'havijel_id':fields.many2one('tarh.havijel.haz', 'kapocs', ondelete='cascade', select=True, readonly=True),
               
        }
    
       
tarh_havijel_haz_sor()
    
    
    
class tarh_haz_lakoegy(osv.osv):
    _name = 'tarh.haz.lakoegy'
    _columns ={
        'kezdatum':fields.date('Kezdodatum', required=True),
        'vegdatum':fields.date('Befejezo datum', required=True),
        'tarsashaz':fields.many2one('res.partner','Tarsashaz',required=True),
        'min_tartozas':fields.integer('Nyomtatas csak ekkora tartozastol'),
        'min_honap':fields.integer('Nyomtatas csak ennyi honap tartozastol'),
        'bankszamla':fields.char('Tarsahaz uzemeltetesi szamlaja'),
        'sor_id':fields.one2many('tarh.haz.lakoegy.sor', 'lakoegy_id', 'kapocs2'),
        'lekerdate': fields.date('Lekerdezes datuma'),

    }
    _defaults={'min_tartozas':20000,
               'min_honap':3,
               'lekerdate':fields.date.context_today
               }
    

    def onchange_tarsashaz(self,cr,uid,ids,tarsashaz, vegdatum, context=None):
        '''
        csak azert kell, hogy majd ki tudjuk iratni a reportban, hogy melyik szamlara kell befizetni.
        illetve beírjuk végdátumnak a ház utolsó lekönyvelt napjának a dátumát
        :param cr:
        :param uid:
        :param ids:
        :param tarsashaz: társasház a lapról
        :param vegdatum: befejező dátum a lapról
        :param context:
        :return:
        '''
        eredmeny={}
        if tarsashaz:
            uzemeltetesi=self.pool.get('res.partner.bank').search(cr,uid,[('partner_id','=',tarsashaz),('state','=','bank_uzem')],context=None)
            if uzemeltetesi[0]:
                eredmeny['bankszamla']=self.pool.get('res.partner.bank').browse(cr,uid,uzemeltetesi[0],context=None).acc_number
            zarodatum=utolso_konyvelt_datum(self,cr,uid,tarsashaz)
            if vegdatum > zarodatum:
                eredmeny['vegdatum'] = zarodatum
        return {'value': eredmeny}
    
    def lakoegyenlegek(self,cr,uid,ids,contex=None):
        
        def str_to_date(str_date):
            szeletelt=str_date.split("-")
            return(date( int(szeletelt[0]),int(szeletelt[1]),int(szeletelt[2])))

        
        '''
        def lakoegyenleg(_lako,datum):
            #kiszamolja,hogy a _lako tulajdonosnak a datum idopontban mennyi az egyenlege
            #ezt az eredmeny listaban adjuk vissza: nyito, osszes eloiras, osszes jovairas, datum honapjaban a
            #rendkivuli nelkuli eloiras formaban
            sum_eloiras=0
            sum_jovairas=0
            _nyito_osszeg=0
            havi_eloiras=0
            _tarh_lako_nyito=self.pool.get('tarh.lako.nyito')
            talalt_id=_tarh_lako_nyito.search(cr,uid,[('tarh_lako','=',_lako)],context=None)
            if talalt_id: # ha van nyitoegyenleg rogzitve
                nyito_dok=_tarh_lako_nyito.browse(cr,uid,talalt_id[0],context=None)
                _nyito_datum=nyito_dok.egyenleg_datuma
                _nyito_osszeg=nyito_dok.egyenleg
                _tarh_lakoeloir_havi=self.pool.get('tarh.lakoeloir.havi')
                _eloiras_fajta=self.pool.get('eloiras.fajta')
                _my_report=self.pool.get('my.report')
                tarh_lakoeloir_havi_lista=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',_lako),('eloir_datum','>',_nyito_datum),('eloir_datum','<=',datum)],context=None) #datum szures kell bele!
                my_report_lista=_my_report.search(cr,uid,[('partner','=',_lako),('erteknap','>',_nyito_datum),('erteknap','<=',datum)],context=None) #datum szures kell bele!
                eloirasok=_tarh_lakoeloir_havi.browse(cr,uid,tarh_lakoeloir_havi_lista, context=None)

                #innen kezdodik a havi eloirasok kigyujtese
                aktualis_havi_eloir_lista=_tarh_lakoeloir_havi.search(cr,uid,[('lako','=',_lako),('ev','=',datum.year),('honap','=',datum.month)],context=None)
                aktualis_havi_eloiras=_tarh_lakoeloir_havi.browse(cr,uid,aktualis_havi_eloir_lista,context=None)
                for havi_eloir in aktualis_havi_eloiras:
                    eloirasfajta=havi_eloir.eloirfajta.id
                    eloir_list= _eloiras_fajta.search(cr,uid,[('id','=',eloirasfajta)],context=None)
                    eloir_neve=_eloiras_fajta.browse(cr,uid,eloir_list[0],context=None).name
                    eloir_osszege=havi_eloir.osszeg
                    if 'Rendk' not in eloir_neve and 'gyv' not in eloir_neve:
                        havi_eloiras = havi_eloiras + eloir_osszege



                befizetesek=_my_report.browse(cr,uid,my_report_lista,context=None)
                for befizetes in befizetesek:
                    _nyito_osszeg = _nyito_osszeg+befizetes.jovairas-befizetes.terheles
                    sum_jovairas = sum_jovairas + befizetes.jovairas-befizetes.terheles
                for eloiras in eloirasok:
                    _nyito_osszeg= _nyito_osszeg-eloiras.osszeg
                    sum_eloiras = sum_eloiras + eloiras.osszeg 
                #ha a kejerdezesi datum korabbi mint a nyitoegyenleg datuma, akkor a kezdeti datum a nyitoegyenleg datuma lesz
                _nyito_datum_date=str_to_date(_nyito_datum)
                if datum < _nyito_datum_date:
                    datum=_nyito_datum_date
                    eredmeny=[datum,_nyito_osszeg,'']
            else: # nincs nyitoegyenleg rögzitve
                eredmeny=[datum,0,'Nincs a lakóhoz nyitóegyenleg rögzítve!!!']
                
                eredmeny=[_nyito_osszeg, sum_eloiras, sum_jovairas, havi_eloiras]
                return(eredmeny)
        
        '''


        sajat_id=self.browse(cr, uid, ids, context=None).id
        _kezdatum=str_to_date(self.browse(cr,uid,ids,context=None).kezdatum)
        _vegdatum=str_to_date(self.browse(cr,uid,ids,context=None).vegdatum)
        _tarsashaz=self.browse(cr,uid,ids,context=None).tarsashaz.id
        ref_egyenleg_sor=self.pool.get('tarh.haz.lakoegy.sor')
        ref_res_partner=self.pool.get('res.partner')
        ref_lako_nyito=self.pool.get('tarh.lako.nyito')
        
        '''Töröljük azokat a sorokat, melyek esetleg ehhez a lekérdezéshez tartoznak korábbról 
        '''
        torlendo_sorok=ref_egyenleg_sor.search(cr,uid,[('lakoegy_id','=',sajat_id)],context=None)
        if torlendo_sorok:
            ref_egyenleg_sor.unlink(cr,uid,torlendo_sorok,context=None)
        '''
        Azon lakók kiválasztása,akik a társasházban laknak, aktívak a lekérdezés időpontjában és van nyitóegyenlegük!
        '''
        #lakolista=ref_res_partner.search(cr,uid,[('parent_id','=',_tarsashaz),('active','=',True)],context=None)#,('alb_eladas','>=',_vegdatum),('alb_vetel','<=',_kezdatum)
        aktiv_lako = ref_res_partner.search(cr,uid,[('parent_id','=',_tarsashaz),('active','=',True)],context=None)
        nem_aktiv_lako = ref_res_partner.search(cr,uid,[('parent_id','=',_tarsashaz),('active','=',False),('alb_eladas','>=',_vegdatum)],context=None)
        lakolista = nem_aktiv_lako + aktiv_lako
        for lako in lakolista:
            van_nyito=ref_lako_nyito.search(cr,uid,[('tarh_lako','=',lako)],context=None)
            if van_nyito:
                lako_partner=ref_res_partner.browse(cr,uid,lako,context=None)
                
                if lako_partner.alb_vetel:
                    alb_vetel=str_to_date(lako_partner.alb_vetel)
                else:
                    alb_vetel=date(2010,1,1)
                if lako_partner.alb_eladas:
                    alb_eladas=str_to_date(lako_partner.alb_eladas)
                else:
                    alb_eladas=date(2050,12,31)
                if alb_vetel <= _vegdatum and alb_eladas >= _vegdatum:
                    kezdoadat=lakoegyenleg3(self,cr,uid, lako, _kezdatum)
                    vegadat=lakoegyenleg3(self,cr,uid, lako, _vegdatum)
                    #kezdoadat = lakoegyenleg( lako, _kezdatum)
                    #vegadat = lakoegyenleg( lako, _vegdatum)
                    #print lako
                    kiirando={}
                    kiirando['tulaj']=lako_partner.name
                    kiirando['tulajdonos']=lako_partner.id
                    kiirando['kezdoegyenleg']=kezdoadat[0]
                    kiirando['eloirasok']=vegadat[1]-kezdoadat[1]
                    kiirando['befizetesek']=vegadat[2]-kezdoadat[2]
                    kiirando['zaroegyenleg']=vegadat[0]
                    kiirando['cim']=lako_partner.street2
                    kiirando['albetet']=lako_partner.alb_szam
                    kiirando['havi_eloiras']=vegadat[3]
                    kiirando['lakoegy_id']=sajat_id
                    ref_egyenleg_sor.create(cr,uid,kiirando,context=None)
            
                
        
        return
    
    
    
tarh_haz_lakoegy()    


class tarh_haz_lakoegy_sor(osv.osv):
    _name = 'tarh.haz.lakoegy.sor'
    _columns = {
        'tulaj':fields.char('Albetet tulajdonos',size=128),
        'tulajdonos':fields.many2one('res.partner','Tulajdonos'),
        'kezdoegyenleg':fields.integer('Kezdo egyenleg'),
        'eloirasok':fields.integer('Eloirasok'),
        'befizetesek':fields.integer('Befizetesek'),
        'zaroegyenleg':fields.integer('Aktualis egyenleg'),
        'cim':fields.char('cim',size=32),
        'albetet':fields.integer('Albetet'),
        'havi_eloiras':fields.integer('Havonta eloiras'),
        'lakoegy_id':fields.many2one('tarh.haz.lakoegy', 'kapocs', ondelete='cascade', select=True, readonly=True),

        }
    _order = 'albetet'
tarh_haz_lakoegy_sor()
    
