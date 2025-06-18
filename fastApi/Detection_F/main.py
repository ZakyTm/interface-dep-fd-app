import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import shutil
import numpy as np
from IA_Detction.main_Final import main as ia_main

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = "./IA_Resultat"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.post("/analyse")
async def analyse(
    file: UploadFile = File(...),
    model: str = Form(...),
    use_advanced: bool = Form(False),
    max_fraud_rate: Optional[float] = Form(None),
    min_fraud_rate: Optional[float] = Form(None),
    grid_size: Optional[float] = Form(None)
):
    file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    params = {}
    if use_advanced:
        if model in ["kmeans", "grid-kmeans"]:
            if max_fraud_rate is not None:
                params["max_fraud_rate"] = max_fraud_rate
            if min_fraud_rate is not None:
                params["min_fraud_rate"] = min_fraud_rate
        if model == "grid-kmeans" and grid_size is not None:
            params["grid_size"] = grid_size
    try:
        result = ia_main(
            file_location,
            UPLOAD_DIRECTORY,
            model=model,
            **params
        )
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    return {
        "status": "ok",
        "input_filename": file.filename,
        "model": model,
        "used_advanced": use_advanced,
        "advanced_params": params if use_advanced else {},
        "result": result
    }

# ---- Helper ----
def get_excel_path(model, actor):
    return os.path.join("IA_Resultat", "Resultat", model, actor + ".xlsx")

PDV_STAT_KEYS = [
    "nb_ventes", "moy_nb_vente", "delai_moyen_activations",
    "pct_ventes_wilaya", "pdv_unique_clients", "ratio_clients_uniques", "pct_new_subs",
    "var", "nb_bursts_360s"
]
SUB_STAT_KEYS = [
    "subscriber_id_number", "nb_sim", "delai_moyen_jours", "delai_total_jours",
    "nb_wilayas_distinctes", "ecart_type_jours", "nb_pdvs_distincts",
    "nb_code_sub_wilaya_distincts", "nb_cas_wilaya_diff", "nb_wilayas_pdv_sub_distinctes"
]

