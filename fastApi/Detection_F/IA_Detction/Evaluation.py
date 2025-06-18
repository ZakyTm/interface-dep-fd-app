import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def compare_models(file_kmeans, file_grid, output_dir=None):
    # 📂 Vérification des fichiers
    for file in [file_kmeans, file_grid]:
        if not os.path.exists(file):
            print(f"❌ Fichier introuvable : {file}")
            return

    # 📥 Chargement des données
    df_kmeans = pd.read_excel(file_kmeans)
    df_grid = pd.read_excel(file_grid)

    df_kmeans = df_kmeans[df_kmeans["Cluster"] != -1].copy()
    df_grid = df_grid[df_grid["Cluster"] != -1].copy()

    df_kmeans["Modèle"] = "K-Means"
    df_grid["Modèle"] = "K-Means + Grid"

    # 🧩 Fusion des deux datasets
    df_all = pd.concat([df_kmeans, df_grid], ignore_index=True)

    # 🔍 Reclassification des types
    df_all["Type"] = "Normal"
    df_all.loc[df_all["Cluster"].isin([2, -2]), "Type"] = "Anomalie"

    # 📊 Statistiques globales
    stats = df_all.groupby(["Modèle", "Type"]).size().reset_index(name="Nombre")
    total = df_all.groupby("Modèle").size().reset_index(name="Total")
    stats = stats.merge(total, on="Modèle")
    stats["Taux (%)"] = (stats["Nombre"] / stats["Total"] * 100).round(2)

    # 📈 Visualisation
    plt.figure(figsize=(8, 5))
    sns.barplot(data=stats, x="Type", y="Taux (%)", hue="Modèle")
    plt.title("Taux (%) de cas détectés - Normal vs Anomalie")
    plt.tight_layout()

    suffix = os.path.splitext(os.path.basename(file_kmeans))[0].split("_")[1].lower() if "_" in file_kmeans else "comparison"

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        fig_name = f"Comparaison_{suffix}.png"
        plt.savefig(os.path.join(output_dir, fig_name), dpi=300)
        print(f"📸 Figure enregistrée : {fig_name}")

    # 🧮 Analyse des cas croisés
    id_col = df_kmeans.columns[0]
    set_kmeans = set(df_kmeans[df_kmeans["Cluster"].isin([2, -2])][id_col])
    set_grid = set(df_grid[df_grid["Cluster"].isin([2, -2])][id_col])

    commun = set_kmeans & set_grid
    unique_kmeans = set_kmeans - set_grid
    unique_grid = set_grid - set_kmeans
    all_anomalies = set_kmeans | set_grid

    stats_add = pd.DataFrame({
        "Modèle": ["Commun", "Unique K-Means", "Unique Grid"],
        "Type": ["Anomalie"] * 3,
        "Nombre": [len(commun), len(unique_kmeans), len(unique_grid)],
        "Total": [len(all_anomalies)] * 3,
        "Taux (%)": [
            round(len(commun) / len(all_anomalies) * 100, 2) if all_anomalies else 0,
            round(len(unique_kmeans) / len(all_anomalies) * 100, 2) if all_anomalies else 0,
            round(len(unique_grid) / len(all_anomalies) * 100, 2) if all_anomalies else 0,
        ]
    })

    stats = pd.concat([stats, stats_add], ignore_index=True)

    # 📊 Matrice de confusion simplifiée
    df_k = df_kmeans[[id_col, "Cluster"]].copy()
    df_g = df_grid[[id_col, "Cluster"]].copy()
    df_k["KM"] = df_k["Cluster"].apply(lambda x: "Anomalie" if x in [2, -2] else "Normal")
    df_g["GR"] = df_g["Cluster"].apply(lambda x: "Anomalie" if x in [2, -2] else "Normal")

    confusion_df = pd.merge(df_k[[id_col, "KM"]], df_g[[id_col, "GR"]], on=id_col, how="outer")
    confusion = confusion_df.groupby(["KM", "GR"]).size().unstack(fill_value=0)

    print("\n📊 Matrice de confusion simplifiée (K-Means vs Grid) :")
    print(confusion)

    # 📁 Export
    if output_dir:
        filename = f"Comparaison_Clusters_{suffix}.xlsx"
        path = os.path.join(output_dir, filename)
        with pd.ExcelWriter(path) as writer:
            stats.to_excel(writer, index=False, sheet_name="Résumé")
            confusion.to_excel(writer, sheet_name="Matrice de confusion")
        print(f"📁 Résumé exporté : {path}")
        return path

    return stats, confusion
