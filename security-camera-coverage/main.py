"""
Point d'entrée principal de l'application de Couverture Maximale.
Lance l'interface graphique PyQt.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.main_window import MainWindow


def check_dependencies():
    """Vérifie que toutes les dépendances sont installées."""
    missing_packages = []
    
    try:
        import gurobipy
    except ImportError:
        missing_packages.append("gurobipy")
    
    try:
        import PyQt5
    except ImportError:
        missing_packages.append("PyQt5")
    
    try:
        import matplotlib
    except ImportError:
        missing_packages.append("matplotlib")
    
    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")
    
    return missing_packages


def main():
    """Lance l'application."""
    # Vérifier les dépendances
    missing = check_dependencies()
    
    if missing:
        app = QApplication(sys.argv)
        error_msg = f"Les packages suivants sont manquants:\n\n"
        error_msg += "\n".join(f"  - {pkg}" for pkg in missing)
        error_msg += "\n\nVeuillez les installer avec:\n"
        error_msg += f"pip install {' '.join(missing)}"
        
        QMessageBox.critical(None, "Dépendances Manquantes", error_msg)
        return 1
    
    # Lancer l'application
    app = QApplication(sys.argv)
    app.setApplicationName("Couverture Maximale - Caméras de Surveillance")
    app.setOrganizationName("INSAT")
    
    try:
        window = MainWindow()
        window.show()
        return app.exec_()
    except Exception as e:
        QMessageBox.critical(None, "Erreur", f"Erreur lors du lancement:\n{str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
