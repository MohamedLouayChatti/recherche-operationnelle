"""
Module de visualisation pour le problème de Couverture Maximale.

Ce module fournit des fonctions pour créer des visualisations graphiques
de la solution d'optimisation, incluant:
- Cartes de couverture
- Heatmaps
- Graphiques statistiques
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle
import numpy as np
from typing import List, Tuple, Dict


class CoverageVisualizer:
    """Classe pour visualiser les résultats de l'optimisation."""
    
    def __init__(self):
        """Initialise le visualiseur."""
        plt.style.use('seaborn-v0_8-darkgrid')
        
    def plot_coverage_map(self, 
                         zones: List[Tuple[float, float]],
                         camera_locations: List[Tuple[float, float]],
                         cameras_installed: List[int],
                         zones_covered: List[int],
                         camera_ranges: Dict[int, float],
                         zone_priorities: Dict[int, float]):
        """
        Affiche la carte de couverture avec les zones et les caméras.
        
        Args:
            zones: Liste des positions des zones
            camera_locations: Liste des positions possibles de caméras
            cameras_installed: Indices des caméras installées
            zones_covered: Indices des zones couvertes
            camera_ranges: Portées des caméras
            zone_priorities: Priorités des zones
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Tracer les zones
        zones_array = np.array(zones)
        zones_not_covered = [i for i in range(len(zones)) if i not in zones_covered]
        
        # Zones non couvertes (rouge)
        if zones_not_covered:
            not_covered_array = zones_array[zones_not_covered]
            priorities_not_covered = [zone_priorities.get(i, 1.0) for i in zones_not_covered]
            scatter1 = ax.scatter(not_covered_array[:, 0], not_covered_array[:, 1],
                                c=priorities_not_covered, cmap='Reds', 
                                s=200, alpha=0.6, marker='s',
                                edgecolors='darkred', linewidths=2,
                                label='Zones non couvertes', vmin=0, vmax=10)
        
        # Zones couvertes (vert)
        if zones_covered:
            covered_array = zones_array[zones_covered]
            priorities_covered = [zone_priorities.get(i, 1.0) for i in zones_covered]
            scatter2 = ax.scatter(covered_array[:, 0], covered_array[:, 1],
                                c=priorities_covered, cmap='Greens',
                                s=200, alpha=0.6, marker='s',
                                edgecolors='darkgreen', linewidths=2,
                                label='Zones couvertes', vmin=0, vmax=10)
        
        # Tracer les cercles de couverture des caméras installées
        for cam_id in cameras_installed:
            pos = camera_locations[cam_id]
            range_m = camera_ranges.get(cam_id, 50.0)
            
            circle = Circle(pos, range_m, color='blue', alpha=0.15, linestyle='--', linewidth=1.5)
            ax.add_patch(circle)
        
        # Tracer les caméras installées
        cameras_array = np.array([camera_locations[i] for i in cameras_installed])
        ax.scatter(cameras_array[:, 0], cameras_array[:, 1],
                  c='blue', s=300, alpha=0.9, marker='^',
                  edgecolors='navy', linewidths=2,
                  label='Caméras installées', zorder=5)
        
        # Numéroter les caméras
        for idx, cam_id in enumerate(cameras_installed):
            pos = camera_locations[cam_id]
            ax.annotate(f'C{cam_id}', (pos[0], pos[1]), 
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, fontweight='bold', color='darkblue',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # Numéroter les zones prioritaires (priorité >= 7)
        for i, pos in enumerate(zones):
            if zone_priorities.get(i, 1.0) >= 7:
                ax.annotate(f'Z{i}\n(P:{zone_priorities[i]:.0f})', pos,
                           xytext=(0, -15), textcoords='offset points',
                           fontsize=8, ha='center', color='red', fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
        
        # Colorbar pour les priorités
        if zones_covered:
            cbar = plt.colorbar(scatter2, ax=ax, label='Priorité des Zones')
        elif zones_not_covered:
            cbar = plt.colorbar(scatter1, ax=ax, label='Priorité des Zones')
        
        ax.set_xlabel('Coordonnée X (mètres)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordonnée Y (mètres)', fontsize=12, fontweight='bold')
        ax.set_title('Carte de Couverture Optimale - Positionnement des Caméras de Surveillance', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        plt.show()
    
    def plot_coverage_heatmap(self,
                             zones: List[Tuple[float, float]],
                             camera_locations: List[Tuple[float, float]],
                             cameras_installed: List[int],
                             camera_ranges: Dict[int, float],
                             coverage_details: Dict[int, List[int]]):
        """
        Affiche une heatmap de l'intensité de la couverture.
        
        Args:
            zones: Liste des positions des zones
            camera_locations: Liste des positions possibles de caméras
            cameras_installed: Indices des caméras installées
            camera_ranges: Portées des caméras
            coverage_details: Détails de couverture par zone
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Créer une grille pour la heatmap
        zones_array = np.array(zones)
        x_min, x_max = zones_array[:, 0].min() - 50, zones_array[:, 0].max() + 50
        y_min, y_max = zones_array[:, 1].min() - 50, zones_array[:, 1].max() + 50
        
        # Résolution de la grille
        resolution = 100
        x_grid = np.linspace(x_min, x_max, resolution)
        y_grid = np.linspace(y_min, y_max, resolution)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        # Calculer l'intensité de couverture en chaque point
        Z = np.zeros_like(X)
        
        for cam_id in cameras_installed:
            cam_pos = camera_locations[cam_id]
            cam_range = camera_ranges.get(cam_id, 50.0)
            
            # Distance de chaque point de la grille à la caméra
            dist = np.sqrt((X - cam_pos[0])**2 + (Y - cam_pos[1])**2)
            
            # Contribution de cette caméra (décroissance avec la distance)
            contribution = np.where(dist <= cam_range, 1 - (dist / cam_range), 0)
            Z += contribution
        
        # Afficher la heatmap
        heatmap = ax.contourf(X, Y, Z, levels=20, cmap='YlOrRd', alpha=0.7)
        plt.colorbar(heatmap, ax=ax, label='Intensité de Couverture')
        
        # Tracer les zones
        for i, pos in enumerate(zones):
            n_cameras = len(coverage_details.get(i, []))
            if n_cameras > 0:
                color = 'green'
                marker = 'o'
            else:
                color = 'red'
                marker = 'x'
            
            ax.scatter(pos[0], pos[1], c=color, s=150, marker=marker,
                      edgecolors='black', linewidths=1.5, zorder=5, alpha=0.8)
            
            # Annoter le niveau de redondance
            if n_cameras > 1:
                ax.annotate(f'{n_cameras}×', pos,
                           xytext=(8, 8), textcoords='offset points',
                           fontsize=9, fontweight='bold', color='darkgreen',
                           bbox=dict(boxstyle='circle,pad=0.3', facecolor='white', alpha=0.9))
        
        # Tracer les caméras
        cameras_array = np.array([camera_locations[i] for i in cameras_installed])
        ax.scatter(cameras_array[:, 0], cameras_array[:, 1],
                  c='blue', s=300, alpha=0.9, marker='^',
                  edgecolors='navy', linewidths=2,
                  label='Caméras', zorder=6)
        
        ax.set_xlabel('Coordonnée X (mètres)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordonnée Y (mètres)', fontsize=12, fontweight='bold')
        ax.set_title('Heatmap d\'Intensité de Couverture', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        plt.show()
    
    def plot_statistics(self, 
                       solution: Dict,
                       zone_priorities: Dict[int, float]):
        """
        Affiche des statistiques sur la solution.
        
        Args:
            solution: Dictionnaire contenant la solution
            zone_priorities: Priorités des zones
        """
        fig = plt.figure(figsize=(16, 10))
        
        # 1. Diagramme à barres des caméras par type
        ax1 = plt.subplot(2, 3, 1)
        camera_types_count = {}
        for cam in solution['camera_details']:
            cam_type = cam['type']
            camera_types_count[cam_type] = camera_types_count.get(cam_type, 0) + 1
        
        types = list(camera_types_count.keys())
        counts = list(camera_types_count.values())
        colors_types = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
        
        bars = ax1.bar(types, counts, color=colors_types[:len(types)], alpha=0.8, edgecolor='black')
        ax1.set_ylabel('Nombre de Caméras', fontweight='bold')
        ax1.set_title('Distribution des Types de Caméras', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Annoter les barres
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        # 2. Camembert de la couverture
        ax2 = plt.subplot(2, 3, 2)
        covered = solution['n_zones_covered']
        not_covered = len(solution['zone_details']) - covered
        
        labels = [f'Couvertes\n({covered})', f'Non couvertes\n({not_covered})']
        sizes = [covered, not_covered]
        colors_pie = ['#2ecc71', '#e74c3c']
        explode = (0.1, 0)
        
        ax2.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
               autopct='%1.1f%%', shadow=True, startangle=90,
               textprops={'fontweight': 'bold', 'fontsize': 11})
        ax2.set_title('Taux de Couverture des Zones', fontweight='bold')
        
        # 3. Histogramme des niveaux de redondance
        ax3 = plt.subplot(2, 3, 3)
        redundancy_levels = [zone['redundancy_level'] for zone in solution['zone_details'] if zone['is_covered']]
        
        if redundancy_levels:
            max_redundancy = max(redundancy_levels)
            bins = range(1, max_redundancy + 2)
            ax3.hist(redundancy_levels, bins=bins, color='#9b59b6', alpha=0.8, edgecolor='black', align='left')
            ax3.set_xlabel('Niveau de Redondance (nombre de caméras)', fontweight='bold')
            ax3.set_ylabel('Nombre de Zones', fontweight='bold')
            ax3.set_title('Distribution de la Redondance', fontweight='bold')
            ax3.grid(axis='y', alpha=0.3)
            ax3.set_xticks(bins[:-1])
        
        # 4. Diagramme à barres des coûts
        ax4 = plt.subplot(2, 3, 4)
        camera_costs = [cam['cost'] for cam in solution['camera_details']]
        camera_ids = [f"C{cam['id']}" for cam in solution['camera_details']]
        
        bars = ax4.bar(camera_ids, camera_costs, color='#e67e22', alpha=0.8, edgecolor='black')
        ax4.set_xlabel('Caméras Installées', fontweight='bold')
        ax4.set_ylabel('Coût (€)', fontweight='bold')
        ax4.set_title('Coût par Caméra Installée', fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 5. Distribution des priorités des zones couvertes vs non couvertes
        ax5 = plt.subplot(2, 3, 5)
        
        covered_priorities = [zone['priority'] for zone in solution['zone_details'] if zone['is_covered']]
        not_covered_priorities = [zone['priority'] for zone in solution['zone_details'] if not zone['is_covered']]
        
        x_pos = np.arange(1, 11)
        covered_counts = [covered_priorities.count(i) for i in x_pos]
        not_covered_counts = [not_covered_priorities.count(i) for i in x_pos]
        
        width = 0.35
        ax5.bar(x_pos - width/2, covered_counts, width, label='Couvertes', 
               color='#2ecc71', alpha=0.8, edgecolor='black')
        ax5.bar(x_pos + width/2, not_covered_counts, width, label='Non couvertes',
               color='#e74c3c', alpha=0.8, edgecolor='black')
        
        ax5.set_xlabel('Niveau de Priorité', fontweight='bold')
        ax5.set_ylabel('Nombre de Zones', fontweight='bold')
        ax5.set_title('Couverture par Niveau de Priorité', fontweight='bold')
        ax5.set_xticks(x_pos)
        ax5.legend()
        ax5.grid(axis='y', alpha=0.3)
        
        # 6. Tableau récapitulatif
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # Données du tableau
        stats_data = [
            ['Métrique', 'Valeur'],
            ['─' * 30, '─' * 20],
            ['Fonction Objectif', f"{solution['objective_value']:.2f}"],
            ['Caméras Installées', f"{solution['n_cameras_installed']}"],
            ['Coût Total', f"{solution['total_cost']:.0f} €"],
            ['Budget Utilisé', f"{solution['budget_utilization']:.1f}%"],
            ['Zones Couvertes', f"{solution['n_zones_covered']}"],
            ['Taux de Couverture', f"{solution['coverage_percentage']:.1f}%"],
            ['Temps de Résolution', f"{solution['solve_time']:.2f}s"],
        ]
        
        table = ax6.table(cellText=stats_data, cellLoc='left', loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Styliser l'en-tête
        for i in range(2):
            table[(0, i)].set_facecolor('#3498db')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Styliser les lignes
        for i in range(2, len(stats_data)):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#ecf0f1')
                else:
                    table[(i, j)].set_facecolor('#ffffff')
        
        ax6.set_title('Résumé des Performances', fontweight='bold', fontsize=12, pad=20)
        
        # Titre principal
        fig.suptitle('Statistiques de la Solution d\'Optimisation', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()
    
    def plot_camera_efficiency(self, solution: Dict):
        """
        Affiche l'efficacité de chaque caméra (zones couvertes / coût).
        
        Args:
            solution: Dictionnaire contenant la solution
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        camera_ids = [f"C{cam['id']}" for cam in solution['camera_details']]
        efficiencies = [cam['n_zones_covered'] / cam['cost'] * 1000 
                       for cam in solution['camera_details']]
        
        colors = ['#2ecc71' if e > np.mean(efficiencies) else '#e74c3c' 
                 for e in efficiencies]
        
        bars = ax.barh(camera_ids, efficiencies, color=colors, alpha=0.8, edgecolor='black')
        
        ax.set_xlabel('Efficacité (zones couvertes / 1000€)', fontweight='bold')
        ax.set_ylabel('Caméras', fontweight='bold')
        ax.set_title('Efficacité des Caméras Installées', fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        # Ligne de moyenne
        mean_efficiency = np.mean(efficiencies)
        ax.axvline(mean_efficiency, color='navy', linestyle='--', linewidth=2, 
                  label=f'Moyenne: {mean_efficiency:.2f}')
        ax.legend()
        
        plt.tight_layout()
        plt.show()
