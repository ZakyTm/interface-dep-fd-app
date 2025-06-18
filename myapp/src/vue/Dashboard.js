import React, { useEffect, useState } from 'react';
import Stat from './stat';

const MOTIF_MAP = {
  "nb_ventes": "Nombre d’activations",
  "moy_nb_vente": "Moyenne d’activations",
  "delai_moyen_activations": "Délai moyen d’activation",
  "code_phase": "Tranche horaire",
  "pct_ventes_wilaya": "Part des ventes dans la Wilaya",
  "pdv_unique_clients": "Nombre de clients uniques",
  "ratio_clients_uniques": "Ratio de clients uniques",
  "pct_new_subs": "Pourcentage de nouveaux abonnés",
  "var": "Variation des ventes",
  "nb_bursts_360s": "Nombre de bursts (≥5 activations en 6 min)",
  "nb_sim": "Nombre de SIM",
  "delai_moyen_jours": "Délai moyen (jours)",
  "delai_total_jours": "Délai total (jours)",
  "nb_wilayas_distinctes": "Nb wilayas distinctes",
  "ecart_type_jours": "Écart-type jours",
  "nb_pdvs_distincts": "Nb PDVs distincts",
  "nb_code_sub_wilaya_distincts": "Nb codes sub/wilaya distincts",
  "nb_cas_wilaya_diff": "Nb cas wilaya différents",
  "nb_wilayas_pdv_sub_distinctes": "Nb wilayas PDV/sub distinctes"
};

const PDV_STAT_KEYS = [
  "nb_ventes", "moy_nb_vente", "delai_moyen_activations",
  "pct_ventes_wilaya", "pdv_unique_clients", "ratio_clients_uniques", "pct_new_subs",
  "var", "nb_bursts_360s"
];
const SUB_STAT_KEYS = [
  "subscriber_id_number", "nb_sim", "delai_moyen_jours", "delai_total_jours",
  "nb_wilayas_distinctes", "ecart_type_jours", "nb_pdvs_distincts",
  "nb_code_sub_wilaya_distincts", "nb_cas_wilaya_diff", "nb_wilayas_pdv_sub_distinctes"
];

function renderMotif(motif) {
  return MOTIF_MAP[motif] || motif;
}

// Export CSV des stats du grid
function handleExportGridStats(rows) {
  if (!rows.length) return;
  const cols = Object.keys(rows[0]);
  const csv = [
    cols.join(';'),
    ...rows.map(row => cols.map(k => `"${row[k] ?? ''}"`).join(';'))
  ].join('\n');
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = "grid_stats.csv";
  a.click();
  URL.revokeObjectURL(url);
}

// Export CSV des transactions grid (adapter selon ton backend)
function handleExportGridTransactions(rows) {
  if (!rows.length) return;
  const ids = rows.map(r => r.ID).join(',');
  // À adapter selon ton backend, ici une simple ouverture d'URL :
  window.open(`http://localhost:8000/api/export-grid-transactions?ids=${encodeURIComponent(ids)}`, '_blank');
}

