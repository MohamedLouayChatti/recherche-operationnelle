"""
Point d'entrée principal de l'application
Équilibrage de Chaîne de Montage - Agroalimentaire

Projet de Recherche Opérationnelle
INSAT - Décembre 2025
Enseignant: I. AJILI
"""

import sys
import os

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("APPLICATION D'ÉQUILIBRAGE DE CHAÎNE DE MONTAGE")
    print("   Secteur Agroalimentaire - Optimisation PLNE")
    print("=" * 60)
    print()
    print("Lancement de l'interface graphique...")
    print()
    
    try:
        from PyQt5.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.show()
        
        print("Interface lancée avec succès!")
        print()
        
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"Erreur d'import: {e}")
        print()
        print("Vérifiez que toutes les dépendances sont installées:")
        print("  pip install -r requirements.txt")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors du lancement: {e}")
        print()
        print("Vérifiez que Gurobi est correctement configuré:")
        print("  grbgetkey VOTRE-CLE-LICENCE")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()