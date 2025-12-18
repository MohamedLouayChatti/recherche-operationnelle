# backend/network.py

class NetworkData:
    def __init__(
        self,
        C_N=500,
        C_S=800,
        D=180,
        M=0.5,
        nodes=None,
        arcs=None
    ):
        """
        arcs doit être une liste de tuples :
        (start_node, end_node, type, capacity)

        type ∈ { "N", "S", "T" }
        """

        # --- Paramètres économiques ---
        self.C_N = C_N      # Coût capacité normale
        self.C_S = C_S      # Coût surcharge
        self.D = D          # Demande totale
        self.M = M          # Ratio X_S ≤ M * X_N

        # --- Nœuds du réseau ---
        self.nodes = nodes if nodes is not None else []

        # --- Arcs du réseau ---
        # Chaque arc : (i, j, type, capacity)
        if arcs is None:
            self.arcs = []
        else:
            self.arcs = arcs

        # --- Classification des arcs par type ---
        self.normal_arcs = [(i, j, c) for i, j, t, c in self.arcs if t == "N"]
        self.surcharge_arcs = [(i, j, c) for i, j, t, c in self.arcs if t == "S"]
        self.total_arcs = [(i, j, c) for i, j, t, c in self.arcs if t == "T"]
