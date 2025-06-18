import pandas as pd
import numpy as np
from collections import deque

Wilaya = {
    1: "Adrar", 2: "Chlef", 3: "Laghouat", 4: "Oum El Bouaghi", 5: "Batna", 6: "Bejaia",
    7: "Biskra", 8: "Bechar", 9: "Blida", 10: "Bouira", 11: "Tamanrasset", 12: "Tebessa",
    13: "Tlemcen", 14: "Tiaret", 15: "Tizi Ouzou", 16: "Alger", 17: "Djelfa", 18: "Jijel",
    19: "Setif", 20: "Saida", 21: "Skikda", 22: "Sidi Belabbes", 23: "Annaba", 24: "Guelma",
    25: "Constantine", 26: "Medea", 27: "Mostaganem", 28: "Msila", 29: "Mascara", 30: "Ouargla",
    31: "Oran", 32: "El Bayadh", 33: "Illizi", 34: "Bordj Bou Arreridj", 35: "Boumerdes",
    36: "El Taref", 37: "Tindouf", 38: "Tissemsilt", 39: "El Oued", 40: "Khenchela",
    41: "Souk Ahras", 42: "Tipaza", 43: "Mila", 44: "Ain Defla", 45: "Naama", 46: "Ain Temouchent",
    47: "Ghardaia", 48: "Relizane", 49: "Timimoun", 50: "Bordj Badji Mokhtar", 51: "Ouled Djellal",
    52: "Beni Abbes", 53: "In Salah", 54: "In Guezzam", 55: "Touggourt", 56: "Djanet",
    57: "El Mghair", 58: "El Meniaa", 59: "France", 60: "Libya", 61: "Tunis", 62: "Tunisia",
    63: "Cameroun", 64: "Bamako", 65:"China", 66:"korea", 67:"serbia", 68:"spain", 69:"swiss", 70:"yemen"
}

def parse_dates_safe(series):
    """Convertit en datetime en conservant les heures et minutes, avec dayfirst=True."""
    return pd.to_datetime(series, errors="coerce", dayfirst=True)

def calcul_pourcentage_ventes_wilaya(data):
    if "code_pdv_wilaya" not in data.columns or "nb_ventes" not in data.columns:
        print("Les colonnes nécessaires ne sont pas présentes dans le DataFrame.")
        return data
    data["wilaya"] = data["code_pdv_wilaya"].map(Wilaya)
    ventes_par_wilaya = data.groupby("wilaya")["nb_ventes"].sum().reset_index()
    ventes_par_wilaya.columns = ["wilaya", "total_ventes_wilaya"]
    data = data.merge(ventes_par_wilaya, on="wilaya", how="left")
    data["pct_ventes_wilaya"] = (data["nb_ventes"] / data["total_ventes_wilaya"]).fillna(0)
    data.drop(columns=["total_ventes_wilaya"], inplace=True)
    return data

def add_date_range_info(df, col_name="activation_date"):
    if col_name in df.columns:
        dates = pd.to_datetime(df[col_name], errors="coerce")
        valid_dates = dates.dropna()
        if not valid_dates.empty:
            df["date_debut_analyse"] = valid_dates.min()
            df["date_fin_analyse"] = valid_dates.max()
        else:
            df["date_debut_analyse"] = pd.NaT
            df["date_fin_analyse"] = pd.NaT
    else:
        df["date_debut_analyse"] = pd.NaT
        df["date_fin_analyse"] = pd.NaT
    return df

def detect_bursts(group, threshold_seconds=360, min_activations=5):
    timestamps = group["activation_ts"].tolist()
    window = deque()
    burst_count = 0
    for ts in timestamps:
        window.append(ts)
        while window and (ts - window[0]) > threshold_seconds:
            window.popleft()
        if len(window) >= min_activations:
            burst_count += 1
    return burst_count

