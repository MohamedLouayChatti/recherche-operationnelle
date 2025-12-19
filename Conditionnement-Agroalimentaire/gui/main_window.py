"""
Interface graphique principale pour l'équilibrage de chaîne de montage
"""

import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog,
                             QMessageBox, QGroupBox, QTabWidget, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import os
import sys

# Ajouter le chemin parent pour l'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solver.optimizer import AssemblyLineOptimizer
from gui.visualization import SolutionVisualizer


class OptimizationThread(QThread):
    """Thread pour exécuter l'optimisation sans bloquer l'UI"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, optimizer, time_limit):
        super().__init__()
        self.optimizer = optimizer
        self.time_limit = time_limit
        
    def run(self):
        try:
            solution = self.optimizer.solve(self.time_limit)
            if solution:
                self.finished.emit(solution)
            else:
                self.error.emit("Aucune solution trouvée")
        except Exception as e:
            self.error.emit(f"Erreur: {str(e)}")


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.optimizer = None
        self.solution = None
        self.data = None
        self.opt_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Équilibrage de Chaîne de Montage - Agroalimentaire")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Titre
        title = QLabel("Optimisation d'Équilibrage de Chaîne de Montage")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Onglets
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Onglet 1: Données
        tab_data = self.create_data_tab()
        tabs.addTab(tab_data, "Données")
        
        # Onglet 2: Paramètres
        tab_params = self.create_params_tab()
        tabs.addTab(tab_params, "Paramètres")
        
        # Onglet 3: Résultats
        tab_results = self.create_results_tab()
        tabs.addTab(tab_results, "Résultats")
        
        # Barre de contrôle
        control_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("Charger Scénario")
        self.btn_load.clicked.connect(self.load_scenario)
        control_layout.addWidget(self.btn_load)
        
        self.btn_solve = QPushButton("Optimiser")
        self.btn_solve.clicked.connect(self.run_optimization)
        self.btn_solve.setEnabled(False)
        self.btn_solve.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        control_layout.addWidget(self.btn_solve)
        
        self.btn_export = QPushButton("Exporter Solution")
        self.btn_export.clicked.connect(self.export_solution)
        self.btn_export.setEnabled(False)
        control_layout.addWidget(self.btn_export)
        
        control_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(control_layout)
        
        # Barre de statut
        self.statusBar().showMessage("Prêt")
        
    def create_data_tab(self):
        """Crée l'onglet de saisie des données"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info scénario
        info_group = QGroupBox("Informations du Scénario")
        info_layout = QVBoxLayout()
        self.scenario_name = QLabel("Aucun scénario chargé")
        self.scenario_name.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addWidget(self.scenario_name)
        self.scenario_desc = QLabel("")
        info_layout.addWidget(self.scenario_desc)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Tableau des tâches
        tasks_group = QGroupBox("Tâches de Production")
        tasks_layout = QVBoxLayout()
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(
            ["ID", "Nom Tâche", "Durée (s)", "Prérequis", "Pénibilité"]
        )
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        tasks_layout.addWidget(self.tasks_table)
        
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)
        
        return widget
    
    def create_params_tab(self):
        """Crée l'onglet des paramètres"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Paramètres de la ligne
        line_group = QGroupBox("Paramètres de la Ligne de Production")
        line_layout = QVBoxLayout()
        
        # Nombre de postes
        postes_layout = QHBoxLayout()
        postes_layout.addWidget(QLabel("Nombre de postes de travail:"))
        self.spin_postes = QSpinBox()
        self.spin_postes.setRange(1, 20)
        self.spin_postes.setValue(4)
        postes_layout.addWidget(self.spin_postes)
        postes_layout.addStretch()
        line_layout.addLayout(postes_layout)
        
        # Temps de cycle max
        cycle_layout = QHBoxLayout()
        cycle_layout.addWidget(QLabel("Temps de cycle maximum (s):"))
        self.spin_cycle = QSpinBox()
        self.spin_cycle.setRange(10, 500)
        self.spin_cycle.setValue(60)
        cycle_layout.addWidget(self.spin_cycle)
        cycle_layout.addStretch()
        line_layout.addLayout(cycle_layout)
        
        line_group.setLayout(line_layout)
        layout.addWidget(line_group)
        
        # Paramètres solveur
        solver_group = QGroupBox("Paramètres du Solveur Gurobi")
        solver_layout = QVBoxLayout()
        
        # Temps limite
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Temps limite d'optimisation (s):"))
        self.spin_time = QSpinBox()
        self.spin_time.setRange(10, 3600)
        self.spin_time.setValue(300)
        time_layout.addWidget(self.spin_time)
        time_layout.addStretch()
        solver_layout.addLayout(time_layout)
        
        solver_group.setLayout(solver_layout)
        layout.addWidget(solver_group)
        
        layout.addStretch()
        return widget
    
    def create_results_tab(self):
        """Crée l'onglet des résultats"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistiques
        stats_group = QGroupBox("Statistiques de la Solution")
        stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Affectations
        affectation_group = QGroupBox("Affectation des Tâches aux Postes")
        affectation_layout = QVBoxLayout()
        self.affectation_table = QTableWidget()
        self.affectation_table.setColumnCount(5)
        self.affectation_table.setHorizontalHeaderLabels(
            ["Poste", "Tâches", "Charge (s)", "Pénibilité", "Utilisation (%)"]
        )
        affectation_layout.addWidget(self.affectation_table)
        affectation_group.setLayout(affectation_layout)
        layout.addWidget(affectation_group)
        
        # Visualisation
        viz_group = QGroupBox("Visualisation Graphique")
        viz_layout = QVBoxLayout()
        self.viz_canvas = SolutionVisualizer()
        viz_layout.addWidget(self.viz_canvas)
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        return widget
    
    def load_scenario(self):
        """Charge un scénario depuis un fichier JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Charger un scénario", "data/",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                
                self.display_scenario_data()
                self.btn_solve.setEnabled(True)
                self.statusBar().showMessage(f"Scénario chargé: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur de chargement: {str(e)}")
    
    def display_scenario_data(self):
        """Affiche les données du scénario chargé"""
        # Info
        self.scenario_name.setText(f"{self.data.get('nom_scenario', 'Sans nom')}")
        self.scenario_desc.setText(self.data.get('description', ''))
        
        # Paramètres
        self.spin_postes.setValue(self.data.get('nombre_postes', 4))
        self.spin_cycle.setValue(self.data.get('temps_cycle_max', 60))
        
        # Tableau des tâches
        taches = self.data['taches']
        self.tasks_table.setRowCount(len(taches))
        
        for i, tache in enumerate(taches):
            self.tasks_table.setItem(i, 0, QTableWidgetItem(str(tache['id'])))
            self.tasks_table.setItem(i, 1, QTableWidgetItem(tache['nom']))
            self.tasks_table.setItem(i, 2, QTableWidgetItem(str(tache['duree'])))
            
            prerequis = ", ".join(map(str, tache['prerequis'])) if tache['prerequis'] else "-"
            self.tasks_table.setItem(i, 3, QTableWidgetItem(prerequis))
            
            penibilite = str(tache.get('penibilite', 0))
            self.tasks_table.setItem(i, 4, QTableWidgetItem(penibilite))
        
        self.tasks_table.resizeColumnsToContents()
    
    def run_optimization(self):
        """Lance l'optimisation dans un thread séparé"""
        if not self.data:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord charger un scénario")
            return
        
        # Mise à jour des paramètres
        self.data['nombre_postes'] = self.spin_postes.value()
        self.data['temps_cycle_max'] = self.spin_cycle.value()
        
        # Désactiver les contrôles
        self.btn_solve.setEnabled(False)
        self.btn_load.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.statusBar().showMessage("Optimisation en cours...")
        
        # Créer l'optimiseur
        self.optimizer = AssemblyLineOptimizer(self.data)
        
        # Lancer dans un thread
        self.opt_thread = OptimizationThread(self.optimizer, self.spin_time.value())
        self.opt_thread.finished.connect(self.on_optimization_finished)
        self.opt_thread.error.connect(self.on_optimization_error)
        self.opt_thread.start()
    
    def on_optimization_finished(self, solution):
        """Callback quand l'optimisation est terminée"""
        self.solution = solution
        self.display_solution(solution)
        
        # Réactiver les contrôles
        self.btn_solve.setEnabled(True)
        self.btn_load.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Optimisation terminée avec succès ✓")
        
        QMessageBox.information(self, "Succès", 
                               f"Optimisation terminée!\n"
                               f"Temps de cycle: {solution['temps_cycle']:.1f}s\n"
                               f"Efficacité: {solution['efficacite']:.1f}%")
    
    def on_optimization_error(self, error_msg):
        """Callback en cas d'erreur"""
        self.btn_solve.setEnabled(True)
        self.btn_load.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Erreur d'optimisation")
        
        QMessageBox.critical(self, "Erreur", error_msg)
    
    def display_solution(self, solution):
        """Affiche la solution obtenue"""
        # Statistiques
        stats = f"""
╔══════════════════════════════════════════════════════════╗
║           RÉSULTATS D'OPTIMISATION                       ║
╚══════════════════════════════════════════════════════════╝

Temps de cycle optimal: {solution['temps_cycle']:.2f} secondes
Efficacité de la ligne: {solution['efficacite']:.2f} %
Valeur objectif: {solution['objectif']:.4f}
Gap d'optimalité: {solution['gap']*100:.2f} %
Temps de résolution: {solution['temps_resolution']:.2f} secondes
Nombre de postes: {solution['n_postes']}
        """
        self.stats_text.setPlainText(stats)
        
        # Tableau d'affectation
        affectations = solution['affectations']
        charges = solution['charges']
        temps_cycle = solution['temps_cycle']
        
        self.affectation_table.setRowCount(len(affectations))
        
        for idx, (poste, taches) in enumerate(affectations.items()):
            # Poste
            self.affectation_table.setItem(idx, 0, 
                QTableWidgetItem(f"Poste {poste}"))
            
            # Tâches
            taches_str = "\n".join([f"• {t['nom']} ({t['duree']}s)" 
                                   for t in taches])
            self.affectation_table.setItem(idx, 1, 
                QTableWidgetItem(taches_str))
            
            # Charge
            charge = charges[poste]
            self.affectation_table.setItem(idx, 2, 
                QTableWidgetItem(f"{charge:.1f}"))
            
            # Pénibilité
            penibilite = sum(t['penibilite'] for t in taches)
            self.affectation_table.setItem(idx, 3, 
                QTableWidgetItem(str(penibilite)))
            
            # Utilisation
            utilisation = (charge / temps_cycle) * 100
            self.affectation_table.setItem(idx, 4, 
                QTableWidgetItem(f"{utilisation:.1f}%"))
        
        self.affectation_table.resizeColumnsToContents()
        self.affectation_table.resizeRowsToContents()
        
        # Visualisation
        self.viz_canvas.plot_solution(solution)
    
    def export_solution(self):
        """Exporte la solution en JSON"""
        if not self.solution:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la solution", "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.solution, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Succès", 
                                       f"Solution exportée vers:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", 
                                    f"Erreur d'export: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())