
from .model.kmeans import *
from .model.Grid import *
from .Evaluation import *
from .Util import *



def App_2(cR,model,max_fraud_rate=None, min_fraud_rate=None, grid_size=None):
    D=pd.read_excel(rf"{cR}/Data0.xlsx")
    if max_fraud_rate is not None and min_fraud_rate is not None:
     # Convertis les entrées en float si elles sont str
     min_fraud = float(min_fraud_rate)
     max_fraud = float(max_fraud_rate)
     distribution_bounds = [(0.7, 0.85), (0.1, 0.15), (min_fraud, max_fraud)]
    else:
     distribution_bounds = [(0.7, 0.85), (0.1, 0.15), (0.05, 0.1)]

    if model == "kmeans":
     # _____________________________________Executer l'Algo Kmeans_________________________________________________
     cree_R(rf"{cR}/Resultat/", "Kmeans")
     K_means(rf"{cR}/DataDays/sub_Days/Analyse_sub_globale.xlsx", rf"{cR}/Resultat/Kmeans/A_sub_Fraud.xlsx",distribution_bounds=distribution_bounds)
     K_means(rf"{cR}/DataDays/Analyse_Phases.xlsx", rf"{cR}/Resultat/Kmeans/A_pdv_Fraud.xlsx",distribution_bounds=distribution_bounds)
     # ______________________________________Jointure R sub avec datasource_____________________________________________
     rF = DataManager.join_strict_Sub(D, DataManager.charger_data(rf"{cR}/Resultat/Kmeans/A_sub_Fraud.xlsx"))
     rF = DataManager.supprimer_doublons_msisdn(rF)
     DataManager.enregistrer_data(rF, rf"{cR}/Resultat/Kmeans/D_sub_Fraud.xlsx")
     # ______________________________________Jointure R pdv avec datasource__________________________________________
     rF = DataManager.join_strict_PDV(D, DataManager.charger_data(rf"{cR}/Resultat/Kmeans/A_pdv_Fraud.xlsx"))
     rF = DataManager.supprimer_doublons_msisdn(rF)
     DataManager.enregistrer_data(rF, rf"{cR}/Resultat/Kmeans/D_pdv_Fraud.xlsx")
     # ------------------------------------------------------------------------------------------------------------------
    if model == "grid-kmeans":
     # ___________________________________________Executer l'Algo Grid_________________________________________________
     cree_R(rf"{cR}/Resultat/", "grid-kmeans")
     Grid_Hybride(rf"{cR}/DataDays/sub_Days/Analyse_sub_globale.xlsx", rf"{cR}/Resultat/grid-kmeans/A_sub_Fraud.xlsx" ,grid_size=grid_size if grid_size is not None else 12.8,
            distribution_bounds=distribution_bounds)
     Grid_Hybride(rf"{cR}/DataDays/Analyse_Phases.xlsx", rf"{cR}/Resultat/grid-kmeans/A_pdv_Fraud.xlsx", grid_size=grid_size if grid_size is not None else 12.8,
            distribution_bounds=distribution_bounds)
     # ______________________________________Jointure R sub avec datasource_____________________________________________
     rF = DataManager.join_strict_Sub(D, DataManager.charger_data(rf"{cR}/Resultat/grid-kmeans/A_sub_Fraud.xlsx"))
     rF = DataManager.supprimer_doublons_msisdn(rF)
     DataManager.enregistrer_data(rF, rf"{cR}/Resultat/grid-kmeans/D_sub_Fraud.xlsx")
     # ______________________________________Jointure R pdv avec datasource__________________________________________
     rF = DataManager.join_strict_PDV(D, DataManager.charger_data(rf"{cR}/Resultat/grid-kmeans/A_pdv_Fraud.xlsx"))
     rF = DataManager.supprimer_doublons_msisdn(rF)
     DataManager.enregistrer_data(rF, rf"{cR}/Resultat/grid-kmeans/D_pdv_Fraud.xlsx")
