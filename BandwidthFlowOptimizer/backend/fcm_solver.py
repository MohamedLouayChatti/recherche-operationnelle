# backend/fcm_solver.py

import gurobipy as gp
from gurobipy import GRB


class FCMSolver:

    def __init__(self, data):
        self.data = data
        self.model = gp.Model("FCM")
        self.model.setParam('OutputFlag', 0)

        # Variables
        self.X_N = self.model.addVar(name="X_N", lb=0)
        self.X_S = self.model.addVar(name="X_S", lb=0)
        self.X_T = self.model.addVar(name="X_T", lb=0)

    def build_model(self):
        d = self.data

        # Capacités totales selon le type d'arc
        cap_N = sum(cap for (_, _, cap) in d.normal_arcs)
        cap_S = sum(cap for (_, _, cap) in d.surcharge_arcs)
        cap_T = sum(cap for (_, _, cap) in d.total_arcs)

        # Contraintes
        self.model.addConstr(self.X_T == self.X_N + self.X_S, "flux_conservation")
        self.model.addConstr(self.X_N <= cap_N, "cap_normale")
        self.model.addConstr(self.X_S <= cap_S, "cap_surcharge")
        self.model.addConstr(self.X_T <= cap_T, "cap_totale")
        self.model.addConstr(self.X_S <= d.M * self.X_N, "ratio_M")
        self.model.addConstr(self.X_T >= d.D, "demande")

        # Fonction objectif
        self.model.setObjective(
            d.C_N * self.X_N + d.C_S * self.X_S,
            GRB.MINIMIZE
        )

    def solve(self):
        self.build_model()
        self.model.optimize()

        if self.model.Status != GRB.OPTIMAL:
            return None

        return {
            "cost": self.model.objVal,
            "X_N": self.X_N.X,
            "X_S": self.X_S.X,
            "X_T": self.X_T.X,
        }


def solve_fcm(data):
    solver = FCMSolver(data)
    return solver.solve()
