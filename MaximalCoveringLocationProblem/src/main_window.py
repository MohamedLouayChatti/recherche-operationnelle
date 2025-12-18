"""
Interface graphique principale pour l'application de Couverture Maximale.

Cette interface permet de:
- Saisir les paramètres du problème
- Lancer l'optimisation de manière non-bloquante (QThread)
- Visualiser les résultats graphiquement
- Exporter les résultats
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QTabWidget, QTextEdit, QGroupBox, QComboBox,
    QMessageBox, QProgressBar, QFileDialog, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import numpy as np
import json
from datetime import datetime

from src.optimization_model import MaximalCoveringLocationModel
from src.visualization import CoverageVisualizer


class OptimizationThread(QThread):
    """Thread pour exécuter l'optimisation sans bloquer l'interface."""
    
    finished = pyqtSignal(bool, dict)
    progress = pyqtSignal(str)
    
    def __init__(self, model, time_limit, gap):
        super().__init__()
        self.model = model
        self.time_limit = time_limit
        self.gap = gap
    
    def run(self):
        """Exécute l'optimisation dans un thread séparé."""
        try:
            self.progress.emit("Construction du modèle...")
            # Activer les diagnostics pour le débogage
            success = self.model.build_model(enable_diagnostics=True)
            
            if not success:
                self.finished.emit(False, {})
                return
            
            self.progress.emit("Résolution en cours...")
            success = self.model.solve(time_limit=self.time_limit, gap=self.gap)
            
            if success:
                self.progress.emit("Solution trouvée!")
                solution = self.model.get_detailed_solution()
                self.finished.emit(True, solution)
            else:
                self.progress.emit("Aucune solution trouvée.")
                self.finished.emit(False, {})
                
        except Exception as e:
            self.progress.emit(f"Erreur: {str(e)}")
            self.finished.emit(False, {})


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""
    
    def __init__(self):
        super().__init__()
        self.model = MaximalCoveringLocationModel()
        self.visualizer = CoverageVisualizer()
        self.current_solution = None
        self.optimization_thread = None
        
        self.init_ui()
        self.load_default_data()
        
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        self.setWindowTitle("Couverture Maximale - Positionnement de Caméras de Surveillance")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Titre
        title = QLabel("Problème de Couverture Maximale\nPositionnement Optimal de Caméras de Surveillance")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Tabs pour organiser l'interface
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Tab 1: Configuration
        config_tab = self.create_config_tab()
        tabs.addTab(config_tab, "Configuration des Données")
        
        # Tab 2: Résolution
        solve_tab = self.create_solve_tab()
        tabs.addTab(solve_tab, "Résolution")
        
        # Tab 3: Résultats
        results_tab = self.create_results_tab()
        tabs.addTab(results_tab, "Résultats et Visualisation")
        
        # Barre de statut
        self.statusBar().showMessage("Prêt")
        
    def create_config_tab(self):
        """Crée l'onglet de configuration des données."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Paramètres généraux
        general_group = QGroupBox("Paramètres Généraux")
        general_layout = QVBoxLayout()
        
        params_layout = QHBoxLayout()
        
        # Nombre maximum de caméras
        params_layout.addWidget(QLabel("Nombre max. de caméras:"))
        self.max_cameras_spin = QSpinBox()
        self.max_cameras_spin.setRange(1, 100)
        self.max_cameras_spin.setValue(10)
        params_layout.addWidget(self.max_cameras_spin)
        
        # Budget maximal
        params_layout.addWidget(QLabel("Budget maximal (€):"))
        self.max_budget_spin = QDoubleSpinBox()
        self.max_budget_spin.setRange(1000, 1000000)
        self.max_budget_spin.setValue(50000)
        self.max_budget_spin.setSingleStep(1000)
        params_layout.addWidget(self.max_budget_spin)
        
        # Nombre de zones
        params_layout.addWidget(QLabel("Nombre de zones:"))
        self.n_zones_spin = QSpinBox()
        self.n_zones_spin.setRange(5, 100)
        self.n_zones_spin.setValue(20)
        self.n_zones_spin.valueChanged.connect(self.update_zone_table)
        params_layout.addWidget(self.n_zones_spin)
        
        # Nombre d'emplacements caméras
        params_layout.addWidget(QLabel("Emplacements caméras:"))
        self.n_cameras_spin = QSpinBox()
        self.n_cameras_spin.setRange(5, 100)
        self.n_cameras_spin.setValue(15)
        self.n_cameras_spin.valueChanged.connect(self.update_camera_table)
        params_layout.addWidget(self.n_cameras_spin)
        
        general_layout.addLayout(params_layout)
        
        # Boutons de génération
        buttons_layout = QHBoxLayout()
        
        gen_random_btn = QPushButton("Générer Données Aléatoires")
        gen_random_btn.clicked.connect(self.generate_random_data)
        buttons_layout.addWidget(gen_random_btn)
        
        load_btn = QPushButton("Charger depuis Fichier")
        load_btn.clicked.connect(self.load_from_file)
        buttons_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Sauvegarder Données")
        save_btn.clicked.connect(self.save_to_file)
        buttons_layout.addWidget(save_btn)
        
        general_layout.addLayout(buttons_layout)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Tables de données
        tables_splitter = QSplitter(Qt.Horizontal)
        
        # Table des zones
        zones_group = QGroupBox("Zones à Surveiller")
        zones_layout = QVBoxLayout()
        self.zones_table = QTableWidget()
        self.zones_table.setColumnCount(5)
        self.zones_table.setHorizontalHeaderLabels(["X", "Y", "Priorité", "Population", "Description"])
        zones_layout.addWidget(self.zones_table)
        zones_group.setLayout(zones_layout)
        tables_splitter.addWidget(zones_group)
        
        # Table des caméras
        cameras_group = QGroupBox("Emplacements Potentiels de Caméras")
        cameras_layout = QVBoxLayout()
        self.cameras_table = QTableWidget()
        self.cameras_table.setColumnCount(6)
        self.cameras_table.setHorizontalHeaderLabels(["X", "Y", "Coût (€)", "Portée (m)", "Angle (°)", "Type"])
        cameras_layout.addWidget(self.cameras_table)
        cameras_group.setLayout(cameras_layout)
        tables_splitter.addWidget(cameras_group)
        
        layout.addWidget(tables_splitter)
        
        return widget
    
    def create_solve_tab(self):
        """Crée l'onglet de résolution."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Paramètres de résolution
        params_group = QGroupBox("Paramètres du Solveur Gurobi")
        params_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Temps limite (secondes):"))
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(10, 3600)
        self.time_limit_spin.setValue(300)
        row1.addWidget(self.time_limit_spin)
        
        row1.addWidget(QLabel("Gap d'optimalité (%):"))
        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(0.01, 10.0)
        self.gap_spin.setValue(1.0)
        self.gap_spin.setSingleStep(0.1)
        row1.addWidget(self.gap_spin)
        
        params_layout.addLayout(row1)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Bouton de résolution
        self.solve_button = QPushButton("🚀 Lancer l'Optimisation")
        self.solve_button.setStyleSheet("QPushButton { font-size: 14px; padding: 10px; background-color: #4CAF50; color: white; }")
        self.solve_button.clicked.connect(self.start_optimization)
        layout.addWidget(self.solve_button)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Zone de log
        log_group = QGroupBox("Journal d'Exécution")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        return widget
    
    def create_results_tab(self):
        """Crée l'onglet des résultats."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Résumé de la solution
        summary_group = QGroupBox("Résumé de la Solution")
        summary_layout = QVBoxLayout()
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Visualisation
        viz_group = QGroupBox("Visualisation de la Couverture")
        viz_layout = QVBoxLayout()
        
        viz_buttons = QHBoxLayout()
        show_coverage_btn = QPushButton("Afficher Carte de Couverture")
        show_coverage_btn.clicked.connect(self.show_coverage_map)
        viz_buttons.addWidget(show_coverage_btn)
        
        show_heatmap_btn = QPushButton("Afficher Heatmap")
        show_heatmap_btn.clicked.connect(self.show_heatmap)
        viz_buttons.addWidget(show_heatmap_btn)
        
        show_stats_btn = QPushButton("Afficher Statistiques")
        show_stats_btn.clicked.connect(self.show_statistics)
        viz_buttons.addWidget(show_stats_btn)
        
        viz_layout.addLayout(viz_buttons)
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        # Détails de la solution
        details_group = QGroupBox("Détails de la Solution")
        details_layout = QVBoxLayout()
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Boutons d'export
        export_layout = QHBoxLayout()
        export_solution_btn = QPushButton("Exporter Solution (JSON)")
        export_solution_btn.clicked.connect(self.export_solution)
        export_layout.addWidget(export_solution_btn)
        
        export_report_btn = QPushButton("Générer Rapport (TXT)")
        export_report_btn.clicked.connect(self.export_report)
        export_layout.addWidget(export_report_btn)
        
        layout.addLayout(export_layout)
        
        return widget
    
    def load_default_data(self):
        """Charge des données par défaut."""
        self.update_zone_table()
        self.update_camera_table()
        self.generate_random_data()
    
    def update_zone_table(self):
        """Met à jour le nombre de lignes dans la table des zones."""
        n_zones = self.n_zones_spin.value()
        self.zones_table.setRowCount(n_zones)
        
    def update_camera_table(self):
        """Met à jour le nombre de lignes dans la table des caméras."""
        n_cameras = self.n_cameras_spin.value()
        self.cameras_table.setRowCount(n_cameras)
    
    def generate_random_data(self):
        """Génère des données aléatoires pour le problème."""
        n_zones = self.n_zones_spin.value()
        n_cameras = self.n_cameras_spin.value()
        
        # Générer zones aléatoires (coordonnées entre 0 et 1000)
        for i in range(n_zones):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            priority = np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            population = np.random.randint(10, 1000)
            
            descriptions = ["Zone commerciale", "Zone résidentielle", "Zone industrielle", 
                          "Parking", "Entrée principale", "Zone sensible", "Zone publique"]
            description = np.random.choice(descriptions)
            
            self.zones_table.setItem(i, 0, QTableWidgetItem(f"{x:.1f}"))
            self.zones_table.setItem(i, 1, QTableWidgetItem(f"{y:.1f}"))
            self.zones_table.setItem(i, 2, QTableWidgetItem(str(priority)))
            self.zones_table.setItem(i, 3, QTableWidgetItem(str(population)))
            self.zones_table.setItem(i, 4, QTableWidgetItem(description))
        
        # Générer emplacements caméras aléatoires
        camera_types = ["fixe", "PTZ", "thermique", "PTZ", "fixe"]  # Plus de PTZ
        for i in range(n_cameras):
            x = np.random.uniform(0, 1000)
            y = np.random.uniform(0, 1000)
            cost = np.random.uniform(2000, 8000)
            range_m = np.random.uniform(30, 100)
            angle = np.random.choice([90, 180, 270, 360])
            cam_type = np.random.choice(camera_types)
            
            # Les caméras PTZ coûtent plus cher
            if cam_type == "PTZ":
                cost *= 1.5
            elif cam_type == "thermique":
                cost *= 2.0
            
            self.cameras_table.setItem(i, 0, QTableWidgetItem(f"{x:.1f}"))
            self.cameras_table.setItem(i, 1, QTableWidgetItem(f"{y:.1f}"))
            self.cameras_table.setItem(i, 2, QTableWidgetItem(f"{cost:.0f}"))
            self.cameras_table.setItem(i, 3, QTableWidgetItem(f"{range_m:.1f}"))
            self.cameras_table.setItem(i, 4, QTableWidgetItem(f"{angle:.0f}"))
            self.cameras_table.setItem(i, 5, QTableWidgetItem(cam_type))
        
        self.log_message("Données aléatoires générées avec succès.")
    
    def load_from_file(self):
        """Charge les données depuis un fichier JSON."""
        filename, _ = QFileDialog.getOpenFileName(self, "Charger Données", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Charger les paramètres
                self.max_cameras_spin.setValue(data.get('max_cameras', 10))
                self.max_budget_spin.setValue(data.get('max_budget', 50000))
                
                # Charger les zones
                zones = data.get('zones', [])
                self.n_zones_spin.setValue(len(zones))
                self.update_zone_table()
                for i, zone in enumerate(zones):
                    self.zones_table.setItem(i, 0, QTableWidgetItem(str(zone[0])))
                    self.zones_table.setItem(i, 1, QTableWidgetItem(str(zone[1])))
                    self.zones_table.setItem(i, 2, QTableWidgetItem(str(zone[2])))
                    self.zones_table.setItem(i, 3, QTableWidgetItem(str(zone[3])))
                    self.zones_table.setItem(i, 4, QTableWidgetItem(zone[4]))
                
                # Charger les caméras
                cameras = data.get('cameras', [])
                self.n_cameras_spin.setValue(len(cameras))
                self.update_camera_table()
                for i, cam in enumerate(cameras):
                    self.cameras_table.setItem(i, 0, QTableWidgetItem(str(cam[0])))
                    self.cameras_table.setItem(i, 1, QTableWidgetItem(str(cam[1])))
                    self.cameras_table.setItem(i, 2, QTableWidgetItem(str(cam[2])))
                    self.cameras_table.setItem(i, 3, QTableWidgetItem(str(cam[3])))
                    self.cameras_table.setItem(i, 4, QTableWidgetItem(str(cam[4])))
                    self.cameras_table.setItem(i, 5, QTableWidgetItem(cam[5]))
                
                self.log_message(f"Données chargées depuis {filename}")
                QMessageBox.information(self, "Succès", "Données chargées avec succès!")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
    
    def save_to_file(self):
        """Sauvegarde les données dans un fichier JSON."""
        filename, _ = QFileDialog.getSaveFileName(self, "Sauvegarder Données", "", "JSON Files (*.json)")
        if filename:
            try:
                data = {
                    'max_cameras': self.max_cameras_spin.value(),
                    'max_budget': self.max_budget_spin.value(),
                    'zones': [],
                    'cameras': []
                }
                
                # Sauvegarder les zones
                for i in range(self.zones_table.rowCount()):
                    zone = [
                        float(self.zones_table.item(i, 0).text()),
                        float(self.zones_table.item(i, 1).text()),
                        int(self.zones_table.item(i, 2).text()),
                        int(self.zones_table.item(i, 3).text()),
                        self.zones_table.item(i, 4).text()
                    ]
                    data['zones'].append(zone)
                
                # Sauvegarder les caméras
                for i in range(self.cameras_table.rowCount()):
                    cam = [
                        float(self.cameras_table.item(i, 0).text()),
                        float(self.cameras_table.item(i, 1).text()),
                        float(self.cameras_table.item(i, 2).text()),
                        float(self.cameras_table.item(i, 3).text()),
                        float(self.cameras_table.item(i, 4).text()),
                        self.cameras_table.item(i, 5).text()
                    ]
                    data['cameras'].append(cam)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.log_message(f"Données sauvegardées dans {filename}")
                QMessageBox.information(self, "Succès", "Données sauvegardées avec succès!")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
    
    def start_optimization(self):
        """Lance l'optimisation dans un thread séparé."""
        try:
            # Extraire les données des tables
            zones = []
            zone_priorities = {}
            zone_populations = {}
            
            for i in range(self.zones_table.rowCount()):
                x = float(self.zones_table.item(i, 0).text())
                y = float(self.zones_table.item(i, 1).text())
                priority = float(self.zones_table.item(i, 2).text())
                population = int(self.zones_table.item(i, 3).text())
                
                zones.append((x, y))
                zone_priorities[i] = priority
                zone_populations[i] = population
            
            camera_locations = []
            camera_costs = {}
            camera_ranges = {}
            camera_angles = {}
            camera_types = {}
            
            for i in range(self.cameras_table.rowCount()):
                x = float(self.cameras_table.item(i, 0).text())
                y = float(self.cameras_table.item(i, 1).text())
                cost = float(self.cameras_table.item(i, 2).text())
                range_m = float(self.cameras_table.item(i, 3).text())
                angle = float(self.cameras_table.item(i, 4).text())
                cam_type = self.cameras_table.item(i, 5).text()
                
                camera_locations.append((x, y))
                camera_costs[i] = cost
                camera_ranges[i] = range_m
                camera_angles[i] = angle
                camera_types[i] = cam_type
            
            # Configurer le modèle
            self.model = MaximalCoveringLocationModel()
            self.model.set_problem_data(
                zones=zones,
                camera_locations=camera_locations,
                zone_priorities=zone_priorities,
                zone_populations=zone_populations,
                camera_costs=camera_costs,
                camera_ranges=camera_ranges,
                camera_angles=camera_angles,
                max_cameras=self.max_cameras_spin.value(),
                max_budget=self.max_budget_spin.value(),
                camera_types=camera_types
            )
            
            # Désactiver le bouton et afficher la progression
            self.solve_button.setEnabled(False)
            self.progress_bar.show()
            self.log_text.clear()
            self.log_message("Démarrage de l'optimisation...")
            
            # Lancer le thread d'optimisation
            time_limit = self.time_limit_spin.value()
            gap = self.gap_spin.value() / 100.0  # Convertir en fraction
            
            self.optimization_thread = OptimizationThread(self.model, time_limit, gap)
            self.optimization_thread.progress.connect(self.log_message)
            self.optimization_thread.finished.connect(self.optimization_finished)
            self.optimization_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage: {str(e)}")
            self.solve_button.setEnabled(True)
            self.progress_bar.hide()
    
    def optimization_finished(self, success, solution):
        """Appelé lorsque l'optimisation est terminée."""
        self.solve_button.setEnabled(True)
        self.progress_bar.hide()
        
        if success:
            self.current_solution = solution
            self.display_solution()
            QMessageBox.information(self, "Succès", "Optimisation terminée avec succès!")
        else:
            QMessageBox.warning(self, "Attention", "Aucune solution trouvée ou erreur lors de l'optimisation.")
    
    def display_solution(self):
        """Affiche la solution dans l'interface."""
        if not self.current_solution:
            return
        
        sol = self.current_solution
        
        # Résumé
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║                  RÉSUMÉ DE LA SOLUTION OPTIMALE                 ║
╚════════════════════════════════════════════════════════════════╝

