import arcpy
import os
from configparser import ConfigParser
import logging
def transetti():
    config = ConfigParser()
    # get the path to config.ini
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    # check if the path is to a valid file
    config.read(config_path)
    #logging
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=logging.INFO)
    logging.info('**** Ho iniziato lo script TRANSETTI ****')

    # Dati di input

    gdb = config.get('data-input','gdb_tr')
    cavidotti = config.get('data-input','cavidotti')
    pozzetti = config.get('data-input','pozzetti')
    route = config.get('data-input','route_new')
    dist = config.get('data-input','search_distance') #verificare distanze
    arcpy.env.overwriteOutput = True


    # Genero i pozzetti per creare i transetti dai cavidotti
    arcpy.management.FeatureVerticesToPoints(cavidotti,pozzetti,"DANGLE")
    logging.info('Ho generato i vertici')

    #creo campi near
    arcpy.analysis.Near(pozzetti, route, None, "LOCATION", "ANGLE", "PLANAR", "NEAR_FID NEAR_FID;NEAR_DIST NEAR_DIST;NEAR_X NEAR_X;NEAR_Y NEAR_Y;NEAR_ANGLE NEAR_ANGLE","")

    arcpy.management.CalculateField(pozzetti, "NEAR_Y", "int(!NEAR_Y!/10)", "PYTHON3", "", "TEXT", "NO_ENFORCE_DOMAINS")

    arcpy.management.AddField(pozzetti, "NY", "LONG", None, None, None, "", "NULLABLE", "NON_REQUIRED", "")

    arcpy.management.CalculateField(pozzetti, "NY", "!NEAR_Y!", "PYTHON3", "", "LONG", "NO_ENFORCE_DOMAINS")

    # Genero i transetti con Se.Te in comune

    trv1 = arcpy.analysis.GenerateOriginDestinationLinks( pozzetti, pozzetti, os.path.join(gdb, 'Transetti_V1'), "Sede_Tecnica_MUIF", "Sede_Tecnica_MUIF", "PLANAR", 1, dist, "METERS", "NO_AGGREGATE", None)
    logging.info('Ho generato i transetti per sede tecnica')
    # Seleziono i pozzetti che non sono interessati già dalla creazione dei transetti V1
    pozzetti_v2= arcpy.management.SelectLayerByLocation(pozzetti,"INTERSECT", gdb+"\\Transetti_V1", None, "NEW_SELECTION", "INVERT")
    # Genero i transetti in base alla chilometrica inizio fine
    trv2 = arcpy.analysis.GenerateOriginDestinationLinks(pozzetti_v2,pozzetti_v2,gdb+"\\Transetti_V2", "Punto_iniziale_SI","Punto_finale_SI", "PLANAR", 1, dist, "METERS", "NO_AGGREGATE", None)
    # Unisco i transetti V1 e V2
    arcpy.management.Merge(
        inputs=r"'C:\MUIF\SINFI\NUOVA SOLUZIONE_CAVIDOTTI\Prj_gis\Cavidotti\Transetti.gdb\Transetti_V1';'C:\MUIF\SINFI\NUOVA SOLUZIONE_CAVIDOTTI\Prj_gis\Cavidotti\Transetti.gdb\Transetti_V2'",
        output=gdb+"\\Transetti_V1_V2",
        field_mappings='Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Transetti_v1,Shape_Length,-1,-1,Transetti_v2,Shape_Length,-1,-1;ORIG_FID "ORIG_FID" true true false 4 Long 0 0,First,#,Transetti_v1,ORIG_FID,-1,-1,Transetti_v2,ORIG_FID,-1,-1;ORIG_X "ORIG_X" true true false 8 Double 0 0,First,#,Transetti_v1,ORIG_X,-1,-1,Transetti_v2,ORIG_X,-1,-1;ORIG_Y "ORIG_Y" true true false 8 Double 0 0,First,#,Transetti_v1,ORIG_Y,-1,-1,Transetti_v2,ORIG_Y,-1,-1;DEST_FID "DEST_FID" true true false 4 Long 0 0,First,#,Transetti_v1,DEST_FID,-1,-1,Transetti_v2,DEST_FID,-1,-1;DEST_X "DEST_X" true true false 8 Double 0 0,First,#,Transetti_v1,DEST_X,-1,-1,Transetti_v2,DEST_X,-1,-1;DEST_Y "DEST_Y" true true false 8 Double 0 0,First,#,Transetti_v1,DEST_Y,-1,-1,Transetti_v2,DEST_Y,-1,-1;LINK_DIST "LINK_DIST" true true false 8 Double 0 0,First,#,Transetti_v1,LINK_DIST,-1,-1,Transetti_v2,LINK_DIST,-1,-1;GROUP_ID "GROUP_ID" true true false 5000 Text 0 0,First,#,Transetti_v1,GROUP_ID,0,5000,Transetti_v2,GROUP_ID,-1,-1;COLOR_ID "COLOR_ID" true true false 4 Long 0 0,First,#,Transetti_v1,COLOR_ID,-1,-1,Transetti_v2,COLOR_ID,-1,-1',
        add_source="NO_SOURCE_INFO"
    )
    logging.info('Ho unito i transetti chilometrica e sede tecnica')

    elimina = arcpy.management.SelectLayerByLocation(gdb+"\\Transetti_V1_V2","SHARE_A_LINE_SEGMENT_WITH",cavidotti,None,"NEW_SELECTION","NOT_INVERT")

    arcpy.management.DeleteRows(elimina)

    logging.info('ho eliminati i transetti sofrapposti ai cavidotti')
    # Seleziono i pozzetti che non sono interessati già dalla creazione dei transetti V2

    pozzetti_v3= arcpy.management.SelectLayerByLocation(pozzetti,"INTERSECT",gdb+"\\Transetti_V1_V2",None,"NEW_SELECTION","INVERT")


    trv3 = arcpy.analysis.GenerateOriginDestinationLinks(pozzetti_v3,pozzetti_v3,gdb+"\\Transetti_V4","NY","NY","PLANAR",1,dist,"METERS","NO_AGGREGATE",None)
    logging.info('Ho generato i transetti per NEAR_Y')

    # Merge dei transetti
    arcpy.management.Merge([trv1,trv2,trv3],gdb+"\\Transetti","NO_SOURCE_INFO")
    logging.info('Ho unito i transetti')
    # seleziono i cavidotti corrispondenti sui transetti e li elimino

    arcpy.management.DeleteRows(
        in_rows= arcpy.management.SelectLayerByLocation(gdb+"\\Transetti","SHARE_A_LINE_SEGMENT_WITH",cavidotti,None,"NEW_SELECTION","NOT_INVERT"))
    arcpy.management.DeleteIdentical(
        in_dataset=gdb+"\\Transetti",
        fields="Shape",
        xy_tolerance=None,
        z_tolerance=0
    )
    logging.info('Ho cancellato i transetti identici geometricamente')

