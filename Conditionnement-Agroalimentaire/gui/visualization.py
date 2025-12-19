"""
Module de visualisation pour les solutions d'équilibrage
"""

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class SolutionVisualizer(FigureCanvas):
    """Canvas Matplotlib intégré dans PyQt5 pour visualiser la solution"""
    
    def __init__(self, parent=None, width=12, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def plot_solution(self, solution):
        """
        Visualise la solution d'équilibrage
        
        Args:
            solution: dictionnaire contenant la solution
        """
        self.fig.clear()
        
        # Créer 2 subplots
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)
        
        # Graphique 1: Charge par poste
        self._plot_workload(ax1, solution)
        
        # Graphique 2: Diagramme de Gantt
        self._plot_gantt(ax2, solution)
        
        self.fig.tight_layout()
        self.draw()
    
    def _plot_workload(self, ax, solution):
        """Graphique en barres de la charge par poste"""
        charges = solution['charges']
        temps_cycle = solution['temps_cycle']
        
        postes = list(charges.keys())
        charges_values = list(charges.values())
        
        # Barres de charge
        bars = ax.bar(postes, charges_values, color='#2196F3', alpha=0.7, 
                     label='Charge')
        
        # Ligne de temps de cycle
        ax.axhline(y=temps_cycle, color='red', linestyle='--', 
                  linewidth=2, label=f'Temps de cycle ({temps_cycle:.1f}s)')
        
        # Style
        ax.set_xlabel('Poste de Travail', fontsize=12, fontweight='bold')
        ax.set_ylabel('Temps (secondes)', fontsize=12, fontweight='bold')
        ax.set_title('Charge de Travail par Poste', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Ajouter les valeurs sur les barres
        for bar, charge in zip(bars, charges_values):
            height = bar.get_height()
            utilisation = (charge / temps_cycle) * 100
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{charge:.1f}s\n({utilisation:.0f}%)',
                   ha='center', va='bottom', fontsize=9)
        
        # Ajuster les limites
        ax.set_ylim(0, temps_cycle * 1.2)
        ax.set_xticks(postes)
        ax.set_xticklabels([f'P{p}' for p in postes])
    
    def _plot_gantt(self, ax, solution):
        """Diagramme de Gantt des affectations"""
        affectations = solution['affectations']
        
        colors = plt.cm.Set3(range(len(affectations)))
        
        y_pos = 0
        y_labels = []
        
        for poste, taches in sorted(affectations.items()):
            if not taches:
                continue
            
            y_labels.append(f'Poste {poste}')
            
            # Position de départ pour ce poste
            start = 0
            
            for tache in taches:
                duree = tache['duree']
                
                # Dessiner la tâche
                ax.barh(y_pos, duree, left=start, height=0.6, 
                       color=colors[poste-1], alpha=0.8,
                       edgecolor='black', linewidth=1)
                
                # Ajouter le texte (nom de la tâche)
                ax.text(start + duree/2, y_pos, 
                       f"{tache['nom']}\n{duree}s",
                       ha='center', va='center', fontsize=8,
                       fontweight='bold')
                
                start += duree
            
            y_pos += 1
        
        # Style
        ax.set_xlabel('Temps (secondes)', fontsize=12, fontweight='bold')
        ax.set_title('Diagramme de Gantt - Affectation des Tâches', 
                    fontsize=14, fontweight='bold')
        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels(y_labels)
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0, solution['temps_cycle'] * 1.1)
        
        # Inverser l'axe Y pour avoir Poste 1 en haut
        ax.invert_yaxis()