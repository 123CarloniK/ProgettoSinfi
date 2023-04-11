#### Python 3.7

import arcpy
import pandas as pd
import os
from configparser import ConfigParser
import logging
from arcpy import env
from lato_posa import main_excel
import Transetti
import cardinalita
import out_elab

config = ConfigParser()
# get the path to config.ini
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
# check if the path is to a valid file
config.read(config_path)
#logging
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=logging.INFO)
logging.info('**** Ho iniziato lo script ****')
try:

    # Dati di input
    path = config.get('data-input','path')
    gdb = config.get('data-input','gdb')
    dati_ine = config.get('data-input','csv')
    lato_posa = config.get('data-input','lato_posa')
    tab_lato = config.get('data-input','tab_lato')
    tab_route = config.get('data-input', 'tab_route')
    route_bin_c = config.get('data-input','route')
    bin_c = config.get('data-input','binari')
    coord_sys= config.get('data-input','coord_sys')
    #feauture dataset di output in base alla distanza di ricerca
    out_gdb = config.get('data-input', 'out_gdb')
    dist = config.get('data-input', 'search_distance')
    fdata="Dati_" + dist
    fgdb = str(out_gdb+ '\\' + fdata)
    env.workspace = gdb
    env.overwriteOutput = True

    logging.info('**** INIZIO Elaborazione tabella CSV ****')

    # Elaborazione del CSV proveniente da INE
    df_ine = pd.read_csv(dati_ine, sep=';')

    # Tolgo la prima colonna vuota
    df_ine = df_ine.iloc[:, 1:]

    # Creo un campo sede tecnica MUIF
    df_ine["Sede Tecnica MUIF"] = df_ine['Sede Tecnica'].str.replace('CV', 'BC')

    # Modifico il separatore per i numeri decimali da , a .
    df_ine['Valore car. Numerico'] = df_ine['Valore car. Numerico'].str.replace(',', '.')
    df_ine['Punto iniziale SI'] = df_ine['Punto iniziale SI'].str.replace(',', '.')
    df_ine['Punto finale SI'] = df_ine['Punto finale SI'].str.replace(',', '.')
    df_ine['Lunghezza SI'] = df_ine['Lunghezza SI'].str.replace(',', '.')

    #Converto la distanza binario in float
    df_ine['Distanza Binario'] = pd.to_numeric(df_ine['Valore car. Numerico'])
    df_ine['Valore car. Numerico'] = df_ine['Valore car. Numerico'].astype(float)

    # generazione tabella per route
    tab_route_ = df_ine[(df_ine["Codice caratteristica"] == "S01500_0010")]
    tab_route_ = tab_route_.filter(items=['Punto iniziale SI', 'Punto finale SI', 'Sede Tecnica MUIF'])
    tab_route_.to_csv(path + 'tab_route.csv')

    # generazione tabella lato sx dx
    tab_lato_ = df_ine[(df_ine["Codice caratteristica"] == "S01500_0020") | (df_ine["Codice caratteristica"] == "S01500_0030")]
    tab_lato_ = tab_lato_.filter(
        items=['Codice caratteristica', 'Valore car.', 'Valore car. Numerico', 'Punto iniziale SI', 'Punto finale SI',
               'Lunghezza SI', 'Sede Tecnica MUIF'])
    tab_lato_.to_csv(path + 'tab_lato.csv')

    # Richiamo lo script che determina il lato sinistro e destro del cavidotto
    logging.info('Sono entrato nel modulo determina lato posa\n')
    main_excel(os.path.join(path, 'tab_lato.csv'),lato_posa)
    logging.info('**** Ho creato il CSV per l"event table **** \n')
    logging.info('**** FINE Elaborazione tabella CSV **** INIZIO Elaborazione GIS **** \n')

    #seleziona i binari Dispari e Unici
    bin_c1= arcpy.management.SelectLayerByAttribute(bin_c,"NEW_SELECTION","S16000_0010 = '2' Or S16000_0010 = '3'",None)

    # Eseguo il join con i binari di corsa e la sua route
    # route join binari
    j_bin_route = arcpy.management.AddJoin(route_bin_c, "SETE", bin_c1, "SEDE_TECNICA", "KEEP_ALL")
    # binari join route
    #j_bin_route = arcpy.management.AddJoin(bin_c1, "SEDE_TECNICA",route_bin_c, "SETE", "KEEP_ALL")

    arcpy.conversion.FeatureClassToFeatureClass(j_bin_route, gdb, "j_bin_route", "", )

    #dissolve delle sede tecniche per evitare errori nella generazione dei cavidotti
    arcpy.management.Dissolve("j_bin_route", "j_bin_route_diss", 'SEDE_TECNICA')

    #importa tabella csv nel geodatabase (possibile evolutiva imoporta df pandas)
    arcpy.conversion.TableToGeodatabase(tab_route, gdb)
    arcpy.conversion.TableToGeodatabase(tab_lato, gdb)
    arcpy.conversion.TableToGeodatabase(lato_posa, gdb)
    # Join per la creazione della route
    V_16000_join_Route = arcpy.management.AddJoin("j_bin_route_diss","SEDE_TECNICA",gdb+"\\tab_route","Sede_Tecnica_MUIF","KEEP_COMMON","NO_INDEX_JOIN_FIELDS")
    # Cancellla se risolto verifica con cosa viene creata la route
    arcpy.conversion.FeatureClassToFeatureClass(V_16000_join_Route, gdb, "V_16000_join_Route", "", )
    # Creo la route
    route= arcpy.lr.CreateRoutes(V_16000_join_Route,"tab_route.Sede_Tecnica_MUIF","Route","TWO_FIELDS","tab_route.Punto_iniziale_SI","tab_route.Punto_finale_SI","UPPER_LEFT",1,0,"IGNORE","INDEX")
    logging.info('Ho generato la nuova route\n')
    #arcpy.conversion.ExportFeatures(route, out_features="route_")

    #Creo i cavidotti
    cavidotti = arcpy.lr.MakeRouteEventLayer(route,"Sede_Tecnica_MUIF",gdb+"\\lato_posa","Sede Tecnica MUIF; LINE; Punto iniziale SI; Punto finale SI","lato_posa Events","Valore_car__Numerico","NO_ERROR_FIELD","NO_ANGLE_FIELD","NORMAL","ANGLE","RIGHT","POINT")

    cavidotti = arcpy.management.FeatureToLine(cavidotti,gdb+"\\Cavidotti_FeatureToLine",None,"ATTRIBUTES")
    #Eseguo la pulizzia dei cavidotti trim e extent a 1,5m
    arcpy.edit.TrimLine(cavidotti,"1.5 Meters","DELETE_SHORT")
    arcpy.edit.ExtendLine(cavidotti,"1.5 Meters","EXTENSION")

    # Salvo i cavidotti
    arcpy.conversion.FeatureClassToFeatureClass(cavidotti, gdb,"Cavidotti","",)
    logging.info('Ho generato i cavidotti\n')
    # Salvo i cavidotti longitudinali con sede tecnica e distanza dist
    arcpy.management.CreateFeatureDataset(out_gdb,fdata,coord_sys)
    cavidotti_dist= "Cavidotti_long" + dist
    arcpy.conversion.FeatureClassToFeatureClass(cavidotti, fgdb, cavidotti_dist, "",)
    logging.info(' Ho salvato i cavidotti longitudinali a distanza {}\n'.format(dist))

    logging.info('**** Entro nel modulo generazione Transetti ****')

    Transetti.transetti()
    logging.info('**** Ripulisco i Transetti con cardinalità maggiore di uno ****')
    cardinalita.cardi()
    out_elab.out()

    logging.info('**** FINE Elaborazione GIS ****')

    logging.info('**** Ho terminato lo script ****')


except Exception as e:
    logging.error("!!! Lo script si e' interrotto !!!", exc_info=True)
