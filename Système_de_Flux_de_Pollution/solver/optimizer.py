# =============================================================================
# solver/optimizer.py - Module d'optimisation Gurobi
# =============================================================================

import gurobipy as gp
from gurobipy import GRB
from PyQt5.QtCore import QThread, pyqtSignal

class OptimizationThread(QThread):
    """Thread pour l'optimisation avec Gurobi"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, nodes, arcs):
        super().__init__()
        self.nodes = nodes
        self.arcs = arcs
    
    def run(self):
        try:
            self.progress.emit(10)
            result = self.solve_min_cost_flow()
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def solve_min_cost_flow(self):
        """
        Résout le problème de flux à coût minimum
        
        Variables: x_ij = flux sur l'arc (i,j)
        Objectif: min Σ c_ij * x_ij
        Contraintes:
        - Conservation: Σ x_ij - Σ x_ji = b_i
        - Capacités: 0 ≤ x_ij ≤ u_ij
        """
        model = gp.Model("Pollution_Flow")
        model.setParam('OutputFlag', 0)
        
        self.progress.emit(30)
        
        # Variables de décision
        flow_vars = {}
        for idx, arc in enumerate(self.arcs):
            flow_vars[idx] = model.addVar(
                lb=0.0,
                ub=arc['capacity'],
                name=f"flow_{arc['from']}_{arc['to']}",
                vtype=GRB.CONTINUOUS
            )
        
        self.progress.emit(50)
        
        # Fonction objectif
        objective = gp.quicksum(
            arc['cost'] * flow_vars[idx] 
            for idx, arc in enumerate(self.arcs)
        )
        model.setObjective(objective, GRB.MINIMIZE)
        
        # Contraintes de conservation
        for node in self.nodes:
            node_id = node['id']
            
            outflow = gp.quicksum(
                flow_vars[idx] 
                for idx, arc in enumerate(self.arcs) 
                if arc['from'] == node_id
            )
            
            inflow = gp.quicksum(
                flow_vars[idx] 
                for idx, arc in enumerate(self.arcs) 
                if arc['to'] == node_id
            )
            
            model.addConstr(
                outflow - inflow == node['supply'],
                name=f"conservation_{node_id}"
            )
        
        self.progress.emit(70)
        model.optimize()
        self.progress.emit(90)
        
        # Extraction des résultats
        if model.status == GRB.OPTIMAL:
            flows = [flow_vars[idx].X for idx in range(len(self.arcs))]
            
            arc_details = []
            for idx, arc in enumerate(self.arcs):
                from_name = next(n['name'] for n in self.nodes if n['id'] == arc['from'])
                to_name = next(n['name'] for n in self.nodes if n['id'] == arc['to'])
                
                arc_details.append({
                    'from': from_name,
                    'to': to_name,
                    'flow': flows[idx],
                    'capacity': arc['capacity'],
                    'cost': arc['cost'],
                    'total_cost': flows[idx] * arc['cost']
                })
            
            return {
                'status': 'optimal',
                'objective': model.objVal,
                'flows': flows,
                'arc_details': arc_details
            }
        else:
            return {
                'status': 'infeasible',
                'message': f"Statut: {model.status}"
            }
