#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""M�dulo para obtener c�digo de autorizaci�n electr�nico del web service 
WSFEv1 de AFIP (Factura Electr�nica Nacional - Version 1 - RG2904 opci�n B)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.00a"

import datetime
import decimal
import sys
from pysimplesoap.client import SimpleXMLElement, SoapClient

HOMO = True

#WSDL="https://www.sistemasagiles.com.ar/simulador/wsfev1/call/soap?WSDL=None"
WSDL="http://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
#WSDL="http://www.afip.gov.ar/fe/documentos/wsdl_viejo_wsfe.xml"

class WSFEv1:
    "Interfase para el WebService de Factura Electr�nica Version 1"
    _public_methods_ = ['CrearFactura', 'AgregarIva', 'CAESolicitar', 
                        'AgregarTributo', 'AgregarCmpAsoc',
                        'Dummy', 'Conectar', ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Reproceso',
        'CAE','Vencimiento', 'Eventos', 'Errs',
        'CbteNro', 'FechaCbte', 'ImpTotal']
        
    _reg_progid_ = "WSFEv1"
    _reg_clsid_ = "{CA0E604D-E3D7-493A-8880-F6CDD604185E}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologaci�n' or '')
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None

    def Conectar(self,cache="cache"):
        # cliente soap del web service
        self.client = SoapClient( 
            wsdl = WSDL,        
            cache = cache,
            trace = "--trace" in sys.argv)


    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.FEDummy()['FEDummyResult']
        self.AppServerStatus = result['AppServer']
        self.DbServerStatus = result['DbServer']
        self.AuthServerStatus = result['AuthServer']

    def CrearFactura(self, concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz,
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportaci�n 
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto, 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
            }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        self.factura = fact

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'tipo': tipo, 'pto_vta': pto_vta, 'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)

    def AgregarTributo(self, id, desc, base_imp, alic, importe):
        "Agrego un tributo a una factura (interna)"
        tributo = { 'id': id, 'desc': desc, 'base_imp': base_imp, 
                    'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)

    def AgregarIva(self, id, base_imp, importe):
        "Agrego un tributo a una factura (interna)"
        iva = { 'id': id, 'base_imp': base_imp, 'importe': importe }
        self.factura['iva'].append(iva)

    def CAESolicitar(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 1, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    'FchServDesde': f['fecha_serv_desde'],
                    'FchServHasta': f['fecha_serv_hasta'],
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']],
                    }
                }]
            })
        
        result = ret['FECAESolicitarResult']
        fecabresp = result['FeCabResp']
        self.Resultado = fecabresp['Resultado']
        print result['FeDetResp']
        fedetresp = result['FeDetResp'][0]['FECAEDetResponse']
        # Obs:
        #self.Obs = auth['obs'].strip(" ")
        #self.Reproceso = auth['reproceso']
        self.CAE = fedetresp['CAE']
        #vto = str(auth['fch_venc_cae'])
        #self.Vencimiento = "%s/%s/%s" % (vto[6:8], vto[4:6], vto[0:4])
        #self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]
        return self.CAE



def main():
    "Funci�n principal de pruebas (obtener CAE)"
    import os, time

    # obteniendo el TA
    TA = "TA-wsfe.xml"
    if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsfe")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        ta_string = wsaa.call_wsaa(cms)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    # fin TA

    wsfev1 = WSFEv1()
    wsfev1.Cuit = "20267565393"
    wsfev1.Token = str(ta.credentials.token)
    wsfev1.Sign = str(ta.credentials.sign)

    wsfev1.Conectar()
    
    if "--dummy" in sys.argv:
        print wsfev1.client.help("FEDummy")
        wsfev1.Dummy()
        print "AppServerStatus", wsfev1.AppServerStatus
        print "DbServerStatus", wsfev1.DbServerStatus
        print "AuthServerStatus", wsfev1.AuthServerStatus
    
    if "--prueba" in sys.argv:
        print wsfev1.client.help("FECAESolicitar").encode("latin1")

        tipo_cbte = 2
        punto_vta = 4001
        cbte_nro = 0
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        concepto = 1
        tipo_doc = 80; nro_doc = "20267565393"
        cbt_desde = cbte_nro + 1; cbt_hasta = cbte_nro + 1
        imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
        imp_iva = "21.00"; imp_trib = "1.00"; imp_op_ex = "0.00"
        fecha_cbte = fecha; fecha_venc_pago = fecha
        # Fechas del per�odo del servicio facturado (solo si concepto = 1?)
        fecha_serv_desde = fecha; fecha_serv_hasta = fecha
        moneda_id = 'PES'; moneda_ctz = '1.000'

        wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz)
        
        if tipo_cbte not in (1, 2):
            tipo = 19
            pto_vta = 2
            nro = 1234
            wsfev1.AgregarCmpAsoc(tipo, pto_vta, nro)
        
        id = 99
        desc = 'Impuesto Municipal Matanza'
        base_imp = 100
        alic = 1
        importe = 1
        wsfev1.AgregarTributo(id, desc, base_imp, alic, importe)

        id = 5 # 21%
        base_im = 100
        importe = 21
        wsfev1.AgregarIva(id, base_imp, importe)
        
        wsfev1.CAESolicitar()
        
        print "Resultado", wsfev1.Resultado
        print "CAE", wsfev1.CAE
        

if __name__ == '__main__':

    if "/register" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSFEv1)
    else:
        main()
