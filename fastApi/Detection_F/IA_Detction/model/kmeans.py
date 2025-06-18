import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances
import matplotlib.pyplot as plt
import seaborn as sns


def K_means(cD, cR, k=3, max_attempts=1000,
            distribution_bounds=[(0.7, 0.85), (0.1, 0.15), (0.05, 0.1)]):
    """
    Applique l'algorithme KMeans pour identifier les anomalies et calculer l'impact des variables
    pour chaque ligne en fonction de leur influence dans la détection des anomalies.
    """
    print("🔹 Lancement du clustering KMeans")
    print("📂 Chargement du fichier :", cD)

    try:
        df = pd.read_excel(cD)
    except Exception as e:
        print(f"❌ Erreur de chargement : {e}")
        return None

    df = df.drop_duplicates().reset_index(drop=True)
    df_numeric = df.select_dtypes(include=[np.number]).copy()
    df_non_numeric = df.select_dtypes(exclude=[np.number]).copy()

    if df_numeric.empty:
        print("❌ Aucune colonne numérique détectée.")
        return None

    # Standardisation des données
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df_numeric)
    df_scaled_df = pd.DataFrame(df_scaled, columns=df_numeric.columns)

    best_result, best_kmeans = None, None

    # Tentatives de clustering
    for attempt in range(max_attempts):
        kmeans = KMeans(n_clusters=k, random_state=42 + attempt, n_init=10)
        clusters = kmeans.fit_predict(df_scaled_df)
        counts = pd.Series(clusters).value_counts(normalize=True).sort_values(ascending=False)

        if len(counts) == k and all(
                distribution_bounds[i][0] <= counts.iloc[i] <= distribution_bounds[i][1] for i in range(k)):
            print(f"✅ Distribution atteinte à la tentative {attempt + 1}")
            best_result = clusters
            best_kmeans = kmeans
            break

        if attempt == max_attempts - 1:
            print("⚠️ Distribution approximative retenue après toutes les tentatives.")
            best_result = clusters
            best_kmeans = kmeans

    # Mapping et détection des anomalies
    cluster_counts = pd.Series(best_result).value_counts().sort_values()
    cluster_mapping = {old: new for new, old in enumerate(cluster_counts.index[::-1])}
    mapped_clusters = pd.Series(best_result).map(cluster_mapping)
    anomaly_cluster = mapped_clusters.value_counts().idxmin()

    # Calcul des distances au centroïde (score d'anomalie)
    distances = pairwise_distances(df_scaled_df, best_kmeans.cluster_centers_)
    distance_scores = [distances[i][cluster] for i, cluster in enumerate(best_result)]

    # Création du DataFrame final avec données ORIGINALES
    df_final = pd.concat([df_non_numeric.reset_index(drop=True), df_numeric.reset_index(drop=True)], axis=1)
    df_final["Cluster"] = mapped_clusters
    df_final["Anomalie"] = df_final["Cluster"].apply(lambda x: 1 if x == anomaly_cluster else 0)
    df_final["Score_anomalie"] = distance_scores

    print(f"📊 Répartition des clusters :\n{df_final['Cluster'].value_counts(normalize=True)}")

    # Variables responsables et leur taux de contribution à l'anomalie
    df_scaled_with_clusters = df_scaled_df.copy()
    df_scaled_with_clusters["Cluster"] = mapped_clusters
    # Moyennes des clusters
    cluster_means = df_scaled_with_clusters.groupby("Cluster").mean(numeric_only=True)
    # Calcul de l'impact pour chaque ligne
    def calculate_responsible_variable_and_impact(row):
        cluster = row["Cluster"]
        if cluster == anomaly_cluster and cluster in cluster_means.index:
            diff = abs(row[df_numeric.columns] - cluster_means.loc[cluster])
            responsible_var = diff.idxmax()  # Variable avec le plus grand impact
            impact = diff[responsible_var]
            sum_diff = diff.sum()  # Somme des différences
            contribution_pct = (impact / sum_diff) * 100 if sum_diff > 0 else 0
            return responsible_var, contribution_pct
        else:
            return "N/A", 0
    responsible_info = df_final.apply(calculate_responsible_variable_and_impact, axis=1, result_type='expand')
    df_final["Variable_responsable"] = responsible_info[0]
    df_final["Taux_impact"] = responsible_info[1]

    # Centroïdes (non standardisés)
    centroids_orig = pd.DataFrame(scaler.inverse_transform(best_kmeans.cluster_centers_), columns=df_numeric.columns)
    centroids_orig["Cluster"] = centroids_orig.index.map(cluster_mapping)
    centroids_orig = centroids_orig.sort_values("Cluster").reset_index(drop=True)

    # Visualisation PCA
    output_dir = os.path.dirname(cR)
    base_name = os.path.basename(cD)
    df_pca = pd.DataFrame(PCA(n_components=2).fit_transform(df_scaled_df), columns=["PCA1", "PCA2"])
    df_pca["Cluster"] = mapped_clusters
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x="PCA1", y="PCA2", hue="Cluster", data=df_pca, palette="tab10", alpha=0.7)
    plt.title(f"Visualisation PCA KMeans - {base_name}")
    plt.tight_layout()
    img_path = os.path.join(output_dir, f"Visualisation_{os.path.splitext(base_name)[0]}.png")
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Export Excel complet
    try:
        with pd.ExcelWriter(cR, engine="xlsxwriter") as writer:
            df_final.to_excel(writer, sheet_name="Resultats", index=False)
            centroids_orig.to_excel(writer, sheet_name="Centroïdes", index=False)
        print(f"✅ Fichier Excel généré : {cR}")
    except Exception as e:
        print(f"❌ Erreur d'export Excel : {e}")

    return df_final
