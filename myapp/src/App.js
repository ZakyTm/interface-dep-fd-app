import React, { useEffect, useState } from "react";
import Nav from './vue/Nav';
import Dashboard from './vue/Dashboard';
import Home from './vue/Home';
import loading from './img/tube-spinner.svg';

function App() {
  const [msg, setMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const [dashData, setDashData] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/hello")
      .then((res) => res.json())
      .then((data) => setMsg(data.message));
  }, []);

  const handleAnalyse = (result, model) => {
    setIsLoading(false);
    setDashData(result);
    setSelectedModel(model); // <-- Le modèle choisi dans Nav
    setShowDashboard(true);
  };

  const handleStartLoading = () => {
    setIsLoading(true);
    setShowDashboard(false);
  };

  return (
    <div className="flex ">
      <Nav onStartLoading={handleStartLoading} onAnalyseDone={handleAnalyse} />
      <main className="ml-24 p-4 flex-1">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <img src={loading} alt="Chargement" className="w-24 h-24 mb-6 animate-pulse" style={{ maxWidth: "120px", maxHeight: "120px" }} />
            <p className="text-xl font-bold text-[#E60000]">Analyse en cours…</p>
          </div>
        ) : showDashboard ? (
          <Dashboard data={dashData} model={selectedModel} />
        ) : (
          <Home />
        )}
      </main>
    </div>
  );
}

export default App;