function Dashboard({ model }) {
  const [acteur, setActeur] = useState("pdv");
  const actorFile = acteur === "pdv" ? "A_pdv_Fraud" : "A_sub_Fraud";
  const isPDV = acteur === "pdv";

  const idLabel = isPDV ? "ID Point de Vente" : "ID Adhérent";
  const selectLabel = isPDV ? "Point de Vente" : "Adhérent";

  // Colonnes tableau principal (kmeans)
  const TABLE_COLS = [
    { key: "ID", label: idLabel },
    { key: "DateDebut", label: "Date Début" },
    { key: "DateFin", label: "Date Fin" },
    { key: "Score", label: "Score" },
    { key: "Motif", label: "Motif" },
    ...(isPDV ? [{ key: "Wilaya", label: "Wilaya" }, { key: "TimePhase", label: "Tranche horaire" }] : [])
  ];

  // Colonnes tableau grid
  const GRID_TABLE_COLS = isPDV
    ? [
        { key: "ID", label: idLabel },
        { key: "date_debut_analyse", label: "Date Début" },
        { key: "date_fin_analyse", label: "Date Fin" },
        { key: "Wilaya", label: "Wilaya" },
        { key: "time_phase", label: "Tranche horaire" }
      ]
    : [
        { key: "ID", label: idLabel },
        { key: "date_debut_analyse", label: "Date Début" },
        { key: "date_fin_analyse", label: "Date Fin" }
      ];

  const [fraudData, setFraudData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dateDebut, setDateDebut] = useState('');
  const [dateFin, setDateFin] = useState('');
  const [motifList, setMotifList] = useState([]);
  const [selectedMotif, setSelectedMotif] = useState('');
  const [timePhaseList, setTimePhaseList] = useState([]);
  const [selectedTimePhase, setSelectedTimePhase] = useState('');
  const [dateList, setDateList] = useState([]);
  const [wilayaList, setWilayaList] = useState([]);
  const [selectedWilaya, setSelectedWilaya] = useState('');

  const [fraudStats, setFraudStats] = useState({
    totalAnomalies: 0,
    topPdv: "Aucun",
    topWilaya: "Aucune",
    topMotif: "Aucun"
  });
  const [statLoading, setStatLoading] = useState(true);

  // Pour stats en ligne (tableau principal)
  const [openedIndex, setOpenedIndex] = useState(null);
  const [rowStats, setRowStats] = useState(null);
  const [rowStatsLoading, setRowStatsLoading] = useState(false);

  // Pour grid sample (tableau secondaire, cluster -2)
  const [gridSample, setGridSample] = useState([]);
  const [gridLoading, setGridLoading] = useState(false);
  const [openedGridIndex, setOpenedGridIndex] = useState(null);
  const [gridRowStats, setGridRowStats] = useState(null);
  const [gridRowStatsLoading, setGridRowStatsLoading] = useState(false);

  const STAT_KEYS = isPDV ? PDV_STAT_KEYS : SUB_STAT_KEYS;

  // Motifs
  useEffect(() => {
    setSelectedMotif("");
    if (!model) return;
    fetch(`http://localhost:8000/api/all-motifs?model=${encodeURIComponent(model)}&actor=${actorFile}`)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setMotifList(resJson.motifs);
        else setMotifList([]);
      });
  }, [model, actorFile]);

  // Wilayas (PDV seulement)
  useEffect(() => {
    setSelectedWilaya("");
    if (!model || !isPDV) return setWilayaList([]);
    fetch(`http://localhost:8000/api/all-wilayas?model=${encodeURIComponent(model)}&actor=${actorFile}`)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setWilayaList(resJson.wilayas);
        else setWilayaList([]);
      });
  }, [model, actorFile, isPDV]);

  // Timephases (PDV seulement)
  useEffect(() => {
    setSelectedTimePhase("");
    if (!model || !isPDV) return setTimePhaseList([]);
    fetch(`http://localhost:8000/api/all-timephases?model=${encodeURIComponent(model)}&actor=${actorFile}`)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setTimePhaseList(resJson.time_phases);
        else setTimePhaseList([]);
      });
  }, [model, actorFile, isPDV]);

  // Dates
  useEffect(() => {
    setDateDebut("");
    setDateFin("");
    if (!model) return;
    fetch(`http://localhost:8000/api/all-dates?model=${encodeURIComponent(model)}&actor=${actorFile}`)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setDateList(resJson.dates);
        else setDateList([]);
      });
  }, [model, actorFile]);

  // Données anomalies (tableau principal)
  useEffect(() => {
    if (!model) return;
    setLoading(true);
    setOpenedIndex(null);
    setRowStats(null);

    let url = `http://localhost:8000/api/top-fraud?model=${encodeURIComponent(model)}&actor=${actorFile}`;
    if (selectedMotif) url += `&motif=${encodeURIComponent(selectedMotif)}`;
    if (dateDebut) url += `&date_debut=${encodeURIComponent(dateDebut)}`;
    if (dateFin) url += `&date_fin=${encodeURIComponent(dateFin)}`;
    if (isPDV && selectedTimePhase) url += `&time_phase=${encodeURIComponent(selectedTimePhase)}`;
    if (isPDV && selectedWilaya) url += `&wilaya=${encodeURIComponent(selectedWilaya)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    fetch(url)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setFraudData(resJson.rows);
        else {
          setFraudData([]);
          alert("Erreur : " + resJson.detail);
        }
      })
      .catch(() => {
        setFraudData([]);
        alert("Erreur de récupération des anomalies.");
      })
      .finally(() => setLoading(false));
  }, [model, actorFile, selectedMotif, dateDebut, dateFin, selectedTimePhase, selectedWilaya, search, isPDV]);

  // Stats globales
  useEffect(() => {
    if (!model) return;
    setStatLoading(true);
    let url = `http://localhost:8000/api/fraud-stats?model=${encodeURIComponent(model)}&actor=${actorFile}`;
    if (selectedMotif) url += `&motif=${encodeURIComponent(selectedMotif)}`;
    if (dateDebut) url += `&date_debut=${encodeURIComponent(dateDebut)}`;
    if (dateFin) url += `&date_fin=${encodeURIComponent(dateFin)}`;
    if (isPDV && selectedTimePhase) url += `&time_phase=${encodeURIComponent(selectedTimePhase)}`;
    if (isPDV && selectedWilaya) url += `&wilaya=${encodeURIComponent(selectedWilaya)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    fetch(url)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setFraudStats(resJson);
        else setFraudStats({
          totalAnomalies: 0,
          topPdv: "Aucun",
          topWilaya: "Aucune",
          topMotif: "Aucun"
        });
      })
      .catch(() => {
        setFraudStats({
          totalAnomalies: 0,
          topPdv: "Aucun",
          topWilaya: "Aucune",
          topMotif: "Aucun"
        });
      })
      .finally(() => setStatLoading(false));
  }, [model, actorFile, selectedMotif, dateDebut, dateFin, selectedTimePhase, selectedWilaya, search, isPDV]);

  // Grid sample (pour grid-kmeans)
  useEffect(() => {
    if (model !== "grid-kmeans" || fraudData.length === 0) {
      setGridSample([]);
      return;
    }
    setGridLoading(true);
    const excludeIDs = fraudData.map(row => row.ID).join(",");
    fetch(`http://localhost:8000/api/grid-sample?model=${encodeURIComponent(model)}&actor=${actorFile}&exclude_ids=${encodeURIComponent(excludeIDs)}`)
      .then(res => res.json())
      .then(resJson => {
        if (resJson.status === "ok") setGridSample(resJson.rows);
        else setGridSample([]);
      })
      .finally(() => setGridLoading(false));
  }, [model, actorFile, fraudData]);

  // Réinitialiser
  const handleResetFilters = () => {
    setSearch('');
    setDateDebut('');
    setDateFin('');
    setSelectedMotif('');
    setSelectedTimePhase('');
    setSelectedWilaya('');
    setFraudData([]);
    setLoading(true);
    setOpenedIndex(null);
    setRowStats(null);
  };

  // Afficher/masquer stats par ligne (tableau principal)
  const handleShowStats = (row, index) => {
    if (openedIndex === index) {
      setOpenedIndex(null);
      setRowStats(null);
      return;
    }
    setOpenedIndex(index);
    setRowStatsLoading(true);
    setRowStats(null);

    let endpoint, params;
    if (isPDV) {
      endpoint = "pdv-stats";
      params = `model=${encodeURIComponent(model)}&pdv_id=${row.ID}&date_debut=${row.DateDebut}&date_fin=${row.DateFin}&score=${row.Score}`;
      if (row.Wilaya) params += `&wilaya=${row.Wilaya}`;
    } else {
      endpoint = "sub-stats";
      params = `model=${encodeURIComponent(model)}&sub_id=${row.ID}&date_debut=${row.DateDebut}&date_fin=${row.DateFin}`;
      if (row.Score !== undefined) params += `&score=${row.Score}`;
    }
    fetch(`http://localhost:8000/api/${endpoint}?${params}`)
      .then(res => res.json())
      .then(stats => setRowStats(stats))
      .finally(() => setRowStatsLoading(false));
  };

  // Tableau réutilisable
 function renderTableau(
  rows, tableTitle, openedIdx, rowStats, rowStatsLoading, onShowStats, columns = TABLE_COLS, loadingState = false, options = {}
) {
  // Option pour désactiver "En savoir plus" (pour le tableau Grid)
  const showDetails = !options.noDetails;

  // Téléchargement des transactions individuelles (pour la ligne)
  function handleExportIndividualTransactions(row, model, acteur) {
    window.open(
      `http://localhost:8000/api/export-individual-transactions?model=${encodeURIComponent(model)}&acteur=${encodeURIComponent(acteur)}&id=${encodeURIComponent(row.ID)}`,
      "_blank"
    );
  }

  return (
    <div className="bg-[#1E1E1E] p-4 rounded-lg shadow-lg mb-8">
      <h2 className="text-xl font-semibold mb-4">{tableTitle}</h2>
      {loadingState ? (
        <div className="text-center py-12 text-gray-400">Chargement…</div>
      ) : rows.length === 0 ? (
        <p className="text-center text-gray-400">Aucune anomalie trouvée.</p>
      ) : (
        <>
          <table className="min-w-full table-auto">
            <thead>
              <tr className="border-b border-gray-600">
                {columns.map(col => (
                  <th key={col.key} className="px-4 py-2 text-left">{col.label}</th>
                ))}
                {showDetails && <th className="px-4 py-2 text-left">Action</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <React.Fragment key={row.ID || i}>
                  <tr className="border-t border-gray-600">
                    {columns.map(col => (
                      <td key={col.key} className="px-4 py-2">
                        {col.key === "Motif"
                          ? renderMotif(row.Motif)
                          : row[col.key] || "-"}
                      </td>
                    ))}
                    {showDetails && (
                      <td className="px-4 py-2">
                        <button
                          onClick={() => onShowStats(row, i)}
                          className={`px-3 py-1 rounded ${
                            openedIdx === i
                              ? "bg-[#d32f2f] text-white"
                              : "bg-[#E60000] text-white hover:bg-red-700"
                          } transition`}
                        >
                          {openedIdx === i ? "Fermer" : `En savoir plus`}
                        </button>
                      </td>
                    )}
                  </tr>
                  {/* Bloc expansion : Stats + bouton téléchargement transaction individuel */}
                  {showDetails && openedIdx === i && (
                    <tr>
                      <td colSpan={columns.length + 1}>
                        <div className="bg-[#181924] border-l-4 border-[#E60000] rounded-xl my-2 px-6 py-5 shadow flex flex-col items-center gap-4">
                          {rowStatsLoading || !rowStats ? (
                            <div className="text-white text-center w-full">Chargement…</div>
                          ) : (
                            <>
                              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 w-full mb-4">
                                {STAT_KEYS.map(key => (
                                  <div
                                    key={key}
                                    className="bg-gradient-to-br from-[#232438] to-[#1E1E2E] rounded-xl p-4 shadow border border-[#24243d] flex flex-col items-center w-full min-w-[130px]"
                                  >
                                    <span className="text-xs text-gray-400 mb-1 text-center">{renderMotif(key)}</span>
                                    <span className="font-bold text-lg text-[#E60000]">
                                      {rowStats[key] !== undefined && rowStats[key] !== null && rowStats[key] !== '' ? rowStats[key] : "-"}
                                    </span>
                                  </div>
                                ))}
                              </div>
                              {/* Bouton individuel sous les stats */}
                              <button
                                className="px-5 py-2 mt-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-800 transition"
                                onClick={() => handleExportIndividualTransactions(row, model, acteur)}
                              >
                                Télécharger les transactions
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          {/* Boutons d'export pour le grid (noDetails) */}
          {options.noDetails && (
            <div className="flex gap-6 justify-end mt-6">
              <button
                className="px-6 py-2 rounded bg-green-600 text-white font-semibold hover:bg-green-800 transition"
                onClick={() => options.handleExportGridStats(rows, options.model, options.acteur)}
              >
                Télécharger les stats du Grid
              </button>
              <button
                className="px-6 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-800 transition"
                onClick={() => options.handleExportGridTransactions(rows, options.model, options.acteur)}
              >
                Télécharger les transactions Grid
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

  function handleExportGridStats(rows, model, acteur) {
  window.open(
    `http://localhost:8000/api/export-grid-stats?model=${encodeURIComponent(model)}&acteur=${encodeURIComponent(acteur)}`,
    "_blank"
  );
}

function handleExportGridTransactions(rows, model, acteur) {
  window.open(
    `http://localhost:8000/api/export-grid-transactions?model=${encodeURIComponent(model)}&acteur=${encodeURIComponent(acteur)}`,
    "_blank"
  );
}

function handleExportIndividualTransactions(row, model, acteur) {
  window.open(
    `http://localhost:8000/api/export-individual-transactions?model=${encodeURIComponent(model)}&acteur=${encodeURIComponent(acteur)}&id=${encodeURIComponent(row.ID)}`,
    "_blank"
  );
}

  return (
    <div className="min-h-screen bg-[#121212] text-white p-6 space-y-8 flex flex-col ml-[21vh] p-5 rounded-md">
      <h1 className="text-3xl font-semibold text-center text-white mb-4">
        Dashboard de Détection de Fraude
      </h1>
      <div className="flex flex-col mb-2 max-w-xs">
        <label className="text-sm mb-1">Acteur :</label>
        <select
          value={acteur}
          onChange={e => setActeur(e.target.value)}
          className="p-2 rounded bg-[#222] text-white min-w-[180px]"
        >
          <option value="pdv">Point de Vente</option>
          <option value="sub">Adhérent</option>
        </select>
      </div>
      <Stat 
        acteur={acteur}
        totalAnomalies={fraudStats.totalAnomalies}
        topPdv={fraudStats.topPdv}
        topWilaya={fraudStats.topWilaya}
        topMotif={renderMotif(fraudStats.topMotif)}
        loading={statLoading}
      />
      <div className="flex flex-wrap gap-4 mb-4 items-end">
        {/* Filtres */}
        <div className="flex flex-col">
          <label className="text-sm mb-1">Recherche ({idLabel} ou Motif) :</label>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="p-2 rounded bg-[#222] text-white"
            placeholder={isPDV ? "Ex: P01, Activation..." : "Ex: 123456, Changement..."}
          />
        </div>
        <div className="flex flex-col">
          <label className="text-sm mb-1">Date début (min) :</label>
          <select
            value={dateDebut}
            onChange={e => setDateDebut(e.target.value)}
            className="p-2 rounded bg-[#222] text-white min-w-[160px]"
          >
            <option value="">Toutes</option>
            {dateList.map(date => (
              <option key={date} value={date}>{date}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm mb-1">Date fin (max) :</label>
          <select
            value={dateFin}
            onChange={e => setDateFin(e.target.value)}
            className="p-2 rounded bg-[#222] text-white min-w-[160px]"
          >
            <option value="">Toutes</option>
            {dateList.map(date => (
              <option key={date} value={date}>{date}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm mb-1">Motif :</label>
          <select
            value={selectedMotif}
            onChange={e => setSelectedMotif(e.target.value)}
            className="p-2 rounded bg-[#222] text-white min-w-[220px]"
          >
            <option value="">Tous</option>
            {motifList
              .filter(m => m && m.trim() !== "")
              .map(m => (
                <option key={m} value={m}>
                  {renderMotif(m)}
                </option>
              ))}
          </select>
        </div>
        {isPDV && (
          <>
            <div className="flex flex-col">
              <label className="text-sm mb-1">Wilaya :</label>
              <select
                value={selectedWilaya}
                onChange={e => setSelectedWilaya(e.target.value)}
                className="p-2 rounded bg-[#222] text-white min-w-[150px]"
              >
                <option value="">Toutes</option>
                {wilayaList.map(wilaya => (
                  <option key={wilaya} value={wilaya}>{wilaya}</option>
                ))}
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-sm mb-1">Tranche horaire :</label>
              <select
                value={selectedTimePhase}
                onChange={e => setSelectedTimePhase(e.target.value)}
                className="p-2 rounded bg-[#222] text-white min-w-[160px]"
              >
                <option value="">Toutes</option>
                {timePhaseList.map(tp => (
                  <option key={tp} value={tp}>
                    {tp}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        <button
          className="h-10 px-4 rounded bg-gray-300 hover:bg-red-500 hover:text-white transition mt-5"
          onClick={handleResetFilters}
        >
          Réinitialiser
        </button>
      </div>
      {/* Tableau principal */}
      {renderTableau(
        fraudData,
        "Top 15 Anomalies k-means",
        openedIndex,
        rowStats,
        rowStatsLoading,
        handleShowStats,
        TABLE_COLS,
        loading
      )}

      {/* Tableau secondaire pour grid-kmeans — PAS de "En savoir plus", mais avec boutons d'export */}
      {model === "grid-kmeans" && renderTableau(
        gridSample,
        "Échantillon aléatoire 10 Grid ",
        openedGridIndex,
        gridRowStats,
        gridRowStatsLoading,
        () => {},
        GRID_TABLE_COLS,
        gridLoading,
        { noDetails: true }
      )}
    </div>
  );
}

export default Dashboard;
