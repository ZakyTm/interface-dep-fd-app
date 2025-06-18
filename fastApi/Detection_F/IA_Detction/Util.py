import os

import numpy as np
import pandas as pd

from .Data import DataManager

Wilaya = {
    "Adrar": ["Adrar", "Adrar", "01-Adrar"],
    "Chlef": ["Chlef", "Chlef", "02-Chlef"],
    "Laghouat": ["Laghouat", "Laghouat", "03-Laghouat"],
    "Oum El Bouaghi": ["Oum El Bouaghi", "Oum El Bouaghi", "04-Oum El Bouaghi","oum"],
    "Batna": ["Batna", "Batna", "05-Batna"],
    "Bejaia": ["Bejaia", "Bejaïa", "06-Bejaia","béjaïa"],
    "Biskra": ["Biskra", "Biskra", "07-Biskra"],
    "Bechar": ["Bechar", "Béchar", "08-Bechar"],
    "Blida": ["Blida", "Blida", "09-Blida"],
    "Bouira": ["Bouira", "bouïra", "10-Bouira"],
    "Tamanrasset": ["Tamanrasset", "Tamanghasset", "11-Tamanrasset","tamenraset"],
    "Tebessa": ["Tebessa", "Tébessa", "12-Tebessa"],
    "Tlemcen": ["Tlemcen", "Tlemcen", "13-Tlemcen"],
    "Tiaret": ["Tiaret", "Tiaret", "14-Tiaret"],
    "Tizi Ouzou": ["Tizi Ouzou", "Tizi-Ouzou", "15-Tizi Ouzou"],
    "Alger": ["Alger", "Algiers", "16-Alger","alger centre"],
    "Djelfa": ["Djelfa", "Djelfa", "17-Djelfa"],
    "Jijel": ["Jijel", "Jijel", "18-Jijel","jjijel"],
    "Setif": ["Setif", "Sétif", "19-Setif","el eulma","taya"],
    "Saida": ["Saida", "Saïda", "20-Saida"],
    "Skikda": ["Skikda", "Skikda", "21-Skikda"],
    "Sidi Belabbes": ["Sidi Belabbes", "Sidi Bel Abbès", "22-Sidi Belabbes"],
    "Annaba": ["Annaba", "Annaba", "23-Annaba"],
    "Guelma": ["Guelma", "Guelma", "24-Guelma"],
    "Constantine": ["Constantine", "Constantine", "25-Constantine"],
    "Medea": ["Medea", "Médéa", "26-Medea"],
    "Mostaganem": ["Mostaganem", "Mostaganem", "27-Mostaganem"],
    "Msila": ["Msila", "M'sila", "28-Msila"],
    "Mascara": ["Mascara", "Mascara", "29-Mascara"],
    "Ouargla": ["Ouargla", "Ouargla", "30-Ouargla"],
    "Oran": ["Oran", "Oran", "31-Oran"],
    "El Bayadh": ["El Bayadh", "El Bayadh", "32-El Bayadh"],
    "Illizi": ["Illizi", "Illizi", "33-Illizi"],
    "Bordj Bou Arreridj": ["Bordj Bou Arreridj", "bordj bou arréridj", "34-Bordj Bou Arreridj"],
    "Boumerdes": ["Boumerdes", "Boumerdès", "35-Boumerdes"],
    "El Taref": ["El Taref", "El Tarf", "36-El Taref"],
    "Tindouf": ["Tindouf", "Tindouf", "37-Tindouf"],
    "Tissemsilt": ["Tissemsilt", "Tissemsilt", "38-Tissemsilt"],
    "El Oued": ["El Oued", "El Oued", "39-El Oued","eloued"],
    "Khenchela": ["Khenchela", "Khenchela", "40-Khenchela"],
    "Souk Ahras": ["Souk Ahras", "Souk Ahras", "41-Souk Ahras"],
    "Tipaza": ["Tipaza", "Tipasa", "42-Tipaza"],
    "Mila": ["Mila", "Mila", "43-Mila"],
    "Ain Defla": ["Ain Defla", "Aïn Defla", "44-Ain Defla"],
    "Naama": ["Naama", "Naâma", "45-Naama"],
    "Ain Temouchent": ["Ain Temouchent", "Aïn Témouchent", "46-Ain Temouchent"],
    "Ghardaia": ["Ghardaia", "Ghardaïa", "47-Ghardaia"],
    "Relizane": ["Relizane", "Relizane", "48-Relizane"],
    "Timimoun": ["Timimoun", "Timimoune", "49-Timimoun"],
    "Bordj Badji Mokhtar": ["Bordj Badji Mokhtar", "Bordj Badji Mokhtar", "50-Bordj Badji Mokhtar","bordj badji mokhta"],
    "Ouled Djellal": ["Ouled Djellal", "Ouled Djellal", "51-Ouled Djellal"],
    "Beni Abbes": ["Beni Abbes", "Béni Abbès", "52-Beni Abbes"],
    "In Salah": ["In Salah", "In Salah", "53-In Salah"],
    "In Guezzam": ["In Guezzam", "In Guezzam", "54-In Guezzam","in guzzamj","in guzzam"],
    "Touggourt": ["Touggourt", "Touggourt", "55-Touggourt"],
    "Djanet": ["Djanet", "Djanet", "56-Djanet"],
    "El Mghair": ["El Mghair", "El M'ghaier", "57-El Mghair","el m' ghaier"],
    "El Meniaa": ["El Meniaa", "EL-MENIAA", "58-El Meniaa","el mianiaa"],
    "France": ["France", "France", "59-France","aubenas","la savoie","lyon","sant itienne"],
    "Libya": ["Libya", "Libye", "60-Libya","ghat"],
    "Tunis": ["Tunis", "Tunisia", "61-Tunis","ben arous","hammam lif","tunisie"],
    "Cameroun": ["Cameroun", "Cameroun", "62-Cameroun"],
    "Bamako": ["Bamako", "Bamako", "63-Bamako"],
    "China":["china","chine","china"],
    "korea":["korea"],
    "serbia":["serbia"],
    "spain":["spain"],
    "swiss":["swiss"],
    "yemen":["yemen"]



}

