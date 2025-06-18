
from .Analyse import *
from .Util import *




def App_1(cR,cD):
    # _______________________________ Initialisation des dossiers _______________________________
    print("App_1 DÉMARRÉ avec cR =", cR, "et cD =", cD)

    cree_R(cR, "DataDays")
    cree_R(cR, "Resultat")
    cree_R(f"{cR}/DataDays", "pdv_Days")
    cree_R(f"{cR}/DataDays", "sub_Days")
    cree_R(f"{cR}/DataDays/sub_Days", "Data")  # ← dossier pour les Data découpées
    cree_R(f"{cR}/DataDays/sub_Days", "Analyse")  # ← dossier pour les Analyses

    manager = DataManager(cD)
    D = manager.get_data()
    D = supprimer_colonne(D, "first_cdr_wilaya")
    D = Stand_Wilaya(D)
    D = D.dropna(subset=["activation_date"])
    D = clean(D)
    DataManager.enregistrer_data(D, rf"{cR}\Data0.xlsx")
    print("Pretretement enrgistre ")
    manager = DataManager(rf"{cR}/Data0.xlsx")
    D = manager.get_data()
    A = pd.to_datetime(D["activation_date"], dayfirst=False, errors="coerce").dropna().dt.normalize().unique()

    # ________________________________________________diviser par jour pour pdv _____________________________
    for date in A:
        date_str = date.strftime("%Y-%m-%d")
        cree_R(f"{cR}/DataDays/pdv_Days", date_str)

    for date in A:
        date_str = date.strftime("%Y-%m-%d")
        cree_F(f"{cR}/DataDays/pdv_Days/{date_str}", manager.Div_Data_Day(date), f"Data_{date_str}.xlsx")

        manager1 = DataManager(f"{cR}/DataDays/pdv_Days/{date_str}/Data_{date_str}.xlsx")
        D1 = manager1.get_data()

        # ________________________________________________diviser par phase pour pdv _____________________________
        for phase in ["Night", "Morning", "Afternoon", "Evening"]:
            cree_F(f"{cR}/DataDays/pdv_Days/{date_str}", manager1.Div_Data_phase(D1, phase),
                   f"Data_{date_str}_{phase}.xlsx")
    # _____________________________ Input : nombre de jours _____________________________
    # Nb_jour = int(input("Entrez le nombre de jours par tranche : "))
    Nb_jour = 22
    # _____________________________ Préparation des données _____________________________
    print(f"\n📆 Découpage de la data par tranches de {Nb_jour} jours...\n")

    D["activation_date"] = pd.to_datetime(D["activation_date"], dayfirst=False, errors="coerce")

    print("\n📊 Vérification des dates disponibles dans les données :")
    print(D["activation_date"].min(), "→", D["activation_date"].max())

    print("\n📆 Répartition des lignes par date :")
    print(D["activation_date"].dt.date.value_counts().sort_index())

    # _____________________________ Découpage par tranches dynamiques _____________________________
    df_tranches = manager.diviser_par_tranches(nb_jours=Nb_jour)

    # _____________________________ Génération et export des fichiers _____________________________
    for tranche_id in df_tranches["tranche_jours"].unique():
        df_tranche = df_tranches[df_tranches["tranche_jours"] == tranche_id]

        date_debut = df_tranche["activation_date"].min().date()
        date_fin = df_tranche["activation_date"].max().date()

        tranche_str = f"{date_debut.strftime('%Y-%m-%d')}_to_{date_fin.strftime('%Y-%m-%d')}"
        cree_F(f"{cR}/DataDays/sub_Days/Data", df_tranche, f"Data_{tranche_str}.xlsx")
        print(f"✅ Fichier sauvegardé : Data_{tranche_str}.xlsx")

    # _______________________________ Début de l'Analyse pdv phase _______________________________
    print("\n🔍 Début de l'analyse des phases pdv ...\n")

    analyseur = AnalyseurPDV()    # Initialisation de l'analyseur avec mémoire

    for date in A:
        date_str = date.strftime("%Y-%m-%d")

        # Chargement des données du jour complet
        DA = DataManager.charger_data(f"{cR}/DataDays/pdv_Days/{date_str}/Data_{date_str}.xlsx")

        if DA is None or DA.empty:
            print(f"❌ Données vides pour {date_str}. Analyse annulée.")
            continue

        print(f"✅ Données chargées pour {date_str} : {DA.shape[0]} lignes")

        # Analyse par phase
        for phase in ["Night", "Morning", "Afternoon", "Evening"]:
            DA_phase = DataManager.charger_data(f"{cR}/DataDays/pdv_Days/{date_str}/Data_{date_str}_{phase}.xlsx")

            if DA_phase is None or DA_phase.empty:
                print(f"⚠️ Données absentes pour la phase {phase} ({date_str}).")
                continue

            R_phase = analyseur.analyser(DA_phase)
            cree_F(f"{cR}/DataDays/pdv_Days/{date_str}", R_phase, f"Analyse_{date_str}_{phase}.xlsx")

    # _______________________________ Fusion des analyses pvd phase _______________________________
    print("\n🔄 Fusion des analyses de phase pour chaque jour...\n")
    for date in A:
        date_str = date.strftime("%Y-%m-%d")
        fusionner_analyses_journalieres(cR, date_str)

    print("\n🔄 Fusion des analyses globales...\n")
    fusionner_analyses_globales(cR)

    print("✅ Toutes les analyses de phases ont été fusionnées avec succès.")

    # _____________________________________ Analyse sub tranches de n jours _______________________________________
    print(f"\n🔍 Début de l'analyse des périodes sub (tranches de {Nb_jour} jours) ...\n")

    sub_days_dir = f"{cR}/DataDays/sub_Days/Data"
    fichiers_sub = [f for f in os.listdir(sub_days_dir) if f.startswith("Data_") and f.endswith(".xlsx")]

    for fichier in fichiers_sub:
        chemin_fichier = os.path.join(sub_days_dir, fichier)
        DA = DataManager.charger_data(chemin_fichier)

        if DA is None or DA.empty:
            print(f"❌ Données vides pour {fichier}. Analyse annulée.")
            continue

        print(f"✅ Données chargées pour {fichier} : {DA.shape[0]} lignes")

        # Analyse principale
        R = A_sub(DA)

        # Extraire la période depuis le nom du fichier
        nom_base = fichier.replace("Data_", "").replace(".xlsx", "")
        output_dir = f"{cR}/DataDays/sub_Days/Analyse"

        cree_F(output_dir, R, f"Analyse_{nom_base}.xlsx")
        print(f"✅ Analyse sauvegardée : Analyse_{nom_base}.xlsx")
    # ___________________Fusion des analyse Sub _________________________________________________
    print("\\n🔄 Fusion finale des analyses sub...")
    sub_days_dir = f"{cR}/DataDays/sub_Days/Analyse"

    fichiers_sub = [f for f in os.listdir(sub_days_dir) if f.startswith("Analyse_") and f.endswith(".xlsx")]
    dfs = [DataManager.charger_data(os.path.join(sub_days_dir, f)) for f in fichiers_sub]
    dfs = [df for df in dfs if df is not None and not df.empty]

    if not dfs:
        print("❌ Aucune analyse sub valide à fusionner.")
    else:
        fusion_sub = pd.concat(dfs, ignore_index=True)
        cree_F(f"{cR}/DataDays/sub_Days", fusion_sub, "Analyse_sub_globale.xlsx")
        print(f"✅ Fusion réussie : {fusion_sub.shape[0]} lignes fusionnées dans Analyse_sub_globale.xlsx")

    return cR