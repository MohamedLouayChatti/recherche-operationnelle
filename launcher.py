"""
Launcher Interface - TP Recherche Opérationnelle
Lanceur unifié pour les 3 projets d'optimisation
"""

import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class ProjectLauncher(QMainWindow):
    """Interface de lancement des projets"""
    
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.processes = []
        self.init_ui()
        
    def init_ui(self):
        """Initialisation de l'interface"""
        self.setWindowTitle("Lanceur de Projets - Recherche Opérationnelle")
        self.setGeometry(100, 100, 600, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F9FAFB;
            }
            QLabel#title {
                color: #1E40AF;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
            }
            QLabel#subtitle {
                color: #6B7280;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 20px;
                font-size: 16px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # En-tête
        title = QLabel("🎯 Projets de Recherche Opérationnelle")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Sélectionnez un projet à lancer")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Frame pour les boutons
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        button_layout.setSpacing(15)
        
        # Projet 1 : Système de Flux de Pollution
        self.btn_pollution = QPushButton()
        self.btn_pollution.setText(
            "🌊 Système de Flux de Pollution\n"
            "   Optimisation de réseau hydrique avec Gurobi"
        )
        self.btn_pollution.setMinimumHeight(80)
        self.btn_pollution.clicked.connect(lambda: self.launch_project(
            "Système_de_Flux_de_Pollution",
            "Système de Flux de Pollution"
        ))
        button_layout.addWidget(self.btn_pollution)
        
        # Projet 2 : Security Camera Coverage
        self.btn_camera = QPushButton()
        self.btn_camera.setText(
            "📹 Security Camera Coverage\n"
            "   Optimisation de couverture de caméras de surveillance"
        )
        self.btn_camera.setMinimumHeight(80)
        self.btn_camera.clicked.connect(lambda: self.launch_project(
            "security-camera-coverage",
            "Security Camera Coverage"
        ))
        button_layout.addWidget(self.btn_camera)
        
        # Projet 3 : Bandwidth Flow Optimizer
        self.btn_bandwidth = QPushButton()
        self.btn_bandwidth.setText(
            "📡 Bandwidth Flow Optimizer\n"
            "   Optimisation de flux de bande passante réseau"
        )
        self.btn_bandwidth.setMinimumHeight(80)
        self.btn_bandwidth.clicked.connect(lambda: self.launch_project(
            "BandwidthFlowOptimizer",
            "Bandwidth Flow Optimizer"
        ))
        button_layout.addWidget(self.btn_bandwidth)
        
        # Projet 4 : Conditionnement Agroalimentaire
        self.btn_agro = QPushButton()
        self.btn_agro.setText(
            "🏭 Conditionnement Agroalimentaire\n"
            "   Optimisation de processus de conditionnement"
        )
        self.btn_agro.setMinimumHeight(80)
        self.btn_agro.clicked.connect(lambda: self.launch_project(
            "Conditionnement-Agroalimentaire",
            "Conditionnement Agroalimentaire"
        ))
        button_layout.addWidget(self.btn_agro)
        
        layout.addWidget(button_frame)
        
        # Espace flexible
        layout.addStretch()
        
        # Info footer
        footer = QLabel("💡 Tip: Vous pouvez lancer plusieurs projets en même temps")
        footer.setStyleSheet("color: #6B7280; font-size: 12px; padding: 10px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        
        # Bouton quitter
        btn_quit = QPushButton("❌ Quitter")
        btn_quit.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        btn_quit.clicked.connect(self.close_all)
        layout.addWidget(btn_quit)
    
    def launch_project(self, directory, project_name):
        """Lance un projet dans un processus séparé"""
        project_path = os.path.join(self.base_dir, directory, "main.py")
        
        # Vérifier que le fichier existe
        if not os.path.exists(project_path):
            QMessageBox.critical(
                self,
                "Erreur",
                f"Le fichier main.py n'existe pas dans {directory}"
            )
            return
        
        try:
            # Lancer le projet dans un nouveau processus
            if sys.platform == "win32":
                # Windows
                process = subprocess.Popen(
                    ["python", project_path],
                    cwd=os.path.join(self.base_dir, directory),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Linux/Mac
                process = subprocess.Popen(
                    ["python3", project_path],
                    cwd=os.path.join(self.base_dir, directory)
                )
            
            self.processes.append((process, project_name))
            
            QMessageBox.information(
                self,
                "Succès",
                f"✅ {project_name} a été lancé avec succès!\n\n"
                f"PID: {process.pid}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de lancer {project_name}:\n{str(e)}"
            )
    
    def close_all(self):
        """Ferme tous les processus et l'application"""
        if self.processes:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                f"Il y a {len(self.processes)} projet(s) en cours d'exécution.\n"
                "Voulez-vous les fermer ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for process, name in self.processes:
                    try:
                        process.terminate()
                        print(f"Processus {name} (PID: {process.pid}) terminé")
                    except:
                        pass
        
        self.close()
    
    def closeEvent(self, event):
        """Gestion de la fermeture de la fenêtre"""
        if self.processes:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Des projets sont toujours en cours d'exécution.\n"
                "Les fermer en quittant ?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                for process, name in self.processes:
                    try:
                        process.terminate()
                    except:
                        pass
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    launcher = ProjectLauncher()
    launcher.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
