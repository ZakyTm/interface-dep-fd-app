import { BarChart3, AlertCircle, MapPin, Award, UserRound } from "lucide-react"; // UserRound pour Adhérant

function Stat({ 
  totalAnomalies = 0, 
  topPdv = "Aucun", 
  topWilaya = "Aucune", 
  topMotif = "Aucun",
  acteur = "pdv" // "pdv" ou "sub"
}) {
  return (
    <div className="w-full max-w-5xl mx-auto bg-[#121212] rounded-2xl border border-gray-600 p-8 shadow-xl mt-8">
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-8 min-h-[220px]">
        {/* Grande case à gauche */}
        <div className="col-span-1 row-span-3 flex flex-col justify-center items-center bg-gradient-to-br from-[#E60000]/80 to-[#222] rounded-2xl border-2 border-[#E60000] shadow-lg hover:scale-105 transition-transform duration-200 min-h-[220px]">
          <div className="w-full py-3 px-4 bg-[#E60000] rounded-t-2xl text-center mb-3">
            <span className="text-lg font-semibold tracking-wide text-white">
              Nombre d’anomalies détectées
            </span>
          </div>
          <AlertCircle className="w-14 h-14 text-white mb-1" />
          <div className="text-6xl font-extrabold text-white drop-shadow-lg">{totalAnomalies}</div>
        </div>
        {/* Cases droites */}
        <div className="col-span-3 flex flex-col justify-between gap-5">
          <div className={`flex gap-5 ${acteur === "sub" ? "justify-center" : ""}`}>
            {/* 1er bloc : PDV ou Adhérant le plus touché */}
            <div className="bg-[#222] rounded-2xl border border-gray-600 p-6 flex flex-1 flex-col items-center shadow hover:shadow-lg hover:border-[#E60000] transition">
              {acteur === "pdv" 
                ? <BarChart3 className="w-8 h-8 text-[#E60000] mb-2" />
                : <UserRound className="w-8 h-8 text-[#E60000] mb-2" />}
              <span className="text-base text-white font-medium mb-1">
                {acteur === "pdv" ? "PDV le plus touché" : "Adhérant le plus touché"}
              </span>
              <span className="text-2xl font-bold text-white">{topPdv}</span>
            </div>
            {/* 2e bloc : Wilaya (affiché que pour PDV) */}
            {acteur === "pdv" && (
              <div className="bg-[#222] rounded-2xl border border-gray-600 p-6 flex flex-1 flex-col items-center shadow hover:shadow-lg hover:border-[#E60000] transition">
                <MapPin className="w-8 h-8 text-[#E60000] mb-2" />
                <span className="text-base text-white font-medium mb-1">Wilaya la plus touchée</span>
                <span className="text-2xl font-bold text-white">{topWilaya}</span>
              </div>
            )}
            {/* 3e bloc : Motif */}
            <div className="bg-[#222] rounded-2xl border border-gray-600 p-6 flex flex-1 flex-col items-center shadow hover:shadow-lg hover:border-[#E60000] transition">
              <Award className="w-8 h-8 text-[#E60000] mb-2" />
              <span className="text-base text-white font-medium mb-1">Motif le plus fréquent</span>
              <span className="text-2xl font-bold text-white">{topMotif}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Stat;
