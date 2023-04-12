import arcpy
from arcpy import env
from arcpy import management
import logging
import os

from configparser import ConfigParser

def cardi(gdb,gdb_tr,out_gdb,dist):
    config = ConfigParser()
    # get the path to config.ini
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    # check if the path is to a valid file
    config.read(config_path)

    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=logging.INFO)
    logging.info('**** Ho cominciato lo script CARDINALITA ****')


    try:
        # Dati d'input
        tran_card1 = "tran_card1"
        # Variabili
        transetti = config.get('data-input', 'transetti')
        out_pozzetti = "pozzetti_inter"
        out_transetti = "out_transetti"
        transetti_sort2 = "transetti_sort2"
        # feauture dataset di output in base alla distanza di ricerca
        arcpy.env.overwriteOutput = True
        fdata = "Dati_" + dist
        fgdb = str(out_gdb + '\\' + fdata)
        #
        env.workspace = gdb
        env.overwriteOutput = True
        arcpy.MakeFeatureLayer_management(transetti, "transetti")
        arcpy.CreateFeatureclass_management(gdb, out_transetti, "POLYLINE", "", "", "", transetti)
        arcpy.CreateFeatureclass_management(gdb, transetti_sort2, "POLYLINE", "", "", "", transetti)
        arcpy.CreateFeatureclass_management(gdb, tran_card1, "POLYLINE", "", "", "", transetti)


        pozzetti_V2 = arcpy.analysis.SpatialJoin("Pozzetti","Transetti", gdb + "\\Pozzetti_V2",
            "JOIN_ONE_TO_ONE","KEEP_ALL","INTERSECT", None,"")
        pozzetti= arcpy.management.SelectLayerByAttribute("Pozzetti_V2","NEW_SELECTION","Join_Count > 1",None)

        # cerco i pozzetti che intercettano i transetti
        with arcpy.da.SearchCursor(pozzetti, ['Shape@']) as cursor:
            conto=0
            conto2=0
            for row in cursor:
                # usa la geometria per la selezione
                pozz = row[0]
                #seleziona la coppia di transetti del pozzo[n]
                sele_transetto = arcpy.SelectLayerByLocation_management("transetti", "INTERSECT", pozz, "", "NEW_SELECTION")
                #arcpy.MakeFeatureLayer_management(sele_transetto, "sele_transetto")
                n = int(arcpy.GetCount_management("transetti").getOutput(0))
                #print("la selezione ha {0} oggetti".format(n))
                env.overwriteOutput = True
                #Ordino gli elementi dal più corto al più lungo
                sort_transetto = [["Shape_Length", "ASCENDING"]]
                arcpy.management.Sort("transetti", "sele_transetto_sort", sort_transetto)
                arcpy.MakeFeatureLayer_management("sele_transetto_sort", "sele_transetto_sort_lyr")
                arcpy.management.SelectLayerByAttribute("sele_transetto_sort_lyr", "NEW_SELECTION", "OBJECTID=1")
                if n==0:
                    #print("Cardinalità 0")
                    pass
                elif n == 1:
                    conto+=1
                    arcpy.management.Append("sele_transetto_sort_lyr", tran_card1, "NO_TEST")
                    #print("Cardinalità 1 ha un transetto collegato aggiunto {0}".format(conto))
                elif n > 1:
                    conto2 += 1
                    arcpy.management.Append("sele_transetto_sort_lyr", out_transetti, "NO_TEST")
                    #print("Cardinalità maggiore di 1 ha più di un transetto collegato {0}".format(conto2))
                arcpy.Delete_management("sele_transetto_lyr")
        logging.info("Abbiamo {0} transetti con cardinalita' 1 e {1} con cardinalita' superiore".format(conto,conto2))
        #Tolgo dai transetti quelli che coincidono con quelli con cardinalità maggiore di 1

        arcpy.DeleteRows_management(arcpy.SelectLayerByLocation_management(tran_card1, "BOUNDARY_TOUCHES", out_transetti, None, "NEW_SELECTION", "NOT_INVERT"))
        #sommo i transetti di cardinalità 1 e maggiore di 1
        arcpy.management.Append(out_transetti, tran_card1, "NO_TEST")
        arcpy.management.DeleteIdentical("tran_card1", "Shape", None, 0)
        m = arcpy.GetCount_management(tran_card1)
        arcpy.CopyFeatures_management("tran_card1", "transetti_new")
        arcpy.analysis.SpatialJoin(pozzetti,"transetti_new","VERTICI_ESTREMI__SpatialJoin","JOIN_ONE_TO_ONE","KEEP_ALL","INTERSECT",None)
        arcpy.MakeFeatureLayer_management("VERTICI_ESTREMI__SpatialJoin","Vertici_Nuovi")
        arcpy.management.SelectLayerByAttribute("Vertici_Nuovi","NEW_SELECTION","Join_Count = 2","INVERT")
        arcpy.management.DeleteRows(in_rows="Vertici_Nuovi")
        arcpy.CopyFeatures_management("Vertici_Nuovi", gdb + "\\pozzetti_new")
        # Ciclo di bonifica su transetti residuali con cardinalità maggiore uguale a 2
        # Seleziono i pozzetti che hanno cardinalità maggiore di 1
        #print("LAVORAZIONE SECONDO GIRO")

        with arcpy.da.SearchCursor(gdb + "\\pozzetti_new", ['Shape@']) as cursor1:
            conto3 = 0
            for row1 in cursor1:
                # usa la geometria per la selezione
                pozz1 = row1[0]
                #seleziona la coppia di transetti del pozzo[n]
                sele_transetto1 = arcpy.SelectLayerByLocation_management("transetti_new", "INTERSECT", pozz1, "", "NEW_SELECTION")
                g = int(arcpy.GetCount_management(sele_transetto1).getOutput(0))
                #print("la selezione ha {0} oggetti".format(g))
                env.overwriteOutput = True
                if g==0:
                    #print("Cardinalita' 0")
                    pass
                if g==2:
                    conto3 += 1
                    sort_transetto = [["Shape_Length", "DESCENDING"]]
                    arcpy.management.Sort(sele_transetto1, "sele_transetto1_sort", sort_transetto)
                    arcpy.management.DeleteRows(
                        in_rows=arcpy.management.SelectLayerByAttribute("sele_transetto1_sort","NEW_SELECTION","OBJECTID = 1",None)
                    )
                    arcpy.Append_management("sele_transetto1_sort",transetti_sort2,"NO_TEST")
                    #print("Cardinalita' uguale a 3 sono {0} !!!".format(conto3))
                else:
                    pass
        # Tolgo gli elementi con cardinalità 3 con i transetti ottenuti con i cicli precendenti
        arcpy.management.DeleteRows(in_rows=arcpy.management.SelectLayerByLocation("tran_card1","BOUNDARY_TOUCHES","transetti_sort2",None,"NEW_SELECTION","NOT_INVERT"))
        # Aggiungo il complementare del risultato ottenuto con cardinalita' paria 3
        arcpy.Append_management(transetti_sort2, "tran_card1", "NO_TEST")
        arcpy.management.DeleteIdentical("tran_card1", "Shape", None, 0)
        tr_da_eliminare = arcpy.management.SelectLayerByLocation("Transetti","BOUNDARY_TOUCHES","tran_card1",None,"NEW_SELECTION","NOT_INVERT")

        arcpy.management.DeleteRows(tr_da_eliminare)

        #RIGENERA I VERTICI
        arcpy.management.FeatureVerticesToPoints("tran_card1","Pozzetti","DANGLE")
        arcpy.management.DeleteIdentical("tran_card1", "Shape", None, 0)
        #stampo il totale dei transetti ...
        logging.info('Il totale dei transetti è {0}'.format(int(arcpy.GetCount_management("tran_card1").getOutput(0))))
        # Rinomino i transetti

        logging.info('Ho rigenerato i pozzetti sono {0}'.format(int(arcpy.GetCount_management("Pozzetti").getOutput(0))))


        # Pulizia dei file accessori
        lista_pulisci = ["out_transetti", "pozzetti_new", "sele_transetto1_sort", "sele_transetto_sort", "transetti_new", "transetti_sort2",
                         "VERTICI_ESTREMI__SpatialJoin"]
        for fc in lista_pulisci:
            if arcpy.Exists(fc):
                arcpy.management.Delete(in_data=fc)

        logging.info('**** Ho terminato lo script ****')

        dist = str(dist)
        transetti_dist = "Transetti" + dist
        arcpy.conversion.FeatureClassToFeatureClass(gdb_tr + "\\Transetti", fgdb, transetti_dist, "", )

        logging.info('**** Ho terminato lo script CARDINALITA ****\n')
    except Exception as e:
        logging.error("!!! Lo script si e' interrotto !!!", exc_info=True)