class AnalyseurPDV:
    """
    Collecte de l'historique des abonnés déjà vus (subs_deja_vus)
    pour garantir un calcul juste de pct_new_subs à chaque appel d'analyse.
    """
    def __init__(self):
        self.subs_deja_vus = set()
    def analyser(self, Data):
        resultat = A_pdv(Data, subs_deja_vus=self.subs_deja_vus)
        if "subscriber_id_number" in Data.columns:
            nouveaux_subs = Data["subscriber_id_number"].dropna().unique()
            self.subs_deja_vus.update(nouveaux_subs)
        return resultat

def A_pdv(Data, subs_deja_vus=None):
    if "customer_type" in Data.columns:
        Data = Data[~Data["customer_type"].isin(["BUSINESS", "NON COMMERCIAL"])].copy()
    Data["activation_date"] = parse_dates_safe(Data["activation_date"])
    date_debut = Data["activation_date"].min()
    date_fin = Data["activation_date"].max()

    ventes_par_pdv = Data["pdv_id"].value_counts().reset_index()
    ventes_par_pdv.columns = ["pdv_id", "nb_ventes"]
    ventes_par_pdv["date_debut_analyse"] = date_debut
    ventes_par_pdv["date_fin_analyse"] = date_fin
    total_ventes = ventes_par_pdv["nb_ventes"].sum()
    ventes_par_pdv["moy_nb_vente"] = ventes_par_pdv["nb_ventes"] / total_ventes

    if "time_phase" in Data.columns:
        ventes_par_pdv = ventes_par_pdv.merge(
            Data[["pdv_id", "time_phase"]].drop_duplicates(),
            on="pdv_id", how="left"
        )
        phase_mapping = {"Night": 1, "Morning": 2, "Afternoon": 3, "Evening": 4}
        ventes_par_pdv["code_phase"] = ventes_par_pdv["time_phase"].map(phase_mapping).fillna(-1).astype(int)
    else:
        ventes_par_pdv["time_phase"] = "Unknown"
        ventes_par_pdv["code_phase"] = -1

    if "code_pdv_wilaya" in Data.columns:
        Data["code_pdv_wilaya"] = pd.to_numeric(Data["code_pdv_wilaya"], errors="coerce").fillna(0).astype(int)
        Data["wilaya"] = Data["code_pdv_wilaya"].map(Wilaya)
        wilaya_count = Data.groupby(["pdv_id", "wilaya"]).size().reset_index(name="ventes_wilaya")
        max_wilaya = wilaya_count.groupby("pdv_id")["ventes_wilaya"].max().reset_index(name="max_ventes_wilaya")
        ventes_par_pdv = ventes_par_pdv.merge(max_wilaya, on="pdv_id", how="left")
        ventes_par_pdv["ratio_wilaya"] = ventes_par_pdv["max_ventes_wilaya"] / ventes_par_pdv["nb_ventes"]
        nb_wilayas = Data.groupby("pdv_id")["wilaya"].nunique().reset_index(name="nb_wilayas_diff")
        nb_wilayas["multi_wilaya"] = (nb_wilayas["nb_wilayas_diff"] > 1).astype(int)
        ventes_par_pdv = ventes_par_pdv.merge(
            Data[["pdv_id", "wilaya"]].drop_duplicates(),
            on="pdv_id", how="left"
        ).merge(nb_wilayas[["pdv_id", "multi_wilaya"]], on="pdv_id", how="left")

    if "code_pdv_wilaya" in Data.columns:
        Data["code_pdv_wilaya"] = pd.to_numeric(Data["code_pdv_wilaya"], errors="coerce").fillna(0).astype(int)
        Data["wilaya"] = Data["code_pdv_wilaya"].map(Wilaya)
        code_wilaya_info = Data.groupby("pdv_id")[["code_pdv_wilaya", "wilaya"]].first().reset_index()
        ventes_par_pdv = ventes_par_pdv.merge(code_wilaya_info, on="pdv_id", how="left")
        ventes_par_pdv = calcul_pourcentage_ventes_wilaya(ventes_par_pdv)

    if "subscriber_id_number" in Data.columns:
        unique_subs = Data.groupby("pdv_id")["subscriber_id_number"].nunique().reset_index(name="pdv_unique_clients")
        ventes_par_pdv = ventes_par_pdv.merge(unique_subs, on="pdv_id", how="left")
    else:
        ventes_par_pdv["pdv_unique_clients"] = None

    ventes_par_pdv["ratio_clients_uniques"] = ventes_par_pdv["pdv_unique_clients"] / ventes_par_pdv["nb_ventes"]

    # --- Correction du calcul pct_new_subs ---
    if subs_deja_vus is not None and "subscriber_id_number" in Data.columns:
        Data["is_new_sub"] = ~Data["subscriber_id_number"].isin(subs_deja_vus)
        pct_new = Data.groupby("pdv_id")["is_new_sub"].mean().reset_index(name="pct_new_subs")
        ventes_par_pdv = ventes_par_pdv.merge(pct_new, on="pdv_id", how="left")
    else:
        ventes_par_pdv["pct_new_subs"] = 0.0  # Si historique inconnu, valeur neutre

    # Correction NaN/type sur pct_new_subs (obligatoire pour pipeline ML)
    if "pct_new_subs" in ventes_par_pdv.columns:
        ventes_par_pdv["pct_new_subs"] = ventes_par_pdv["pct_new_subs"].fillna(0).astype(float)
    # --- Fin correction pct_new_subs ---

    # --- Partie bursts ---
    Data["activation_ts"] = Data["activation_date"].astype("int64") // 10**9
    Data = Data.sort_values(by=["pdv_id", "activation_ts"])
    burst_list = []
    for pdv_id, group in Data.groupby("pdv_id"):
        nb_bursts = detect_bursts(group, 360, 5)
        burst_list.append({"pdv_id": pdv_id, "nb_bursts_360s": nb_bursts})
    bursts = pd.DataFrame(burst_list)
    ventes_par_pdv = ventes_par_pdv.merge(bursts, on="pdv_id", how="left")

    Data = Data.sort_values(by=["pdv_id", "activation_date"])
    Data["delta_t"] = Data.groupby("pdv_id")["activation_date"].diff().dt.total_seconds()

    var_temp = (
        Data.groupby("pdv_id")["delta_t"]
        .var()
        .fillna(0)
        .div(3600)
        .reset_index(name="var")
    )
    ventes_par_pdv = ventes_par_pdv.merge(var_temp, on="pdv_id", how="left")

    moy_temp = (
        Data.groupby("pdv_id")["delta_t"]
        .mean()
        .fillna(0)
        .div(3600)
        .reset_index(name="delai_moyen_activations")
    )
    ventes_par_pdv = ventes_par_pdv.merge(moy_temp, on="pdv_id", how="left")

    colonnes_finales = [
        "pdv_id", "nb_ventes", "moy_nb_vente", "time_phase", "code_phase",
        "wilaya", "pct_ventes_wilaya", "pdv_unique_clients", "ratio_clients_uniques",
        "pct_new_subs", "nb_bursts_360s", "var", "delai_moyen_activations",
        "date_debut_analyse", "date_fin_analyse"
    ]
    ventes_par_pdv = ventes_par_pdv.drop_duplicates().reset_index(drop=True)

    # Correction universelle de toutes les colonnes numériques pour KMeans & Co
    num_cols = ventes_par_pdv.select_dtypes(include=['number']).columns
    ventes_par_pdv[num_cols] = ventes_par_pdv[num_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

    return ventes_par_pdv[[col for col in colonnes_finales if col in ventes_par_pdv.columns]]


def A_sub(Data):
    Data.columns = Data.columns.str.strip()
    colonnes_requises = ["subscriber_id_number", "activation_date", "code_sub_wilaya"]
    for col in colonnes_requises:
        if col not in Data.columns:
            print(f"❌ Colonne manquante : {col}")
            return pd.DataFrame()
    Data = Data.copy()
    Data["activation_date"] = parse_dates_safe(Data["activation_date"])
    Data = Data.dropna(subset=["activation_date"])
    if "customer_type" in Data.columns:
        Data = Data[~Data["customer_type"].isin(["BUSINESS", "NON COMMERCIAL"])].copy()
    achat_par_s = Data["subscriber_id_number"].value_counts().reset_index()
    achat_par_s.columns = ["subscriber_id_number", "nb_sim"]
    multi_sim_clients = achat_par_s[achat_par_s["nb_sim"] > 1]
    D_multi = Data.merge(multi_sim_clients, on="subscriber_id_number", how="inner")
    delais_moyens = (
        D_multi.sort_values(["subscriber_id_number", "activation_date"])
        .groupby("subscriber_id_number")["activation_date"]
        .apply(lambda x: x.diff().dropna().dt.total_seconds().mean() / (60 * 60 * 24))
        .reset_index(name="delai_moyen_jours")
    )
    delai_total = (
        D_multi.groupby("subscriber_id_number")["activation_date"]
        .agg(lambda x: (x.max() - x.min()).days)
        .reset_index(name="delai_total_jours")
    )
    nb_wilayas_diff = (
        D_multi.groupby("subscriber_id_number")["code_pdv_wilaya"]
        .nunique()
        .reset_index(name="nb_wilayas_distinctes")
    )
    ecart_type_jours = (
        D_multi.groupby("subscriber_id_number")["activation_date"]
        .agg(lambda x: x.std().total_seconds() / (60 * 60 * 24) if len(x) > 1 else 0)
        .reset_index(name="ecart_type_jours")
    )
    nb_pdvs = (
        D_multi.groupby("subscriber_id_number")["pdv_id"]
        .nunique()
        .reset_index(name="nb_pdvs_distincts")
    ) if "pdv_id" in D_multi.columns else pd.DataFrame()
    nb_wilayas_subs = nb_cas_wilaya_diff = nb_wilayas_total = pd.DataFrame()
    if "code_sub_wilaya" in D_multi.columns:
        sub_info = D_multi[["subscriber_id_number", "code_sub_wilaya"]].drop_duplicates()
        nb_wilayas_subs = (
            sub_info.groupby("subscriber_id_number")["code_sub_wilaya"]
            .nunique()
            .reset_index(name="nb_code_sub_wilaya_distincts")
        )
        D_multi["pdv_vs_sub_diff"] = D_multi["code_pdv_wilaya"] != D_multi["code_sub_wilaya"]
        nb_cas_wilaya_diff = (
            D_multi.groupby("subscriber_id_number")["pdv_vs_sub_diff"]
            .sum()
            .reset_index(name="nb_cas_wilaya_diff")
        )
        total_wilayas = D_multi[["subscriber_id_number", "code_pdv_wilaya", "code_sub_wilaya"]].melt(
            id_vars="subscriber_id_number", value_name="wilaya"
        )
        nb_wilayas_total = (
            total_wilayas.groupby("subscriber_id_number")["wilaya"]
            .nunique()
            .reset_index(name="nb_wilayas_pdv_sub_distinctes")
        )
    first_date = (
        D_multi.groupby("subscriber_id_number")["activation_date"]
        .min()
        .reset_index(name="activation_date")
    )
    result = multi_sim_clients \
        .merge(delais_moyens, on="subscriber_id_number", how="left") \
        .merge(delai_total, on="subscriber_id_number", how="left") \
        .merge(nb_wilayas_diff, on="subscriber_id_number", how="left") \
        .merge(ecart_type_jours, on="subscriber_id_number", how="left") \
        .merge(first_date, on="subscriber_id_number", how="left")
    if not nb_pdvs.empty:
        result = result.merge(nb_pdvs, on="subscriber_id_number", how="left")
    if not nb_wilayas_subs.empty:
        result = result.merge(nb_wilayas_subs, on="subscriber_id_number", how="left")
    if not nb_cas_wilaya_diff.empty:
        result = result.merge(nb_cas_wilaya_diff, on="subscriber_id_number", how="left")
    if not nb_wilayas_total.empty:
        result = result.merge(nb_wilayas_total, on="subscriber_id_number", how="left")
    return add_date_range_info(result)