import arcpy
import os
from configparser import ConfigParser
import logging
from arcpy import env

def out(transetti,cavidotti_longitudinali,gdb,out_gdb,dist):

    config = ConfigParser()
    # get the path to config.ini
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    # check if the path is to a valid file
    config.read(config_path)
    #logging
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=logging.INFO)
    logging.info('**** Sono entrato nel Modulo OUTPUT ****')

    # Dati di input
    # feauture dataset di output in base alla distanza di ricerca
    fdata = "Dati_" + dist
    fgdb = str(out_gdb + '\\' + fdata)
    env.workspace = gdb
    env.overwriteOutput = True


    try:
        cavidotti_e_transetti = [transetti,cavidotti_longitudinali]
        out_cav = (fgdb+"\\Cavidotti"+dist)
        ca = arcpy.management.Merge(cavidotti_e_transetti,out_cav,"NO_SOURCE_INFO")
        t = int(arcpy.GetCount_management(transetti).getOutput(0))
        logging.info('Il totale dei transetti e" {}'.format(t))
        c = int(arcpy.GetCount_management(cavidotti_longitudinali).getOutput(0))
        logging.info('Il totale dei cavidotti longitudinali e" {}'.format(c))
        ca = int(arcpy.GetCount_management(ca).getOutput(0))
        logging.info('Il totale dei cavidotti e" {}'.format(ca))
        logging.info('Ho generato i Cavidotti - unione di Transetti e Cavidotti longitudinali')

        #produco i pozzetti di attraversamento presenti solo se il binario (route) attraversa i transetti

        route =gdb + "\\Route"
        tran_select = arcpy.management.SelectLayerByLocation(transetti,"INTERSECT",route,None,"NEW_SELECTION","NOT_INVERT")
        po = arcpy.management.FeatureVerticesToPoints(tran_select,fgdb+"\\Pozzetti_atr"+dist,"DANGLE")
        p = int(arcpy.GetCount_management(po).getOutput(0))
        logging.info('Il totale pozzetti di attraversamento e" {}'.format(p))
        logging.info('Ho generato i Pozzetti di Attraversamento - Intersezione tra Transetti e Route')
    except Exception as e:
        logging.error("!!! Lo script si e' interrotto !!!", exc_info=True)