📊 Fonction Objectif (Couverture Pondérée)
   Valeur: {sol['objective_value']:.2f} points

🎥 Caméras Installées
   Nombre: {sol['n_cameras_installed']} / {self.max_cameras_spin.value()}
   Coût Total: {sol['total_cost']:.2f} €
   Utilisation du Budget: {sol['budget_utilization']:.1f}%

🗺️ Zones Couvertes
   Nombre: {sol['n_zones_covered']} / {self.n_zones_spin.value()}
   Pourcentage: {sol['coverage_percentage']:.1f}%
   Couverture Prioritaire Totale: {sol['total_priority_coverage']:.0f}

⏱️ Temps de Résolution: {sol['solve_time']:.2f} secondes
"""
        self.summary_text.setPlainText(summary)
        
        # Détails
        details = "═══════════════════════════════════════════════════════════════\n"
        details += "DÉTAILS DES CAMÉRAS INSTALLÉES\n"
        details += "═══════════════════════════════════════════════════════════════\n\n"
        
        for cam in sol['camera_details']:
            details += f"📷 Caméra #{cam['id']} ({cam['type'].upper()})\n"
            details += f"   Position: ({cam['position'][0]:.1f}, {cam['position'][1]:.1f})\n"
            details += f"   Coût: {cam['cost']:.0f} €\n"
            details += f"   Portée: {cam['range']:.1f}m | Angle: {cam['angle']:.0f}°\n"
            details += f"   Zones couvertes: {cam['n_zones_covered']}\n\n"
        
        details += "\n═══════════════════════════════════════════════════════════════\n"
        details += "DÉTAILS DES ZONES\n"
        details += "═══════════════════════════════════════════════════════════════\n\n"
        
        for zone in sol['zone_details']:
            status = "✅ COUVERTE" if zone['is_covered'] else "❌ NON COUVERTE"
            details += f"Zone #{zone['id']} - {status}\n"
            details += f"   Position: ({zone['position'][0]:.1f}, {zone['position'][1]:.1f})\n"
            details += f"   Priorité: {zone['priority']:.0f} | Population: {zone['population']}\n"
            if zone['is_covered']:
                details += f"   Caméras surveillantes: {zone['covering_cameras']}\n"
                details += f"   Niveau de redondance: {zone['redundancy_level']}\n"
            details += "\n"
        
        self.details_text.setPlainText(details)
    
    def show_coverage_map(self):
        """Affiche la carte de couverture."""
        if not self.current_solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à visualiser. Lancez d'abord l'optimisation.")
            return
        
        self.visualizer.plot_coverage_map(
            zones=self.model.zones,
            camera_locations=self.model.camera_locations,
            cameras_installed=self.current_solution['cameras_installed'],
            zones_covered=self.current_solution['zones_covered'],
            camera_ranges=self.model.camera_ranges,
            zone_priorities=self.model.zone_priorities
        )
    
    def show_heatmap(self):
        """Affiche la heatmap de couverture."""
        if not self.current_solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à visualiser.")
            return
        
        self.visualizer.plot_coverage_heatmap(
            zones=self.model.zones,
            camera_locations=self.model.camera_locations,
            cameras_installed=self.current_solution['cameras_installed'],
            camera_ranges=self.model.camera_ranges,
            coverage_details=self.current_solution['coverage_details']
        )
    
    def show_statistics(self):
        """Affiche les statistiques."""
        if not self.current_solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à visualiser.")
            return
        
        self.visualizer.plot_statistics(
            solution=self.current_solution,
            zone_priorities=self.model.zone_priorities
        )
    
    def export_solution(self):
        """Exporte la solution en JSON."""
        if not self.current_solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à exporter.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter Solution", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_solution, f, indent=2, ensure_ascii=False, default=str)
                
                QMessageBox.information(self, "Succès", f"Solution exportée dans {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def export_report(self):
        """Génère un rapport texte."""
        if not self.current_solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à exporter.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Générer Rapport", "", "Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("═══════════════════════════════════════════════════════════════\n")
                    f.write("    RAPPORT D'OPTIMISATION - COUVERTURE MAXIMALE\n")
                    f.write("    Positionnement de Caméras de Surveillance\n")
                    f.write("═══════════════════════════════════════════════════════════════\n\n")
                    f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                    f.write(self.summary_text.toPlainText())
                    f.write("\n\n")
                    f.write(self.details_text.toPlainText())
                
                QMessageBox.information(self, "Succès", f"Rapport généré dans {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def log_message(self, message):
        """Ajoute un message au journal."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
        self.statusBar().showMessage(message)


def main():
    """Point d'entrée de l'application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style moderne
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
