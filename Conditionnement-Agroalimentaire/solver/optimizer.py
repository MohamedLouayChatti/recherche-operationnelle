"""
Solver pour l'équilibrage de chaîne de montage agroalimentaire
Utilise Gurobi pour résoudre le problème PLNE
"""

import gurobipy as gp
from gurobipy import GRB
import json


class AssemblyLineOptimizer:
    """
    Optimiseur pour l'équilibrage de chaîne de montage
    """
    
    def __init__(self, data):
        """
        Initialise l'optimiseur avec les données du problème
        
        Args:
            data: dictionnaire contenant les tâches, postes, contraintes
        """
        self.data = data
        self.taches = data['taches']
        self.n_postes = data['nombre_postes']
        self.temps_cycle_max = data.get('temps_cycle_max', 100)
        self.model = None
        self.solution = None
        
    def build_model(self):
        """
        Construit le modèle PLNE
        """
        try:
            # Créer le modèle
            self.model = gp.Model("EquilibrageChaine")
            self.model.setParam('OutputFlag', 0)  # Désactiver les logs
            
            n_taches = len(self.taches)
            taches_ids = [t['id'] for t in self.taches]
            postes = range(1, self.n_postes + 1)
            
            # Variables de décision
            # x[i,j] = 1 si la tâche i est assignée au poste j
            x = {}
            for i in taches_ids:
                for j in postes:
                    x[i, j] = self.model.addVar(vtype=GRB.BINARY, 
                                               name=f"x_{i}_{j}")
            
            # Variable pour le temps de cycle (temps max sur tous les postes)
            temps_cycle = self.model.addVar(vtype=GRB.CONTINUOUS, 
                                           name="temps_cycle")
            
            # Temps de charge par poste
            charge_poste = {}
            for j in postes:
                charge_poste[j] = self.model.addVar(vtype=GRB.CONTINUOUS,
                                                    name=f"charge_{j}")
            
            self.model.update()
            
            # CONTRAINTES
            
            # 1. Chaque tâche est assignée à exactement un poste
            for i in taches_ids:
                self.model.addConstr(
                    gp.quicksum(x[i, j] for j in postes) == 1,
                    name=f"assign_tache_{i}"
                )
            
            # 2. Calcul de la charge de chaque poste
            for j in postes:
                tache_dict = {t['id']: t for t in self.taches}
                self.model.addConstr(
                    charge_poste[j] == gp.quicksum(
                        x[i, j] * tache_dict[i]['duree'] 
                        for i in taches_ids
                    ),
                    name=f"charge_poste_{j}"
                )
            
            # 3. Le temps de cycle est le maximum des charges
            for j in postes:
                self.model.addConstr(
                    temps_cycle >= charge_poste[j],
                    name=f"temps_cycle_{j}"
                )
            
            # 4. Contraintes de précédence
            for tache in self.taches:
                i = tache['id']
                for pred_id in tache['prerequis']:
                    # Si tâche i au poste j, alors pred doit être à un poste <= j
                    for j in postes:
                        self.model.addConstr(
                            gp.quicksum(x[pred_id, k] for k in postes if k <= j) 
                            >= x[i, j],
                            name=f"precedence_{pred_id}_{i}_{j}"
                        )
            
            # 5. Contrainte de temps de cycle maximum
            self.model.addConstr(
                temps_cycle <= self.temps_cycle_max,
                name="temps_cycle_max"
            )
            
            # CONTRAINTES AVANCÉES (si présentes)
            if 'contraintes_ergonomie' in self.data:
                self._add_ergonomie_constraints(x, postes, taches_ids)
            
            # FONCTION OBJECTIF
            if 'objectifs_multiples' in self.data:
                self._set_multi_objective(x, temps_cycle, charge_poste, 
                                         postes, taches_ids)
            else:
                # Objectif simple : minimiser le temps de cycle
                self.model.setObjective(temps_cycle, GRB.MINIMIZE)
            
            self.variables = {
                'x': x,
                'temps_cycle': temps_cycle,
                'charge_poste': charge_poste
            }
            
            return True
            
        except Exception as e:
            print(f"Erreur construction modèle: {e}")
            return False
    
    def _add_ergonomie_constraints(self, x, postes, taches_ids):
        """
        Ajoute les contraintes d'ergonomie
        """
        contraintes = self.data['contraintes_ergonomie']
        
        # Pénibilité maximale par poste
        if 'penibilite_max_par_poste' in contraintes:
            pen_max = contraintes['penibilite_max_par_poste']
            tache_dict = {t['id']: t for t in self.taches}
            
            for j in postes:
                penibilite_poste = gp.quicksum(
                    x[i, j] * tache_dict[i].get('penibilite', 0)
                    for i in taches_ids
                )
                self.model.addConstr(
                    penibilite_poste <= pen_max,
                    name=f"penibilite_max_{j}"
                )
        
        # Tâches incompatibles (ne peuvent pas être au même poste)
        if 'taches_incompatibles' in contraintes:
            for t1, t2 in contraintes['taches_incompatibles']:
                for j in postes:
                    self.model.addConstr(
                        x[t1, j] + x[t2, j] <= 1,
                        name=f"incompatible_{t1}_{t2}_{j}"
                    )
    
    def _set_multi_objective(self, x, temps_cycle, charge_poste, 
                            postes, taches_ids):
        """
        Définit une fonction objectif multi-critères
        """
        obj = self.data['objectifs_multiples']
        w1 = obj.get('poids_temps_cycle', 0.5)
        w2 = obj.get('poids_equilibrage', 0.3)
        w3 = obj.get('poids_ergonomie', 0.2)
        
        # Normalisation approximative
        temps_total = sum(t['duree'] for t in self.taches)
        
        # Critère 1: Minimiser temps de cycle (normalisé)
        obj1 = temps_cycle / temps_total
        
        # Critère 2: Minimiser l'écart-type des charges (équilibrage)
        charge_moyenne = temps_total / self.n_postes
        ecarts = []
        for j in postes:
            ecart = self.model.addVar(vtype=GRB.CONTINUOUS, 
                                     name=f"ecart_{j}")
            self.model.addConstr(ecart >= charge_poste[j] - charge_moyenne)
            self.model.addConstr(ecart >= charge_moyenne - charge_poste[j])
            ecarts.append(ecart)
        
        obj2 = gp.quicksum(ecarts) / (self.n_postes * temps_total)
        
        # Critère 3: Minimiser pénibilité totale
        tache_dict = {t['id']: t for t in self.taches}
        penibilite_totale = gp.quicksum(
            x[i, j] * tache_dict[i].get('penibilite', 0)
            for i in taches_ids for j in postes
        )
        pen_max_possible = sum(t.get('penibilite', 0) for t in self.taches)
        obj3 = penibilite_totale / max(pen_max_possible, 1)
        
        # Objectif combiné
        objectif = w1 * obj1 + w2 * obj2 + w3 * obj3
        self.model.setObjective(objectif, GRB.MINIMIZE)
    
    def solve(self, time_limit=300):
        """
        Résout le modèle
        
        Args:
            time_limit: temps limite en secondes
            
        Returns:
            dict: solution avec affectations et statistiques
        """
        if self.model is None:
            success = self.build_model()
            if not success:
                return None
        
        try:
            # Paramètres du solveur
            self.model.setParam('TimeLimit', time_limit)
            self.model.setParam('MIPGap', 0.01)  # Gap de 1%
            
            # Résolution
            self.model.optimize()
            
            if self.model.status == GRB.OPTIMAL or self.model.status == GRB.TIME_LIMIT:
                return self._extract_solution()
            else:
                print(f"Statut: {self.model.status}")
                return None
                
        except Exception as e:
            print(f"Erreur résolution: {e}")
            return None
    
    def _extract_solution(self):
        """
        Extrait la solution du modèle résolu
        """
        x = self.variables['x']
        temps_cycle = self.variables['temps_cycle']
        charge_poste = self.variables['charge_poste']
        
        # Affectations
        affectations = {}
        for j in range(1, self.n_postes + 1):
            affectations[j] = []
        
        tache_dict = {t['id']: t for t in self.taches}
        
        for i in [t['id'] for t in self.taches]:
            for j in range(1, self.n_postes + 1):
                if x[i, j].X > 0.5:  # Variable binaire = 1
                    affectations[j].append({
                        'id': i,
                        'nom': tache_dict[i]['nom'],
                        'duree': tache_dict[i]['duree'],
                        'penibilite': tache_dict[i].get('penibilite', 0)
                    })
        
        # Statistiques
        charges = {}
        for j in range(1, self.n_postes + 1):
            charges[j] = charge_poste[j].X
        
        solution = {
            'affectations': affectations,
            'temps_cycle': temps_cycle.X,
            'charges': charges,
            'objectif': self.model.ObjVal,
            'gap': self.model.MIPGap if hasattr(self.model, 'MIPGap') else 0,
            'temps_resolution': self.model.Runtime,
            'n_postes': self.n_postes,
            'efficacite': (sum(charges.values()) / (self.n_postes * temps_cycle.X)) * 100
        }
        
        self.solution = solution
        return solution
    
    @staticmethod
    def load_from_json(filepath):
        """
        Charge les données depuis un fichier JSON
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return AssemblyLineOptimizer(data)