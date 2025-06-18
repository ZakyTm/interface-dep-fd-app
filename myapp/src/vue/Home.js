import React from "react";
import logodjezzy from "../img/logodjezzy.png"; // Assure-toi que ce chemin est correct

function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full text-center ml-[18vh]">
      <img
        src={logodjezzy}
        alt="Logo Djezzy Fraud"
        className="w-32 h-32 mb-4 mt-8"
        style={{ objectFit: "contain" }}
      />
      <h1 className="text-3xl font-bold mb-2 text-[#E60000]">Bienvenue !</h1>
      <p className="text-lg text-gray-600">
        Bienvenue sur la plateforme de détection de fraude Djezzy.<br />
        Veuillez sélectionner un modèle et importer un fichier à gauche pour commencer l’analyse.
      </p>
    </div>
  );
}

export default Home;
