import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances
import matplotlib.pyplot as plt
import seaborn as sns
import gc

def Grid_Hybride(cD, cR, k=3, max_attempts=1000, seuil_cell=4, grid_size=12.8,
                 distribution_bounds=[(0.7, 0.85), (0.1, 0.15), (0.05, 0.10)]):
    print("🔹 Application Grid_Hybride optimisée")
    print("📂 Chargement du fichier :", cD)

    try:
        df = pd.read_excel(cD, engine='openpyxl')
    except Exception as e:
        print(f"❌ Erreur de chargement : {e}")
        return None

    # 🔁 Supprimer les lignes dupliquées
    df = df.drop_duplicates().reset_index(drop=True)

    # Sélectionner les colonnes numériques et non numériques
    df_numeric = df.select_dtypes(include=[np.number]).copy()
    df_non_numeric = df.select_dtypes(exclude=[np.number]).copy()

    if df_numeric.empty:
        print("❌ Aucune colonne numérique trouvée.")
        return None

    # ⚖️ Standardisation (pour le calcul)
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df_numeric)
    df_scaled_df = pd.DataFrame(df_scaled, columns=df_numeric.columns)

    # Conserver pour remettre à la fin les vraies valeurs
    df_numeric_original = df_numeric.copy()

    del df_numeric
    gc.collect()

    # 🔲 Construction des coordonnées grille
    grid_coords = np.floor(df_scaled / grid_size).astype(int)
    df_grid = pd.DataFrame(grid_coords, columns=df_scaled_df.columns)
    df_grid["GridCluster"] = df_grid.astype(str).agg('_'.join, axis=1)

    # 🔍 Densité des cellules
    cell_counts = df_grid["GridCluster"].value_counts()
    # 🔁 Ajustement dynamique du seuil
    original_seuil_cell = seuil_cell
    min_inlier_ratio = 0.05
    while seuil_cell >= 1:
        df_grid["FilteredCluster"] = df_grid["GridCluster"].apply(lambda c: -2 if cell_counts[c] < seuil_cell else 0)
        inliers_mask = df_grid["FilteredCluster"] != -2
        inlier_ratio = inliers_mask.sum() / len(df_grid)
        if inlier_ratio >= min_inlier_ratio:
            break
        seuil_cell -= 1
    if inliers_mask.sum() == 0:
        print("⚠️ Aucun inlier détecté après ajustement. Sélection des 10 cellules les plus denses.")
        top_cells = cell_counts.head(10).index.tolist()
        df_grid["FilteredCluster"] = df_grid["GridCluster"].apply(lambda c: 0 if c in top_cells else -2)
        inliers_mask = df_grid["FilteredCluster"] != -2
    if seuil_cell != original_seuil_cell:
        print(f"⚙️ Seuil_cell ajusté dynamiquement de {original_seuil_cell} à {seuil_cell}")
    df_inliers_scaled = df_scaled_df.loc[inliers_mask].reset_index(drop=True)
    if df_inliers_scaled.empty:
        print("❌ Aucune donnée inlier disponible pour KMeans.")
        return None

    best_result, best_counts, best_kmeans = None, None, None

    for attempt in range(max_attempts):
        kmeans = KMeans(n_clusters=k, random_state=42 + attempt, n_init=10)
        clusters = kmeans.fit_predict(df_inliers_scaled)
        counts = pd.Series(clusters).value_counts(normalize=True).sort_values(ascending=False)

        if len(counts) == k:
            if all(distribution_bounds[i][0] <= counts.iloc[i] <= distribution_bounds[i][1] for i in range(k)):
                print(f"✅ Distribution atteinte à la tentative {attempt + 1}")
                best_result = clusters
                best_counts = counts
                best_kmeans = kmeans
                break

        if attempt == max_attempts - 1:
            print("⚠️ Distribution approximative retenue après toutes les tentatives.")
            best_result = clusters
            best_counts = counts
            best_kmeans = kmeans

    df_result = pd.concat([df_non_numeric.reset_index(drop=True), df_scaled_df.reset_index(drop=True)], axis=1)
    df_result["Cluster"] = -2

    inliers_index = df_result.loc[inliers_mask].index
    if best_result is not None:
        df_result.loc[inliers_index, "Cluster"] = best_result

    print(f"🚨 Outliers détectés (Grid = -2) : {(~inliers_mask).sum()}")
    print(f"🔢 Répartition des clusters (k={k}) :")
    if best_result is not None:
        print(pd.Series(best_result).value_counts())
    else:
        print("Aucun cluster KMeans formé.")

    # 📉 PCA
    pca = PCA(n_components=2)
    df_pca = pca.fit_transform(df_scaled_df)
    df_pca = pd.DataFrame(df_pca, columns=["PCA1", "PCA2"])
    df_pca["Cluster"] = df_result["Cluster"]
    df_pca = df_pca[df_pca["Cluster"] != -1]

    plt.figure(figsize=(8, 6))
    sns.scatterplot(x="PCA1", y="PCA2", hue="Cluster", data=df_pca, palette="tab10", alpha=0.7)
    base_name = os.path.basename(cD)
    plt.title(f"Visualisation PCA Grid+KMeans - {base_name}")
    plt.tight_layout()

    output_dir = os.path.dirname(cR)
    nom_img = f"Visualisation_{os.path.splitext(base_name)[0]}.png"
    plt.savefig(os.path.join(output_dir, nom_img), dpi=300, bbox_inches='tight')
    plt.close()

    # Anomalie = 1 pour les anomalies (Grid -2 ou Cluster 2)
    df_result["Anomalie"] = df_result["Cluster"].apply(lambda x: 1 if x == -2 or x == 2 else 0)

    # Calcul du score d'anomalie basé sur la distance au centroïde
    distance_scores = pd.Series(np.full(len(df_result), np.nan), index=df_result.index)
    if best_kmeans is not None and best_result is not None:
        distances = pairwise_distances(df_scaled_df.loc[inliers_mask], best_kmeans.cluster_centers_)
        distance_scores[inliers_index] = [distances[i][cluster] for i, cluster in enumerate(best_result)]

    # Ajouter le score d'anomalie pour chaque ligne
    df_result["Score_anomalie"] = distance_scores

    # Remettre les résultats dans leur forme originale (données non standardisées)
    df_result[df_numeric_original.columns] = scaler.inverse_transform(df_scaled_df)

    # =========================================
    #   NOUVELLE PARTIE : variable responsable LIGNE PAR LIGNE
    # =========================================
    # Ajoute le cluster au DataFrame standardisé
    df_temp = df_scaled_df.copy()
    df_temp['Cluster'] = df_result['Cluster']

    # Moyenne générale sur toutes les lignes (pour chaque variable)
    mean_all = df_scaled_df.mean(numeric_only=True)

    # Fonction qui compare chaque ligne aux moyennes générales (sur toutes les variables numériques)
    def find_responsable_and_impact(row):
        if row['Cluster'] == 2:  # adapte ici si ton cluster anomalie n'est pas 2
            diffs = abs(row[df_numeric_original.columns] - mean_all)
            responsable = diffs.idxmax()
            impact = (diffs[responsable] / diffs.sum()) * 100 if diffs.sum() > 0 else 0
            return responsable, impact
        else:
            return "Aucune", 0

    responsable_info = df_temp.apply(find_responsable_and_impact, axis=1, result_type='expand')
    df_result['Variable_responsable'] = responsable_info[0]
    df_result['Taux_impact'] = responsable_info[1]

    # =========================================

    # Export Excel complet
    try:
        df_result.to_excel(cR, index=False)
        print(f"✅ Résultat exporté dans : {cR}")
    except Exception as e:
        print(f"❌ Erreur à l'enregistrement : {e}")

    return df_result
