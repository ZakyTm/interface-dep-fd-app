import os

from .App_1 import App_1
from .App_2 import App_2




def main(path_source, path_dest, model, max_fraud_rate=None, min_fraud_rate=None, grid_size=None):
    print("main lancé avec path_source =", path_source, "et path_dest =", path_dest)

    resultat_path = os.path.join(path_dest, "Resultat")
    datadays_path = os.path.join(path_dest, "DataDays")
    model_result_path = os.path.join(resultat_path, model)

    print("DataDays existe :", os.path.exists(datadays_path))
    print("Resultat existe :", os.path.exists(resultat_path))

    # Vérifie si le répertoire du modèle existe déjà
    if os.path.exists(model_result_path):
        print(f"Le répertoire pour le modèle '{model}' existe déjà dans Resultat. Aucun traitement ne sera effectué.")
        return

    # Si les répertoires DataDays et Resultat existent, on lance l'entraînement
    if os.path.exists(datadays_path) and os.path.exists(resultat_path):
        print("Début de l'entraînement.....")
        App_2(path_dest, model)
    else:
        print("Début de l'analyse.........")
        App_1(path_dest, path_source)
        App_2(path_dest, model, max_fraud_rate=max_fraud_rate, min_fraud_rate=min_fraud_rate, grid_size=grid_size)
