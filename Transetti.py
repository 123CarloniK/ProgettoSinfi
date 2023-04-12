import arcpy
import os
from configparser import ConfigParser
import logging
def transetti_fun(gdb, gdb_tr,pozzetti,cavidotti,route,dist,out_gdb):
    config = ConfigParser()
    # get the path to config.ini
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    # check if the path is to a valid file
    config.read(config_path)
    #logging
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=logging.INFO)
    logging.info('**** Ho iniziato lo script TRANSETTI ****')
    arcpy.env.overwriteOutput = True
    # Dati di input
    fdata = "Dati_" + dist
    fgdb = str(out_gdb + '\\' + fdata)

    # Genero i vertici per creare i transetti dai cavidotti
    arcpy.management.FeatureVerticesToPoints(cavidotti,pozzetti,"DANGLE")
    dist = str(dist)
    vertici_dist = "Pozzetti" + dist
    arcpy.conversion.FeatureClassToFeatureClass(gdb+"\\Pozzetti", fgdb, vertici_dist, "", )
    logging.info('Ho generato i vertici')

    # Salvo i vertici per la distanza dist

    #creo campi near
    arcpy.analysis.Near(pozzetti, route, None, "LOCATION", "ANGLE", "PLANAR", "NEAR_FID NEAR_FID;NEAR_DIST NEAR_DIST;NEAR_X NEAR_X;NEAR_Y NEAR_Y;NEAR_ANGLE NEAR_ANGLE","")

    arcpy.management.CalculateField(pozzetti, "NEAR_Y", "int(!NEAR_Y!/10)", "PYTHON3", "", "TEXT", "NO_ENFORCE_DOMAINS")

    arcpy.management.AddField(pozzetti, "NY", "LONG", None, None, None, "", "NULLABLE", "NON_REQUIRED", "")

    arcpy.management.CalculateField(pozzetti, "NY", "!NEAR_Y!", "PYTHON3", "", "LONG", "NO_ENFORCE_DOMAINS")

    # Genero i transetti con Se.Te in comune

    trv1 = arcpy.analysis.GenerateOriginDestinationLinks( pozzetti, pozzetti, os.path.join(gdb_tr, 'Transetti_V1'), "Sede_Tecnica_MUIF", "Sede_Tecnica_MUIF", "PLANAR", 1, dist, "METERS", "NO_AGGREGATE", None)
    logging.info('Ho generato i transetti per sede tecnica')
    # Seleziono i pozzetti che non sono interessati già dalla creazione dei transetti V1
    pozzetti_v2= arcpy.management.SelectLayerByLocation(pozzetti,"INTERSECT", gdb_tr+"\\Transetti_V1", None, "NEW_SELECTION", "INVERT")
    # Genero i transetti in base alla chilometrica inizio fine
    trv2 = arcpy.analysis.GenerateOriginDestinationLinks(pozzetti_v2,pozzetti_v2,gdb_tr+"\\Transetti_V2", "Punto_iniziale_SI","Punto_finale_SI", "PLANAR", 1, dist, "METERS", "NO_AGGREGATE", None)
    # Unisco i transetti V1 e V2
    input_transetti=[trv1,trv2]
    arcpy.management.Merge(input_transetti,gdb_tr+"\\Transetti_V1_V2","NO_SOURCE_INFO")
    logging.info('Ho unito i transetti chilometrica e sede tecnica')

    elimina = arcpy.management.SelectLayerByLocation(gdb_tr+"\\Transetti_V1_V2","SHARE_A_LINE_SEGMENT_WITH",cavidotti,None,"NEW_SELECTION","NOT_INVERT")

    arcpy.management.DeleteRows(elimina)

    logging.info('ho eliminati i transetti sovrapposti ai cavidotti')
    # Seleziono i pozzetti che non sono interessati già dalla creazione dei transetti V2

    pozzetti_v3= arcpy.management.SelectLayerByLocation(pozzetti,"INTERSECT",gdb_tr+"\\Transetti_V1_V2",None,"NEW_SELECTION","INVERT")


    trv3 = arcpy.analysis.GenerateOriginDestinationLinks(pozzetti_v3,pozzetti_v3,gdb_tr+"\\Transetti_V4","NY","NY","PLANAR",1,dist,"METERS","NO_AGGREGATE",None)
    logging.info('Ho generato i transetti per NEAR_Y')

    # Merge dei transetti
    arcpy.management.Merge([trv1,trv2,trv3],gdb_tr+"\\Transetti","NO_SOURCE_INFO")
    logging.info('Ho unito i transetti')
    # seleziono i cavidotti corrispondenti sui transetti e li elimino

    arcpy.management.DeleteRows(
        in_rows= arcpy.management.SelectLayerByLocation(gdb_tr+"\\Transetti","SHARE_A_LINE_SEGMENT_WITH",cavidotti,None,"NEW_SELECTION","NOT_INVERT"))
    arcpy.management.DeleteIdentical(gdb_tr+"\\Transetti","Shape",None,0)
    logging.info('Ho cancellato i transetti identici geometricamente')
