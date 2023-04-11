import pandas as pd


def inverti_campi(df):
    for index,row in df.iterrows():
        if row['Punto iniziale SI'] > row['Punto finale SI']:
            df.at[index, 'Punto iniziale SI'], df.at[index, 'Punto finale SI'] = df.at[index, 'Punto finale SI'], df.at[index, 'Punto iniziale SI']
    return df

def read_excel_to_dataframe(excel_file):
    df = pd.read_csv(excel_file, sep=',')
    return df

def select_row_with_a_charact(df, codice):
    select_df = df[df['Codice caratteristica'] == codice]
    return select_df

def subset_nonzero_lenght(df):
    return df[df["Lunghezza SI"] != 0]

def confronta_dataframe(df1,df2):
    #lista_risultati = []
    nuove_righe = []
    for index, riga1 in df1.iterrows():

        nuova_riga = {'Unnamed: 0': riga1[0], 'Codice caratteristica': riga1[1], 'Valore car.': riga1[2],
                      'Valore car. Numerico': riga1[3], 'Punto iniziale SI': riga1[4], 'Punto finale SI': riga1[5],
                      'Lunghezza SI': riga1[6], 'Sede Tecnica MUIF': riga1[7], 'Lato_posa': riga1[8]}

        punto_iniziale1 = nuova_riga['Punto iniziale SI']
        punto_finale1 = nuova_riga['Punto finale SI']
        selezione = df2[df2['Sede Tecnica MUIF'] == nuova_riga['Sede Tecnica MUIF']]
        # contatore che utilizzo per prendere tutte le SETE che si trovano sia a DX che SX
        # se 0 modifico le linea, se > 0 crea una riga nuova
        count = 0
        for index2, riga2 in selezione.iterrows():
            punto_iniziale2 = riga2['Punto iniziale SI']
            punto_finale2 = riga2['Punto finale SI']
            valore_car = riga2['Valore car.']
            if punto_iniziale2 <= punto_iniziale1 <= punto_finale2 and punto_iniziale2 <= punto_finale1 <= punto_finale2:
            #if punto_iniziale1 >= punto_iniziale2 and punto_finale1 <= punto_finale2:
                if count == 0:
                    count += 1
                    nuova_riga["Lato_posa"] = valore_car
                    if valore_car == 'SX':
                        if nuova_riga['Valore car. Numerico'] >= 0:
                            nuova_riga['Valore car. Numerico'] = -(nuova_riga['Valore car. Numerico'])
                        else:
                            nuova_riga["Lato_posa"] = nuova_riga['Valore car. Numerico']
                    nuove_righe.append(nuova_riga)
                else:
                    count += 1
                   #nuova_riga = df1.iloc[index].copy()
                    nuova_riga = {'Unnamed: 0': riga1[0],'Codice caratteristica':riga1[1], 'Valore car.':riga1[2],
                                  'Valore car. Numerico':riga1[3],'Punto iniziale SI': riga1[4],'Punto finale SI':riga1[5],
                                  'Lunghezza SI':riga1[6],'Sede Tecnica MUIF':riga1[7],'Lato_posa': riga1[8]}
                    nuova_riga["Lato_posa"] = valore_car
                    if valore_car == 'SX':
                        nuova_riga['Valore car. Numerico'] = -(nuova_riga['Valore car. Numerico'])
                    nuove_righe.append(nuova_riga)

        if nuova_riga["Lato_posa"] not in ['SX', 'DX']:
            count_2 = 0
            for index2, riga2 in selezione.iterrows():
                punto_iniziale2 = riga2['Punto iniziale SI']
                punto_finale2 = riga2['Punto finale SI']

                valore_car = riga2['Valore car.']
                intervallo_A_B = (punto_iniziale1, punto_finale1)
                intervallo_C_D = (punto_iniziale2, punto_finale2)
                if intervallo_A_B[1] >= intervallo_C_D[0] and intervallo_A_B[0] <= intervallo_C_D[1]:
                    sottoinsieme = [max(intervallo_A_B[0], intervallo_C_D[0]), min(intervallo_A_B[1],intervallo_C_D[1])]
                    if sottoinsieme[0] != sottoinsieme[1]:

                        if count_2 >= 1:
                            nuova_riga = {'Unnamed: 0': riga1[0], 'Codice caratteristica': riga1[1],
                                          'Valore car.': riga1[2],
                                          'Valore car. Numerico': riga1[3], 'Punto iniziale SI': riga1[4],
                                          'Punto finale SI': riga1[5],
                                          'Lunghezza SI': riga1[6], 'Sede Tecnica MUIF': riga1[7], 'Lato_posa': riga1[8]}

                        nuova_riga["Lato_posa"] = valore_car
                        if punto_iniziale2 >= punto_iniziale1:
                            nuova_riga['Punto iniziale SI'] = punto_iniziale2
                        if punto_finale2 <= punto_finale1:
                            nuova_riga['Punto finale SI'] = punto_finale2
                        nuova_riga["Lato_posa"] = valore_car
                        if nuova_riga["Lato_posa"] == 'SX':
                            if nuova_riga['Valore car. Numerico'] >= 0:
                                nuova_riga['Valore car. Numerico'] = -(nuova_riga['Valore car. Numerico'])
                            else:
                                nuova_riga['Valore car. Numerico'] = nuova_riga['Valore car. Numerico']
                        count_2 += 1
                        nuove_righe.append(nuova_riga)
                    else:
                        pass

    df2 = pd.DataFrame(nuove_righe)
    return df2


def aggiungi_colonna_Lato_Posa(df1):
    df1['Lato_posa'] = pd.Series(dtype=str)
    return df1

def export_csv(df, path):
    df.to_csv(path, index=False)

def filtro_lato_posa_NULL_value(df):
    filtro = df['Lato_posa'].isin(['SX','DX'])
    return df[filtro]

def replace_comma_with_dot(df):
    for col in ['Punto iniziale SI', 'Punto finale SI', 'Lunghezza SI']:
        df[col] = df[col].apply(lambda x: str(x).replace(',','.'))
    return df

def main_excel(excel_file, path_output):

    # mi salvo il pandas dataframe da csv
    df = read_excel_to_dataframe(excel_file)
    # inverto i valori dei campi se Punto iniziale > Punto finale
    df = inverti_campi(df)
    # seleziono i tratti di cavidotti che devo creare
    selected_df_030 = select_row_with_a_charact(df, 'S01500_0030')
    # dei cavidotti precedenti faccio un subset togliendo quelli con lunghezza = 0
    selected_df_030 = subset_nonzero_lenght(selected_df_030)
    # aggiungo la colonna lato di posa
    selected_df_030 = aggiungi_colonna_Lato_Posa(selected_df_030)
    # seleziono le righe con la info di lato DX e SX
    selected_df_020 = select_row_with_a_charact(df, 'S01500_0020')
    # elimino i lati di posa con lunghezza pari a 0
    selected_df_020 = subset_nonzero_lenght(selected_df_020)
    # confronto per ogni SETE del primo DF le coordinate con il seocndo DF e prendo la info di lato
    df_output = confronta_dataframe(selected_df_030,selected_df_020)
    #bonifico il df prima di salvarlo, mantenendo solo i lati SX e DX
    df_output = filtro_lato_posa_NULL_value(df_output)
    # cambio in alcuni campi la virgola con il punto
    df_output = replace_comma_with_dot(df_output)
    # esporto il nuovo df in csv
    export_csv(df_output, path_output)
