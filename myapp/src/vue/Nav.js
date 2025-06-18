import React, { useState } from "react";

function Nav({ onStartLoading, onAnalyseDone }) {
  const [fileName, setFileName] = useState(null);
  const [model, setModel] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxFraudRate, setMaxFraudRate] = useState("");
  const [minFraudRate, setMinFraudRate] = useState("");
  const [gridSize, setGridSize] = useState("");
  const [fileObject, setFileObject] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setFileName(file.name);
      setFileObject(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!fileObject) {
      alert("Veuillez sélectionner un fichier Excel.");
      return;
    }
    if (!model) {
      alert("Veuillez choisir un modèle.");
      return;
    }

    if (onStartLoading) onStartLoading();

    const formData = new FormData();
    formData.append("file", fileObject);
    formData.append("model", model);
    formData.append("use_advanced", showAdvanced);

    if (showAdvanced) {
      if (model === "kmeans" || model === "grid-kmeans") {
        if (maxFraudRate !== "") formData.append("max_fraud_rate", maxFraudRate);
        if (minFraudRate !== "") formData.append("min_fraud_rate", minFraudRate);
      }
      if (model === "grid-kmeans" && gridSize !== "") {
        formData.append("grid_size", gridSize);
      }
    }

    try {
      const response = await fetch("http://localhost:8000/analyse", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (onAnalyseDone) onAnalyseDone(data, model); // <-- On passe aussi le modèle ici !
    } catch (error) {
      alert("Erreur lors de l'envoi : " + error);
      if (onAnalyseDone) onAnalyseDone(null, model);
    }
  };

  return (
    <nav
      className="fixed top-0 left-0 h-screen w-[35vh] p-3 bg-[#121212] shadow-lg flex flex-col items-center py-6 space-y-6 overflow-auto overflow-x-hidden box-border"
      aria-label="Navigation latérale"
    >
      {/* Logo : inchangé */}
      <svg
        width="280"
        height="80"
        viewBox="0 0 280 80"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="Djezzy Fraud logo"
        className="mb-4"
      >
        <defs>
          <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#E60000" />
            <stop offset="100%" stopColor="#FF3333" />
          </linearGradient>
          <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow
              dx="0"
              dy="2"
              stdDeviation="2"
              floodColor="#000"
              floodOpacity="0.15"
            />
          </filter>
        </defs>
        <circle
          cx="40"
          cy="40"
          r="30"
          fill="url(#grad)"
          filter="url(#shadow)"
        />
        <circle
          cx="40"
          cy="40"
          r="18"
          stroke="white"
          strokeWidth="3"
          fill="none"
        />
        <rect
          x="53"
          y="53"
          width="12"
          height="4"
          rx="2"
          ry="2"
          fill="white"
          transform="rotate(45 59 55)"
        />
        <g transform="translate(40, 40)">
          <polygon points="0,-10 9,9 -9,9" fill="#B22222" />
          <rect x="-1" y="-6" width="2" height="7" fill="white" rx="0.3" />
          <circle cx="0" cy="6" r="1.5" fill="white" />
        </g>
        <text
          x="90"
          y="48"
          fontFamily="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"
          fontSize="28"
          fill="#ffffff"
          fontWeight="600"
          textAnchor="start"
          letterSpacing="0.5"
        >
          Djezzy Fraud
        </text>
      </svg>

      {/* Bouton sélection fichier */}
      <label
        htmlFor="file-upload"
        className="cursor-pointer px-4 py-2 bg-[#E60000] text-white rounded-md hover:bg-[#bf0000] transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#E60000] w-full text-center text-sm select-none"
        title="Sélectionner un fichier Excel"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            document.getElementById("file-upload")?.click();
          }
        }}
      >
        Fichier Excel
      </label>
      <input
        id="file-upload"
        type="file"
        accept=".xls,.xlsx"
        className="hidden"
        onChange={handleFileChange}
        aria-describedby="file-name"
      />

      {/* Nom fichier */}
      {fileName && (
        <p
          id="file-name"
          className="text-white text-xs px-2 truncate text-center max-w-full"
          title={fileName}
          aria-live="polite"
        >
          {fileName}
        </p>
      )}

      {/* Formulaire */}
      <form className="w-full flex flex-col gap-3 mt-4 text-white" onSubmit={handleSubmit}>
        <label htmlFor="model-select" className="font-semibold mt-2">
          Modèle
        </label>
        <select
          id="model-select"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="rounded-sm p-2 text-black"
        >
          <option value="" disabled>
            Choisissez votre modèle
          </option>
          <option value="kmeans">K-means</option>
          <option value="grid-kmeans">Grid & K-means</option>
          <option value="isolation-forest">Isolation Forest</option>
          <option value="autoencoder">Autoencoder</option>
        </select>

        {/* Checkbox Paramètres Avancés */}
        <label className="flex items-center gap-2 mt-3 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showAdvanced}
            onChange={() => setShowAdvanced(!showAdvanced)}
            className="w-4 h-4"
          />
          <span>Paramètres Avancés</span>
        </label>

        {/* Paramètres avancés pour kmeans */}
        {showAdvanced && model === "kmeans" && (
          <div className="flex flex-col gap-2 mt-3 text-white">
            <label htmlFor="max-fraud" className="font-semibold">
              Taux max Fraude
            </label>
            <input
              id="max-fraud"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={maxFraudRate}
              onChange={(e) => setMaxFraudRate(e.target.value)}
              placeholder="Exemple : 0.5"
              className="rounded-sm p-2 text-black"
            />

            <label htmlFor="min-fraud" className="font-semibold mt-2">
              Taux min Fraude
            </label>
            <input
              id="min-fraud"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={minFraudRate}
              onChange={(e) => setMinFraudRate(e.target.value)}
              placeholder="Exemple : 0.1"
              className="rounded-sm p-2 text-black"
            />
          </div>
        )}

        {/* Paramètres avancés pour grid-kmeans */}
        {showAdvanced && model === "grid-kmeans" && (
          <div className="flex flex-col gap-2 mt-3 text-white">
            <label htmlFor="max-fraud" className="font-semibold">
              Taux max Fraude
            </label>
            <input
              id="max-fraud"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={maxFraudRate}
              onChange={(e) => setMaxFraudRate(e.target.value)}
              placeholder="Exemple : 0.5"
              className="rounded-sm p-2 text-black"
            />

            <label htmlFor="min-fraud" className="font-semibold mt-2">
              Taux min Fraude
            </label>
            <input
              id="min-fraud"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={minFraudRate}
              onChange={(e) => setMinFraudRate(e.target.value)}
              placeholder="Exemple : 0.1"
              className="rounded-sm p-2 text-black"
            />

            <label htmlFor="grid-size" className="font-semibold mt-2">
              Taille de la grille
            </label>
            <input
              id="grid-size"
              type="number"
              min="0"
              max="100"
              step="2.5"
              value={gridSize}
              onChange={(e) => setGridSize(e.target.value)}
              placeholder="Exemple : 10"
              className="rounded-sm p-2 text-black"
            />
          </div>
        )}

        <input type="submit" value="Detecter" className="p-4 m-2 bg-[#E60000] rounded-md" />
      </form>
    </nav>
  );
}

export default Nav;
