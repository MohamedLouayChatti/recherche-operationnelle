# =============================================================================
# gui/main_window.py - Fenêtre principale (partie 1/2)
# =============================================================================

import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from solver.optimizer import OptimizationThread
from gui.graph_canvas import GraphCanvas

class MainWindow(QMainWindow):
    """Fenêtre principale"""
    
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.arcs = []
        self.results = None
        self.init_ui()
        self.load_default_data()
        
    def init_ui(self):
        """Interface utilisateur"""
        self.setWindowTitle("Flux de Pollution - Système Hydrique")
        self.setGeometry(100, 100, 1400, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Partie gauche
        tabs = QTabWidget()
        tabs.addTab(self.create_graph_tab(), "📊 Graphe")
        tabs.addTab(self.create_nodes_tab(), "🔵 Nœuds")
        tabs.addTab(self.create_arcs_tab(), "➡️ Arcs")
        tabs.addTab(self.create_model_tab(), "📐 Modèle")
        main_layout.addWidget(tabs, stretch=2)
        
        # Partie droite
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        # Boutons
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        self.solve_btn = QPushButton("🚀 Résoudre")
        self.solve_btn.clicked.connect(self.solve_optimization)
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6; color: white;
                padding: 12px; font-size: 14px;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #2563EB; }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        export_btn = QPushButton("💾 Exporter")
        export_btn.clicked.connect(self.export_data)
        
        import_btn = QPushButton("📂 Importer")
        import_btn.clicked.connect(self.import_data)
        
        action_layout.addWidget(self.solve_btn)
        action_layout.addWidget(self.progress_bar)
        action_layout.addWidget(export_btn)
        action_layout.addWidget(import_btn)
        action_group.setLayout(action_layout)
        right_layout.addWidget(action_group)
        
        # Résultats
        results_group = QGroupBox("Résultats")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        right_layout.addWidget(results_group)
        
        main_layout.addWidget(right, stretch=1)
    
    def create_graph_tab(self):
        """Onglet graphe"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.graph_canvas = GraphCanvas()
        layout.addWidget(self.graph_canvas)
        return tab
    
    def create_nodes_tab(self):
        """Onglet nœuds"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("➕ Ajouter", clicked=self.add_node))
        btn_layout.addWidget(QPushButton("🗑️ Supprimer", clicked=self.delete_node))
        layout.addLayout(btn_layout)
        
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(4)
        self.nodes_table.setHorizontalHeaderLabels(
            ["Nom", "Type", "Offre/Demande", "Pos X"]
        )
        layout.addWidget(self.nodes_table)
        return tab
    
    def create_arcs_tab(self):
        """Onglet arcs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("➕ Ajouter", clicked=self.add_arc))
        btn_layout.addWidget(QPushButton("🗑️ Supprimer", clicked=self.delete_arc))
        layout.addLayout(btn_layout)
        
        self.arcs_table = QTableWidget()
        self.arcs_table.setColumnCount(4)
        self.arcs_table.setHorizontalHeaderLabels(
            ["De", "Vers", "Coût", "Capacité"]
        )
        layout.addWidget(self.arcs_table)
        return tab
    
    def create_model_tab(self):
        """Onglet modèle"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Modèle Mathématique</h2>
        <h3>Variables</h3>
        <p><b>x<sub>ij</sub></b> : Flux sur arc (i,j)</p>
        
        <h3>Objectif</h3>
        <p style="background: #E0F2FE; padding: 10px;">
        <b>min Σ c<sub>ij</sub> · x<sub>ij</sub></b></p>
        
        <h3>Contraintes</h3>
        <p><b>Conservation:</b> Σx<sub>ij</sub> - Σx<sub>ji</sub> = b<sub>i</sub></p>
        <p><b>Capacité:</b> 0 ≤ x<sub>ij</sub> ≤ u<sub>ij</sub></p>
        <p><b>Équilibre:</b> Σb<sub>i</sub> = 0</p>
        """)
        layout.addWidget(text)
        return tab
    
    def load_default_data(self):
        """Données par défaut"""
        self.nodes = [
            {'id': 0, 'name': 'Source Usine', 'type': 'source', 
             'supply': 100, 'x': 1, 'y': 2},
            {'id': 1, 'name': 'Station 1', 'type': 'intermediate', 
             'supply': 0, 'x': 3, 'y': 1},
            {'id': 2, 'name': 'Station 2', 'type': 'intermediate', 
             'supply': 0, 'x': 3, 'y': 3},
            {'id': 3, 'name': 'Traitement', 'type': 'sink', 
             'supply': -100, 'x': 5, 'y': 2}
        ]
        
        self.arcs = [
            {'from': 0, 'to': 1, 'cost': 2.0, 'capacity': 60.0},
            {'from': 0, 'to': 2, 'cost': 3.0, 'capacity': 50.0},
            {'from': 1, 'to': 3, 'cost': 1.0, 'capacity': 70.0},
            {'from': 2, 'to': 3, 'cost': 2.0, 'capacity': 60.0}
        ]
        
        self.update_tables()
        self.update_graph()
    
    def solve_optimization(self):
        """Lance Gurobi"""
        total = sum(n['supply'] for n in self.nodes)
        if abs(total) > 0.001:
            QMessageBox.warning(self, "Erreur", 
                f"Somme offres/demandes ≠ 0 ({total:.2f})")
            return
        
        self.solve_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.opt_thread = OptimizationThread(self.nodes, self.arcs)
        self.opt_thread.finished.connect(self.on_finished)
        self.opt_thread.error.connect(self.on_error)
        self.opt_thread.progress.connect(self.progress_bar.setValue)
        self.opt_thread.start()
    
    def on_finished(self, results):
        """Affiche résultats"""
        self.results = results
        self.solve_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if results['status'] == 'optimal':
            text = f"✅ <b>Optimal</b><br><br>"
            text += f"<b>Coût:</b> {results['objective']:.2f} €<br><br>"
            
            for d in results['arc_details']:
                if d['flow'] > 0.01:
                    text += f"<b>{d['from']} → {d['to']}</b><br>"
                    text += f"Flux: {d['flow']:.2f}/{d['capacity']:.0f}<br>"
                    text += f"Coût: {d['total_cost']:.2f} €<br><br>"
            
            self.results_text.setHtml(text)
            self.update_graph()
        else:
            self.results_text.setHtml("❌ <b>Pas de solution</b>")
    
    def on_error(self, error):
        """Erreur"""
        QMessageBox.critical(self, "Erreur", error)
        self.solve_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def export_data(self):
        """Export JSON"""
        fname, _ = QFileDialog.getSaveFileName(
            self, "Exporter", "", "JSON (*.json)"
        )
        if fname:
            with open(fname, 'w') as f:
                json.dump({'nodes': self.nodes, 'arcs': self.arcs}, f, indent=2)
    
    def import_data(self):
        """Import JSON"""
        fname, _ = QFileDialog.getOpenFileName(
            self, "Importer", "", "JSON (*.json)"
        )
        if fname:
            with open(fname) as f:
                data = json.load(f)
                self.nodes = data['nodes']
                self.arcs = data['arcs']
                self.update_tables()
                self.update_graph()
    
    # Méthodes de gestion des tables
    def update_tables(self):
        """Met à jour les tables de nœuds et d'arcs"""
        # Table des nœuds
        self.nodes_table.setRowCount(len(self.nodes))
        for i, node in enumerate(self.nodes):
            self.nodes_table.setItem(i, 0, QTableWidgetItem(node['name']))
            self.nodes_table.setItem(i, 1, QTableWidgetItem(node['type']))
            self.nodes_table.setItem(i, 2, QTableWidgetItem(str(node['supply'])))
            self.nodes_table.setItem(i, 3, QTableWidgetItem(str(node.get('x', 0))))
        
        # Table des arcs
        self.arcs_table.setRowCount(len(self.arcs))
        for i, arc in enumerate(self.arcs):
            from_name = next(n['name'] for n in self.nodes if n['id'] == arc['from'])
            to_name = next(n['name'] for n in self.nodes if n['id'] == arc['to'])
            self.arcs_table.setItem(i, 0, QTableWidgetItem(from_name))
            self.arcs_table.setItem(i, 1, QTableWidgetItem(to_name))
            self.arcs_table.setItem(i, 2, QTableWidgetItem(str(arc['cost'])))
            self.arcs_table.setItem(i, 3, QTableWidgetItem(str(arc['capacity'])))
    
    def update_graph(self):
        """Met à jour la visualisation du graphe"""
        flows = self.results['flows'] if self.results else None
        self.graph_canvas.plot_graph(self.nodes, self.arcs, flows)
    
    def add_node(self):
        """Ajoute un nouveau nœud"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un nœud")
        layout = QFormLayout(dialog)
        
        name_input = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(['source', 'intermediate', 'sink'])
        supply_input = QLineEdit("0")
        x_input = QLineEdit("0")
        y_input = QLineEdit("0")
        
        layout.addRow("Nom:", name_input)
        layout.addRow("Type:", type_combo)
        layout.addRow("Offre/Demande:", supply_input)
        layout.addRow("Position X:", x_input)
        layout.addRow("Position Y:", y_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            new_id = max([n['id'] for n in self.nodes], default=-1) + 1
            self.nodes.append({
                'id': new_id,
                'name': name_input.text(),
                'type': type_combo.currentText(),
                'supply': float(supply_input.text()),
                'x': float(x_input.text()),
                'y': float(y_input.text())
            })
            self.update_tables()
            self.update_graph()
    
    def delete_node(self):
        """Supprime le nœud sélectionné"""
        row = self.nodes_table.currentRow()
        if row >= 0:
            node_id = self.nodes[row]['id']
            # Supprimer les arcs liés
            self.arcs = [a for a in self.arcs if a['from'] != node_id and a['to'] != node_id]
            # Supprimer le nœud
            del self.nodes[row]
            self.update_tables()
            self.update_graph()
    
    def add_arc(self):
        """Ajoute un nouvel arc"""
        if len(self.nodes) < 2:
            QMessageBox.warning(self, "Erreur", "Il faut au moins 2 nœuds pour créer un arc")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un arc")
        layout = QFormLayout(dialog)
        
        from_combo = QComboBox()
        to_combo = QComboBox()
        for node in self.nodes:
            from_combo.addItem(node['name'], node['id'])
            to_combo.addItem(node['name'], node['id'])
        
        cost_input = QLineEdit("1.0")
        capacity_input = QLineEdit("100.0")
        
        layout.addRow("De:", from_combo)
        layout.addRow("Vers:", to_combo)
        layout.addRow("Coût:", cost_input)
        layout.addRow("Capacité:", capacity_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            self.arcs.append({
                'from': from_combo.currentData(),
                'to': to_combo.currentData(),
                'cost': float(cost_input.text()),
                'capacity': float(capacity_input.text())
            })
            self.update_tables()
            self.update_graph()
    
    def delete_arc(self):
        """Supprime l'arc sélectionné"""
        row = self.arcs_table.currentRow()
        if row >= 0:
            del self.arcs[row]
            self.update_tables()
            self.update_graph()