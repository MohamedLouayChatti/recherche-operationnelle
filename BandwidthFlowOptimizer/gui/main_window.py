# gui/main_window.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QTextEdit, QTabWidget
)

from backend.network import NetworkData
from backend.fcm_solver import solve_fcm


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation FCM - Bande Passante")
        self.setMinimumWidth(750) 
        
        # --- STYLES GLOBALES (Palette DARK MODE) ---
        # Fond: Gris très foncé (#2c3e50)
        # Texte: Blanc cassé (#ecf0f1)
        # Accentuation: Bleu vif (#3498db) et Orange foncé pour le bouton
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50; /* Gris très foncé (Bleu nuit) */
                color: #ecf0f1; /* Blanc cassé */
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 10pt;
            }
            QGroupBox {
                font-size: 11pt;
                font-weight: bold;
                margin-top: 10px;
                border: 2px solid #34495e; /* Bordure un peu plus claire que le fond */
                border-radius: 6px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #ffffff; /* Titres en blanc */
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #7f8c8d; /* Bordure gris neutre */
                border-radius: 4px;
                background-color: #34495e; /* Fond des champs de saisie plus foncé */
                color: #ecf0f1; /* Texte de saisie en blanc cassé */
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #3498db; /* Bleu accentuation au focus */
            }
            QLabel {
                padding-top: 5px;
                padding-bottom: 2px;
            }
            QTabWidget::pane { /* The tab widget frame */
                border-top: 2px solid #3498db; 
                background-color: #34495e; /* Fond des onglets */
            }
            QTabBar::tab {
                background: #34495e; /* Fond des onglets inactifs */
                color: #bdc3c7; /* Texte gris clair */
                border: 1px solid #34495e;
                border-bottom: 1px solid #3498db; /* Séparation */
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2c3e50; /* Fond de l'onglet actif */
                border: 1px solid #3498db;
                border-bottom-color: #2c3e50; /* Fusionne avec le fond */
                color: #ffffff;
                font-weight: bold;
            }
        """)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        tabs = QTabWidget()

        # ----------------------------------------------------------------------
        #   ONGLET 1 : PARAMÈTRES GÉNÉRAUX
        # ----------------------------------------------------------------------
        tab_params = QWidget()
        layout_params = QVBoxLayout()

        # --- Coûts ---
        group_costs = QGroupBox("💸 Coûts")
        layout_costs = QVBoxLayout()

        layout_costs.addWidget(QLabel("Coût Bande Normale (C_N) :"))
        self.input_CN = QLineEdit("500")
        layout_costs.addWidget(self.input_CN)

        layout_costs.addWidget(QLabel("Coût Surcharge (C_S) :"))
        self.input_CS = QLineEdit("800")
        layout_costs.addWidget(self.input_CS)

        group_costs.setLayout(layout_costs)
        layout_params.addWidget(group_costs)

        # --- Demande & capacités globales ---
        group_capacity = QGroupBox("📊 Demande et Contraintes")
        layout_capacity = QVBoxLayout()

        layout_capacity.addWidget(QLabel("Demande totale D (en Gbps) :"))
        self.input_D = QLineEdit("180")
        layout_capacity.addWidget(self.input_D)

        layout_capacity.addWidget(QLabel("Ratio surcharge M (X_S ≤ M × X_N) :"))
        self.input_M = QLineEdit("0.5")
        layout_capacity.addWidget(self.input_M)

        group_capacity.setLayout(layout_capacity)
        layout_params.addWidget(group_capacity)

        layout_params.addStretch()
        tab_params.setLayout(layout_params)

        # ----------------------------------------------------------------------
        #   ONGLET 2 : NŒUDS + ARCS AVEC CAPACITÉS
        # ----------------------------------------------------------------------
        tab_network = QWidget()
        layout_network = QVBoxLayout()

        # --- NŒuds ---
        group_nodes = QGroupBox("📍 Nœuds du réseau")
        layout_nodes = QVBoxLayout()

        layout_nodes.addWidget(QLabel("Liste des nœuds (séparés par des virgules) :"))
        self.input_nodes = QLineEdit("s, r, d")
        layout_nodes.addWidget(self.input_nodes)

        group_nodes.setLayout(layout_nodes)
        layout_network.addWidget(group_nodes)

        # --- Arcs ---
        group_arcs = QGroupBox("🔗 Arcs du réseau (avec capacités)")
        layout_arcs = QVBoxLayout()

        explanation = QLabel(
            "Format : noeud_départ, noeud_arrivée, type, capacité_max\n"
            "Types possibles : **N** = Normal, **S** = Surcharge, **T** = Transmission totale\n\n"
            "Exemple :\n"
            "s, r, N, 200\n"
            "s, r, S, 100\n"
            "r, d, T, 300"
        )
        # Style pour l'explication en mode sombre
        explanation.setStyleSheet("""
            QLabel {
                color: #bdc3c7; /* Gris clair */
                font-style: italic;
                padding: 10px;
                border-left: 3px solid #3498db; 
                background-color: #34495e; /* Fond légèrement plus clair que la fenêtre */
                border-radius: 4px;
            }
        """)
        layout_arcs.addWidget(explanation)

        self.input_arcs = QTextEdit()
        self.input_arcs.setPlainText("s, r, N, 200\ns, r, S, 100\nr, d, T, 300")
        self.input_arcs.setMaximumHeight(180)
        layout_arcs.addWidget(self.input_arcs)

        group_arcs.setLayout(layout_arcs)
        layout_network.addWidget(group_arcs)

        layout_network.addStretch()
        tab_network.setLayout(layout_network)

        # Onglets
        tabs.addTab(tab_params, "⚙️ Paramètres Généraux")
        tabs.addTab(tab_network, "🗺️ Structure du Réseau")

        main_layout.addWidget(tabs)

        # ----------------------------------------------------------------------
        #   BOUTON RÉSOUDRE
        # ----------------------------------------------------------------------
        btn_solve = QPushButton("🚀 RÉSOUDRE AVEC GUROBI")
        btn_solve.clicked.connect(self.solve_model)
        # Style du bouton mis à jour pour l'orange foncé
        btn_solve.setStyleSheet("""
            QPushButton {
                padding: 16px;
                font-size: 16px;
                font-weight: bold;
                background-color: #d35400; /* Deep Orange / Burnt Orange */
                color: white;
                border: none;
                border-radius: 8px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.4);
            }
            QPushButton:hover {
                background-color: #e67e22; /* Orange plus clair au survol */
            }
            QPushButton:pressed {
                background-color: #c0392b; /* Rouge brique au clic */
            }
        """)
        main_layout.addWidget(btn_solve)

        self.setLayout(main_layout)

    # ----------------------------------------------------------------------
    # PARSING DES DONNÉES
    # ----------------------------------------------------------------------

    def parse_nodes(self):
        return [
            n.strip() for n in self.input_nodes.text().split(',')
            if n.strip()
        ]

    def parse_arcs(self):
        arcs = []
        for line in self.input_arcs.toPlainText().strip().split("\n"):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split(",")]

            if len(parts) != 4:
                raise ValueError(
                    f"Format incorrect pour : {line}\n"
                    "Format attendu : start, end, type, capacity"
                )

            start, end, arc_type, cap = parts

            if arc_type not in ("N", "S", "T"):
                raise ValueError(
                    f"Type invalide dans : {line}\n"
                    "Types acceptés : N, S, T"
                )

            arcs.append((start, end, arc_type, float(cap)))

        return arcs

    # ----------------------------------------------------------------------
    # RÉSOLUTION DU MODÈLE
    # ----------------------------------------------------------------------
    def solve_model(self):
        try:
            # Lecture des nœuds & arcs
            nodes = self.parse_nodes()
            arcs = self.parse_arcs()

            data = NetworkData(
                C_N=float(self.input_CN.text()),
                C_S=float(self.input_CS.text()),
                D=float(self.input_D.text()),
                M=float(self.input_M.text()),
                nodes=nodes,
                arcs=arcs
            )

            result = solve_fcm(data)

            if result is None:
                QMessageBox.warning(
                    self, 
                    "⚠️ Échec de la Résolution", 
                    "Aucune solution optimale trouvée pour le modèle donné."
                )
                return

            text = f"""
**✅ Solution optimale trouvée !**

---

### 💰 Coût Total Optimal
**{result['cost']:.2f} TND**

---

### 📡 Flux Optimaux
* **Flux Normal (X_N)** : **{result['X_N']:.2f} Gbps**
* **Flux Surcharge (X_S)** : **{result['X_S']:.2f} Gbps**
* **Flux Total (X_T)** : **{result['X_T']:.2f} Gbps**

---

### 🕸 Détails du Réseau
* **Nœuds** : {', '.join(nodes)}
* **Arcs configurés** : {len(arcs)}
"""

            # Style du message en mode sombre
            msg = QMessageBox(self)
            msg.setWindowTitle("Résultat de l'Optimisation")
            msg.setText(text)
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet("""
                QMessageBox { 
                    background-color: #34495e; /* Fond sombre */
                    color: #ecf0f1; /* Texte clair */
                }
                QLabel { 
                    font-size: 10pt;
                    color: #ecf0f1;
                }
            """)
            msg.exec()


        except ValueError as ve:
            QMessageBox.critical(self, "❌ Erreur de Format des Données", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "🔥 Erreur Critique", f"Une erreur inattendue est survenue:\n{str(e)}")