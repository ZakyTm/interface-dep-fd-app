from datetime import datetime, time

import numpy as np
import pandas as pd

phases = {
    "Night": [time(0, 0, 0), time(5, 59, 59)],
    "Morning": [time(6, 0, 0), time(11, 59, 59)],
    "Afternoon": [time(12, 0, 0), time(17, 59, 59)],
    "Evening": [time(18, 0, 0), time(23, 59, 59)]
}

class DataManager:
    def __init__(self, fichier):
        self.Data = self.charger_data(fichier)

    @staticmethod
    def charger_data(fichier):
        try:
            return pd.read_excel(fichier)
        except Exception as e:
            print(f"Erreur lors du chargement du fichier : {e}")
            return None

    @staticmethod
    def enregistrer_data(data, fichier):
        try:
            data.to_excel(fichier, index=False)
            print(f"Fichier enregistré : {fichier}")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement : {e}")

    def get_data(self):
        return self.Data

    def set_data(self, fichier="../Data/Data1.xlsx"):
        self.Data = self.charger_data(fichier)
        if self.Data is not None:
            print("✅ Récupération des données réussie")



    def Div_Data_Day(self, Day):
        print("On va diviser la data par rapport au jour")
        D = self.Data.copy()
        D["activation_date"] = pd.to_datetime(D["activation_date"],dayfirst=False,errors="coerce")
        mask = D["activation_date"].dt.date == Day.date()
        return D[mask]

    def diviser_par_tranches(self, nb_jours=22):
        df = self.Data.copy()
        df["activation_date"] = pd.to_datetime(df["activation_date"], dayfirst=False, errors="coerce")
        df = df.dropna(subset=["activation_date"])
        df = df.sort_values("activation_date")
        # Calcul de la date minimale et maximale
        min_date = df["activation_date"].min().normalize()
        max_date = df["activation_date"].max().normalize()
        # Calcule la différence en jours entre chaque 'activation_date' et la date minimale
        df["delta_jours"] = (df["activation_date"].dt.normalize() - min_date).dt.days
        # Calcule le numéro de tranche basé sur 'delta_jours'
        df["tranche_jours"] = df["delta_jours"] // nb_jours + 1
        # Optionnel : formatage des tranches en libellé, par exemple "J1 à J4"
        df["tranche_label"] = df["tranche_jours"].apply(
            lambda i: f"J{(i - 1) * nb_jours + 1} à J{i * nb_jours}"
        )
        # Suppression de la colonne 'delta_jours' qui n'est plus nécessaire
        df = df.drop(columns=["delta_jours"])

        return df

    @staticmethod
    def supprimer_doublons_msisdn(df):
        # Vérifie si df est None
        if df is None:
            raise ValueError("Le DataFrame passé en argument est None")

        # Vérifie si la colonne 'msisdn' existe dans df
        if 'msisdn' in df.columns:
            df = df.drop_duplicates(subset=['msisdn'])
            return df
        else:
            raise ValueError("'msisdn' n'est pas une colonne dans le DataFrame")

    @staticmethod
    def join_strict_PDV(D1, D2):
        D1 = D1.copy()
        D2 = D2.copy()

        # 🧼 Nettoyage des dates
        D1["activation_date"] = pd.to_datetime(D1["activation_date"], errors='coerce')
        D2["date_debut_analyse"] = pd.to_datetime(D2["date_debut_analyse"], errors='coerce')
        D2["date_fin_analyse"] = pd.to_datetime(D2["date_fin_analyse"], errors='coerce')

        # 🔍 Colonnes utiles uniquement dans D2
        D2 = D2[["pdv_id", "date_debut_analyse", "date_fin_analyse", "Cluster", "Anomalie", "Score_anomalie",
                 "Variable_responsable","Taux_impact"]]

        # ⛓️ Création d’une table élargie par produit cartésien sur pdv_id (pour tester les intervalles)
        merged = pd.merge(D1, D2, on="pdv_id", how="left")

        # 🕒 Pour chaque ligne, vérifier si activation_date ∈ [date_debut_analyse, date_fin_analyse]
        mask = (merged["activation_date"] >= merged["date_debut_analyse"]) & \
               (merged["activation_date"] <= merged["date_fin_analyse"])

        # 🎯 Conserver uniquement les correspondances valides (si multiples correspondances : plusieurs lignes)
        merged_valid = merged[mask].copy()

        # ✅ Si plusieurs correspondances, garder la première
        merged_valid = merged_valid.drop_duplicates(subset=["pdv_id", "activation_date"])

        # 🚫 Pour les lignes sans correspondance, on les retrouve via anti-jointure
        D1_keys = D1[["pdv_id", "activation_date"]].drop_duplicates()
        matched_keys = merged_valid[["pdv_id", "activation_date"]]
        unmatched = pd.merge(D1_keys, matched_keys, on=["pdv_id", "activation_date"], how="left", indicator=True)
        unmatched = unmatched[unmatched["_merge"] == "left_only"].drop(columns=["_merge"])

        # ⛔ Attribuer Cluster = -1 pour les enregistrements sans correspondance
        unmatched["Cluster"] = -1
        final = pd.concat([merged_valid[["pdv_id", "activation_date", "Cluster", "Anomalie", "Score_anomalie",
                                         "Variable_responsable","Taux_impact"]], unmatched], ignore_index=True)

        # 🔁 Fusion finale avec la data source (D1)
        D1 = D1.merge(final, on=["pdv_id", "activation_date"], how="left")
        D1["Cluster"] = D1["Cluster"].fillna(-1).astype(int)

        # L'Anomalie, Score_anomalie et Variable_responsable sont déjà ajoutées depuis D2, donc rien à ajouter ici

        return D1

    @staticmethod
    def join_strict_Sub(D1, D2):
        D1 = D1.copy()
        D2 = D2.copy()

        # 🔄 Conversion des dates
        D1["activation_date"] = pd.to_datetime(D1["activation_date"], errors='coerce')
        D2["date_debut_analyse"] = pd.to_datetime(D2["date_debut_analyse"], errors='coerce')
        D2["date_fin_analyse"] = pd.to_datetime(D2["date_fin_analyse"], errors='coerce')

        # 🧪 Colonnes utiles uniquement dans D2
        D2 = D2[
            ["subscriber_id_number", "date_debut_analyse", "date_fin_analyse", "Cluster", "Anomalie", "Score_anomalie",
             "Variable_responsable","Taux_impact"]]

        # 🔗 Jointure large
        merged = pd.merge(D1, D2, on="subscriber_id_number", how="left")

        # 📌 Marquer les correspondances valides
        mask = (merged["activation_date"] >= merged["date_debut_analyse"]) & \
               (merged["activation_date"] <= merged["date_fin_analyse"])
        merged_valid = merged[mask].copy()

        # 🧠 Pour chaque activation, on garde le premier Cluster valide (si plusieurs)
        merged_valid = merged_valid.drop_duplicates(subset=["subscriber_id_number", "activation_date"])

        # 🎯 Clés de jointure
        keys = ["subscriber_id_number", "activation_date"]

        # 🔍 Trouver les activations sans correspondance valide
        all_keys = D1[keys].drop_duplicates()
        matched_keys = merged_valid[keys]
        unmatched = pd.merge(all_keys, matched_keys, on=keys, how="left", indicator=True)
        unmatched = unmatched[unmatched["_merge"] == "left_only"].drop(columns=["_merge"])
        unmatched["Cluster"] = -1

        # 🔁 Fusion des valides + non appariés
        final = pd.concat(
            [merged_valid[keys + ["Cluster", "Anomalie", "Score_anomalie", "Variable_responsable","Taux_impact"]], unmatched],
            ignore_index=True)

        # 💡 Jointure finale avec la source
        D1 = D1.merge(final, on=keys, how="left")
        D1["Cluster"] = D1["Cluster"].fillna(-1).astype(int)

        # L'Anomalie, Score_anomalie et Variable_responsable sont déjà ajoutées depuis D2, donc rien à ajouter ici

        return D1

    @staticmethod
    def Div_Data_phase(data, phase):
        if data is None:
            print("⚠️ Erreur : les données fournies sont vides")
            return pd.DataFrame()

        print("On va diviser la data par rapport au moment de la journée")
        D = data.copy()
        D["activation_date"] = pd.to_datetime(D["activation_date"],dayfirst=True ,errors="coerce")
        if phase in phases:
            mask = D["activation_date"].dt.time.between(phases[phase][0], phases[phase][1])
            D_filtered = D[mask].copy()
            D_filtered["time_phase"] = phase
            return D_filtered
        else:
            print("⚠️ Phase invalide")
            return pd.DataFrame()

    def drop_col_no_pdv(self, data):
        col_names = ["activation_date", "pdv_id", "code_pdv_wilaya", "status"]
        data = data[col_names]
        return data
