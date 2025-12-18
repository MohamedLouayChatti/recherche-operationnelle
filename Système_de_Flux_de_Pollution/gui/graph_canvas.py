

# =============================================================================
# gui/graph_canvas.py - Visualisation du graphe
# =============================================================================

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import networkx as nx

class GraphCanvas(FigureCanvasQTAgg):
    """Canvas pour visualiser le réseau"""
    
    def __init__(self, parent=None):
        fig = Figure(figsize=(8, 6))
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        
    def plot_graph(self, nodes, arcs, flows=None):
        """Dessine le graphe avec les flux"""
        self.axes.clear()
        G = nx.DiGraph()
        
        # Nœuds
        node_colors = []
        pos = {}
        labels = {}
        
        for node in nodes:
            G.add_node(node['id'])
            pos[node['id']] = (node.get('x', 0), node.get('y', 0))
            labels[node['id']] = f"{node['name']}\n({node['supply']:+.0f})"
            
            if node['type'] == 'source':
                node_colors.append('#10B981')
            elif node['type'] == 'sink':
                node_colors.append('#EF4444')
            else:
                node_colors.append('#3B82F6')
        
        # Arcs
        edge_labels = {}
        edge_widths = []
        edge_colors = []
        
        for idx, arc in enumerate(arcs):
            G.add_edge(arc['from'], arc['to'])
            
            if flows and flows[idx] > 0.01:
                label = f"{flows[idx]:.1f}/{arc['capacity']:.0f}"
                width = 1 + (flows[idx] / arc['capacity']) * 4
                color = '#3B82F6'
            else:
                label = f"c:{arc['cost']:.1f}"
                width = 1
                color = '#9CA3AF'
            
            edge_labels[(arc['from'], arc['to'])] = label
            edge_widths.append(width)
            edge_colors.append(color)
        
        # Dessin
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                               node_size=800, ax=self.axes)
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=self.axes)
        nx.draw_networkx_edges(G, pos, width=edge_widths, 
                               edge_color=edge_colors, arrows=True,
                               connectionstyle='arc3,rad=0.1', ax=self.axes)
        nx.draw_networkx_edge_labels(G, pos, edge_labels, 
                                      font_size=7, ax=self.axes)
        
        self.axes.set_title("Réseau de Flux de Pollution", fontsize=14)
        self.axes.axis('off')
        self.draw()