@app.get("/api/all-motifs")
def get_all_motifs(
    model: str = Query(...),
    actor: str = Query(...)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        col = "Variable_responsable" if "Variable_responsable" in df.columns else None
        motifs = df[col].dropna().astype(str).unique().tolist() if col else []
        return {"status": "ok", "motifs": motifs}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/all-dates")
def get_all_dates(
    model: str = Query(...),
    actor: str = Query(...)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        for col in ["date_debut_analyse", "date_fin_analyse"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
        dates = []
        if "date_debut_analyse" in df.columns:
            dates += df["date_debut_analyse"].dropna().tolist()
        if "date_fin_analyse" in df.columns:
            dates += df["date_fin_analyse"].dropna().tolist()
        dates = sorted(set(dates))
        return {"status": "ok", "dates": dates}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/all-timephases")
def get_all_timephases(
    model: str = Query(...),
    actor: str = Query(...)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        col = "time_phase"
        phases = df[col].dropna().astype(str).unique().tolist() if col in df.columns else []
        return {"status": "ok", "time_phases": phases}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/all-wilayas")
def get_all_wilayas(
    model: str = Query(...),
    actor: str = Query(...)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        col = "wilaya"
        wilayas = df[col].dropna().astype(str).unique().tolist() if col in df.columns else []
        return {"status": "ok", "wilayas": wilayas}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/top-fraud")
def get_top_fraud(
    model: str = Query(...),
    actor: str = Query(...),  # "A_pdv_Fraud" ou "A_sub_Fraud"
    motif: Optional[str] = Query(None),
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None),
    time_phase: Optional[str] = Query(None),
    wilaya: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        # Standardise colonnes
        if actor == "A_pdv_Fraud":
            id_col = "pdv_id"
            motif_col = "Variable_responsable"
            score_col = "Score_anomalie"
            df = df.rename(columns={id_col: "ID"})
            df["Score"] = df[score_col] if score_col in df.columns else None
            df["Motif"] = df[motif_col] if motif_col in df.columns else None
            if "wilaya" in df.columns:
                df["Wilaya"] = df["wilaya"].astype(str)
            if "time_phase" in df.columns:
                df["TimePhase"] = df["time_phase"]
        else:  # A_sub_Fraud
            id_col = "subscriber_id_number"
            motif_col = "Variable_responsable"
            score_col = "Score_anomalie"
            df = df.rename(columns={id_col: "ID"})
            df["Score"] = df[score_col] if score_col in df.columns else None
            df["Motif"] = df[motif_col] if motif_col in df.columns else None

        if "date_debut_analyse" in df.columns:
            df["DateDebut"] = pd.to_datetime(df["date_debut_analyse"]).dt.strftime("%Y-%m-%d")
        if "date_fin_analyse" in df.columns:
            df["DateFin"] = pd.to_datetime(df["date_fin_analyse"]).dt.strftime("%Y-%m-%d")

        # Filtres communs
        if "Anomalie" in df.columns:
            df = df[df["Anomalie"] == 1]
        if motif and motif_col in df.columns:
            df = df[df[motif_col] == motif]
        if date_debut and "DateDebut" in df.columns:
            df = df[df["DateDebut"] >= date_debut]
        if date_fin and "DateFin" in df.columns:
            df = df[df["DateFin"] <= date_fin]
        if time_phase and "TimePhase" in df.columns:
            df = df[df["TimePhase"] == time_phase]
        if wilaya and "Wilaya" in df.columns:
            df = df[df["Wilaya"] == str(wilaya)]
        if search:
            search_lower = search.lower()
            df = df[
                df.apply(
                    lambda row: search_lower in str(row["ID"]).lower()
                                or (motif_col in row and search_lower in str(row[motif_col]).lower()),
                    axis=1,
                )
            ]
        if score_col in df.columns:
            df = df.sort_values(by=score_col, ascending=False)
        if len(df) > 15:
            df = df.head(15)
        df = df.replace([np.inf, -np.inf], np.nan).fillna('')

        if actor == "A_pdv_Fraud":
            base_cols = ["ID", "DateDebut", "DateFin", "Score", "Motif", "Wilaya", "TimePhase"]
        else:
            base_cols = ["ID", "DateDebut", "DateFin", "Score", "Motif"]
        records = df[[col for col in base_cols if col in df.columns]].to_dict(orient="records")
        return {"status": "ok", "rows": records}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/fraud-stats")
def get_fraud_stats(
    model: str = Query(...),
    actor: str = Query(...),
    motif: Optional[str] = Query(None),
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None),
    time_phase: Optional[str] = Query(None),
    wilaya: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        if actor == "A_pdv_Fraud":
            id_col = "pdv_id"
            motif_col = "Variable_responsable"
        else:
            id_col = "subscriber_id_number"
            motif_col = "Variable_responsable"
        df = df.rename(columns={id_col: "ID"})
        if "wilaya" in df.columns:
            df["Wilaya"] = df["wilaya"].astype(str)
        if "Anomalie" in df.columns:
            df = df[df["Anomalie"] == 1]
        if motif and motif_col in df.columns:
            df = df[df[motif_col] == motif]
        if date_debut and "date_debut_analyse" in df.columns:
            df = df[df["date_debut_analyse"] >= date_debut]
        if date_fin and "date_fin_analyse" in df.columns:
            df = df[df["date_fin_analyse"] <= date_fin]
        if time_phase and "time_phase" in df.columns:
            df = df[df["time_phase"] == time_phase]
        if wilaya and "Wilaya" in df.columns:
            df = df[df["Wilaya"] == str(wilaya)]
        if search:
            search_lower = search.lower()
            df = df[
                df.apply(
                    lambda row: search_lower in str(row["ID"]).lower()
                                or (motif_col in row and search_lower in str(row[motif_col]).lower()),
                    axis=1,
                )
            ]
        total_anomalies = len(df)
        top_id = df["ID"].mode()[0] if ("ID" in df.columns and not df.empty) else "Aucun"
        top_wilaya = df["Wilaya"].mode()[0] if ("Wilaya" in df.columns and not df.empty) else "Aucune"
        top_motif = df[motif_col].mode()[0] if (motif_col in df.columns and not df.empty) else "Aucun"
        return {
            "status": "ok",
            "totalAnomalies": total_anomalies,
            "topPdv": top_id,
            "topWilaya": top_wilaya,
            "topMotif": top_motif
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/pdv-stats")
def get_stat_pdv(
    model: str = Query(...),
    pdv_id: str = Query(...),
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None),
    score: Optional[float] = Query(None),
    wilaya: Optional[str] = Query(None)
):
    excel_path = get_excel_path(model, "A_pdv_Fraud")
    if not os.path.exists(excel_path):
        return {}
    df = pd.read_excel(excel_path)
    stat_keys = PDV_STAT_KEYS
    if "date_debut_analyse" in df.columns:
        df["date_debut_analyse"] = pd.to_datetime(df["date_debut_analyse"]).dt.strftime("%Y-%m-%d")
    if "date_fin_analyse" in df.columns:
        df["date_fin_analyse"] = pd.to_datetime(df["date_fin_analyse"]).dt.strftime("%Y-%m-%d")
    if "wilaya" in df.columns:
        df["wilaya"] = df["wilaya"].astype(str)
    df["pdv_id"] = df["pdv_id"].astype(str).str.strip()
    sub_df = df[df["pdv_id"] == str(pdv_id).strip()]
    if wilaya and "wilaya" in df.columns:
        sub_df = sub_df[sub_df["wilaya"] == str(wilaya)]
    if date_debut and "date_debut_analyse" in df.columns:
        sub_df = sub_df[sub_df["date_debut_analyse"] == date_debut]
    if date_fin and "date_fin_analyse" in df.columns:
        sub_df = sub_df[sub_df["date_fin_analyse"] == date_fin]
    # <-- MODIF ICI: filtrage score uniquement si pas grid-kmeans
    if score is not None and "Score_anomalie" in df.columns and model != "grid-kmeans":
        sub_df = sub_df[np.isclose(sub_df["Score_anomalie"], float(score), atol=1e-6)]
    if sub_df.empty:
        return {k: "" for k in stat_keys}
    row = sub_df.iloc[0]
    stats = {}
    for k in stat_keys:
        val = row[k] if k in row else ""
        if pd.isnull(val):
            val = ""
        elif isinstance(val, (np.integer, np.int64, np.int32)):
            val = int(val)
        elif isinstance(val, (np.floating, np.float64, np.float32)):
            val = float(val)
        elif isinstance(val, (np.bool_)):
            val = bool(val)
        stats[k] = val
    return stats

@app.get("/api/sub-stats")
def get_stat_sub(
    model: str = Query(...),
    sub_id: str = Query(...),
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None),
    score: Optional[float] = Query(None)
):
    excel_path = get_excel_path(model, "A_sub_Fraud")
    if not os.path.exists(excel_path):
        return {}
    df = pd.read_excel(excel_path)
    stat_keys = SUB_STAT_KEYS
    if "date_debut_analyse" in df.columns:
        df["date_debut_analyse"] = pd.to_datetime(df["date_debut_analyse"]).dt.strftime("%Y-%m-%d")
    if "date_fin_analyse" in df.columns:
        df["date_fin_analyse"] = pd.to_datetime(df["date_fin_analyse"]).dt.strftime("%Y-%m-%d")
    df["subscriber_id_number"] = df["subscriber_id_number"].astype(str).str.strip()
    sub_df = df[df["subscriber_id_number"] == str(sub_id).strip()]
    if date_debut and "date_debut_analyse" in df.columns:
        sub_df = sub_df[sub_df["date_debut_analyse"] == date_debut]
    if date_fin and "date_fin_analyse" in df.columns:
        sub_df = sub_df[sub_df["date_fin_analyse"] == date_fin]
    # <-- MODIF ICI: filtrage score uniquement si pas grid-kmeans
    if score is not None and "Score_anomalie" in df.columns and model != "grid-kmeans":
        sub_df = sub_df[np.isclose(sub_df["Score_anomalie"], float(score), atol=1e-6)]
    if sub_df.empty:
        return {k: "" for k in stat_keys}
    row = sub_df.iloc[0]
    stats = {}
    for k in stat_keys:
        val = row[k] if k in row else ""
        if pd.isnull(val):
            val = ""
        elif isinstance(val, (np.integer, np.int64, np.int32)):
            val = int(val)
        elif isinstance(val, (np.floating, np.float64, np.float32)):
            val = float(val)
        elif isinstance(val, (np.bool_)):
            val = bool(val)
        stats[k] = val
    return stats


@app.get("/api/grid-sample")
def get_grid_sample(
    model: str = Query(...),
    actor: str = Query(...),
    exclude_ids: Optional[str] = Query(None)
):
    excel_path = get_excel_path(model, actor)
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    try:
        df = pd.read_excel(excel_path)
        id_col = "pdv_id" if actor == "A_pdv_Fraud" else "subscriber_id_number"
        df = df.rename(columns={id_col: "ID"})

        # Toujours renommer wilaya si présente
        if "wilaya" in df.columns:
            df = df.rename(columns={"wilaya": "Wilaya"})

        # Filtrage cluster -2 (pour grid-kmeans) et Anomalie = 1
        if "Cluster" in df.columns:
            df_grid = df[(df["Cluster"] == -2) & (df["Anomalie"] == 1)]
        else:
            df_grid = df[df["Anomalie"] == 1]

        # Colonnes à retourner
        base_cols = ["ID"]
        if "date_debut_analyse" in df_grid.columns:
            base_cols.append("date_debut_analyse")
        if "date_fin_analyse" in df_grid.columns:
            base_cols.append("date_fin_analyse")
        if "Wilaya" in df_grid.columns:
            base_cols.append("Wilaya")
        if "time_phase" in df_grid.columns:
            base_cols.append("time_phase")

        sample = df_grid.sample(n=min(10, len(df_grid)), random_state=42) if len(df_grid) > 0 else pd.DataFrame()
        records = sample[base_cols].replace([np.inf, -np.inf], '').fillna('').to_dict(orient="records")
        return {"status": "ok", "rows": records}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

from fastapi.responses import StreamingResponse
import io

@app.get("/api/export-grid-stats")
def export_grid_stats(model: str = Query(...), acteur: str = Query(...)):
    excel_path = get_excel_path(model, f"A_{acteur}_Fraud")
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    df = pd.read_excel(excel_path)
    if "Cluster" in df.columns:
        df = df[df["Cluster"] == -2]
    # Convert to CSV in memory
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, sep=";")
    buffer.seek(0)
    filename = f"stats_grid_{acteur}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export-grid-transactions")
def export_grid_transactions(model: str = Query(...), acteur: str = Query(...)):
    excel_path = get_excel_path(model, f"D_{acteur}_Fraud")
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    df = pd.read_excel(excel_path)
    if "Cluster" in df.columns:
        df = df[df["Cluster"] == -2]
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, sep=";")
    buffer.seek(0)
    filename = f"transactions_grid_{acteur}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

from fastapi.responses import StreamingResponse

@app.get("/api/export-individual-transactions")
def export_individual_transactions(
    model: str = Query(...),
    acteur: str = Query(...),
    id: str = Query(...),
    date_debut: str = Query(None),
    date_fin: str = Query(None),
    score: float = Query(None)
):
    # Fichier D_{acteur}_Fraud.xlsx
    excel_path = get_excel_path(model, f"D_{acteur}_Fraud")
    if not os.path.exists(excel_path):
        return {"status": "error", "detail": f"Fichier non trouvé: {excel_path}"}
    df = pd.read_excel(excel_path)

    # D'abord filtre Anomalie == 1 (si la colonne existe)
    if "Anomalie" in df.columns:
        df = df[df["Anomalie"] == 1]

    id_col = "pdv_id" if acteur == "pdv" else "subscriber_id_number"
    df[id_col] = df[id_col].astype(str).str.strip()
    filtered_df = df[df[id_col] == str(id).strip()]

    # Appliquer le filtre sur Cluster (s'il existe)
    if "Cluster" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Cluster"] == 2]

    # Filtrer par date début avec heure exacte si précisé
    if date_debut and "date_debut_analyse" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["date_debut_analyse"].astype(str) == str(date_debut)]
    if date_fin and "date_fin_analyse" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["date_fin_analyse"].astype(str) == str(date_fin)]
    # Filtrer par score
    if score is not None and "Score_anomalie" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Score_anomalie"].apply(
            lambda x: abs(float(x) - float(score)) < 1e-6 if pd.notnull(x) else False
        )]

    if filtered_df.empty:
        return {"status": "error", "detail": "Aucune transaction trouvée pour cet individu."}
    import io
    buffer = io.StringIO()
    filtered_df.to_csv(buffer, index=False, sep=";")
    buffer.seek(0)
    filename = f"transactions_{acteur}_{id}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