def wilya(Data, Wilaya , column1,column2):
    # Nettoyage du dictionnaire : conversion en minuscules et suppression des tirets
    w_dict = {wilaya.lower().replace("-", " "): i+1 for i, (wilaya, variants) in enumerate(Wilaya.items())}
    for key, values in Wilaya.items():
        for variant in values:
            w_dict[variant.lower().replace("-", " ")] = w_dict[key.lower().replace("-", " ")]
    # Fonction de transformation
    def get_index(wilaya):
        wilaya = str(wilaya).lower().replace("-", " ")  # Normalisation
        return w_dict.get(wilaya, wilaya)  # Retourne l'index ou la valeur inchangée
    # Ajouter la transformation sur toute la colonne
    Data.insert(loc=7,column= column2, value=Data[column1].apply(get_index))
    return Data

def Stand_Wilaya(D):
    D=wilya(D,Wilaya,"subscriber_wialya","code_sub_wilaya")
    D=wilya(D, Wilaya, "pdv_wilaya", "code_pdv_wilaya")
    return D





def traite_vide(Data, column):
    # Convertir la colonne en type str pour éviter les erreurs de type
    Data[column] = Data[column].astype(str)

    # Remplacer les valeurs "0" et "?" par NaN
    Data[column] = Data[column].replace(["0", "?","UNKNOWN"], np.nan)

    # Supprimer les lignes où la colonne contient NaN
    Data = Data.dropna(subset=[column])

    return Data


def clean(Data):
    if Data is None:
        print("⚠️ Données d'entrée vides !")
        return pd.DataFrame()

    Data = Data.drop_duplicates()
    for column in Data.columns:
        Data = traite_vide(Data, column)
    return Data


def cree_R(path, nomR):
    """Crée un répertoire s'il n'existe pas."""
    os.makedirs(f"{path}/{nomR}", exist_ok=True)

def cree_F(path, data, nomData):
    """Crée ou met à jour un fichier Excel."""
    data.to_excel(f"{path}/{nomData}", index=False)



def fusionner_analyses_journalieres(cR, date_str):
    """Fusionne les analyses de phase d'un jour donné."""
    phases = ["Night", "Morning", "Afternoon", "Evening"]
    fichiers = [f"{cR}/DataDays/pdv_Days/{date_str}/Analyse_{date_str}_{phase}.xlsx" for phase in phases]

    dfs = [DataManager.charger_data(f) for f in fichiers if os.path.exists(f)]
    dfs = [df for df in dfs if df is not None and not df.empty]

    if not dfs:
        print(f"❌ Aucune donnée valide pour {date_str}.")
        return
    analyse_journaliere = pd.concat(dfs, ignore_index=True)
    cree_F(f"{cR}/DataDays/pdv_Days/{date_str}", analyse_journaliere, f"Analyse_{date_str}.xlsx")

def fusionner_analyses_globales(cR):
    """
    Fusionne toutes les analyses journalières en un seul fichier 'Analyse_Phases.xlsx'
    sans écraser les anciennes lignes.
    """
    dossier_pdv = f"{cR}/DataDays/pdv_Days"

    fichiers = [os.path.join(root, file) for root, _, files in os.walk(dossier_pdv)
                for file in files if file.startswith("Analyse_") and file.endswith(".xlsx")]

    print(f"📂 Fichiers trouvés pour fusion globale : {fichiers}")

    dfs = [DataManager.charger_data(f) for f in fichiers if os.path.exists(f)]
    dfs = [df for df in dfs if df is not None and not df.empty]

    if not dfs:
        print("❌ Aucune analyse journalière valide.")
        return

    analyse_totale = pd.concat(dfs, ignore_index=True)

    print(f"✅ Fusion réussie, {analyse_totale.shape[0]} lignes dans Analyse_Phases.xlsx")

    # Sauvegarde du fichier fusionné
    cree_F(f"{cR}/DataDays", analyse_totale, "Analyse_Phases.xlsx")
    print("✅ Analyse globale enregistrée : Analyse_Phases.xlsx")

def supprimer_colonne(df, nom_colonne):

    if nom_colonne in df.columns:
        df = df.drop(columns=[nom_colonne])
        print(f"✅ Colonne '{nom_colonne}' supprimée.")
    else:
        print(f"❌ Colonne '{nom_colonne}' non trouvée.")
    return df