#!/usr/bin/env python3
"""
Relationship Visualizer with GLOWING LINES! ✨
Beautiful interactive graph showing file relationships
"""

import sys
import math
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QPainterPath


class Node:
    """A node in the graph"""
    def __init__(self, id, label, node_type, x=0, y=0):
        self.id = id
        self.label = label
        self.type = node_type  # 'file', 'project', 'tag'
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.connections = []
        self.selected = False
        self.hovered = False
        
        # Colors by type
        self.colors = {
            'file': QColor(59, 130, 246),      # Blue
            'project': QColor(16, 185, 129),   # Green
            'tag': QColor(139, 92, 246)        # Purple
        }
        self.color = self.colors.get(node_type, QColor(156, 163, 175))
    
    def add_connection(self, other_node):
        if other_node not in self.connections:
            self.connections.append(other_node)
    
    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx*dx + dy*dy)


class RelationshipCanvas(QWidget):
    """Canvas for drawing the glowing relationship graph"""
    
    node_clicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        
        self.nodes = []
        self.selected_node = None
        self.hovered_node = None
        self.dragging = False
        self.drag_node = None
        
        # Physics simulation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)  # ~60 FPS
        
        # Animation
        self.animation_frame = 0
        self.glow_animation = QTimer()
        self.glow_animation.timeout.connect(self.animate_glow)
        self.glow_animation.start(50)
    
    def set_data(self, nodes):
        """Set graph data"""
        self.nodes = nodes
        
        # Initial layout in circle
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(self.width(), self.height()) / 3
        
        for i, node in enumerate(self.nodes):
            angle = (2 * math.pi * i) / len(self.nodes)
            node.x = center_x + radius * math.cos(angle)
            node.y = center_y + radius * math.sin(angle)
        
        self.update()
    
    def update_physics(self):
        """Simple force-directed layout"""
        if not self.nodes or self.dragging:
            return
        
        # Repulsion between all nodes
        for node in self.nodes:
            node.vx = 0
            node.vy = 0
            
            for other in self.nodes:
                if node == other:
                    continue
                
                dx = node.x - other.x
                dy = node.y - other.y
                dist = math.sqrt(dx*dx + dy*dy) + 0.1
                
                # Repulsion force
                force = 1000 / (dist * dist)
                node.vx += (dx / dist) * force
                node.vy += (dy / dist) * force
        
        # Attraction for connected nodes
        for node in self.nodes:
            for other in node.connections:
                dx = other.x - node.x
                dy = other.y - node.y
                dist = math.sqrt(dx*dx + dy*dy) + 0.1
                
                # Attraction force
                force = dist * 0.01
                node.vx += (dx / dist) * force
                node.vy += (dy / dist) * force
        
        # Apply forces with damping
        for node in self.nodes:
            node.x += node.vx * 0.1
            node.y += node.vy * 0.1
            
            # Keep in bounds
            margin = 50
            node.x = max(margin, min(self.width() - margin, node.x))
            node.y = max(margin, min(self.height() - margin, node.y))
        
        self.update()
    
    def animate_glow(self):
        """Animate the glow effect"""
        self.animation_frame = (self.animation_frame + 1) % 100
        self.update()
    
    def paintEvent(self, event):
        """Draw the glowing graph!"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dark background
        painter.fillRect(self.rect(), QColor(17, 24, 39))
        
        # Draw connections with GLOWING LINES! ✨
        self._draw_glowing_connections(painter)
        
        # Draw nodes with glow
        self._draw_glowing_nodes(painter)
        
        # Draw labels
        self._draw_labels(painter)
    
    def _draw_glowing_connections(self, painter):
        """Draw connections with beautiful glowing effect"""
        drawn = set()
        
        for node in self.nodes:
            for other in node.connections:
                # Avoid drawing twice
                pair = tuple(sorted([node.id, other.id]))
                if pair in drawn:
                    continue
                drawn.add(pair)
                
                # Glow intensity based on animation
                glow_factor = 0.5 + 0.5 * math.sin(self.animation_frame * 0.1)
                
                # Draw multiple layers for glow effect
                for i in range(5, 0, -1):
                    alpha = int(30 * glow_factor * (i / 5))
                    width = i * 2
                    
                    # Mix colors based on node types
                    color = self._blend_colors(node.color, other.color)
                    color.setAlpha(alpha)
                    
                    pen = QPen(color)
                    pen.setWidth(width)
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    painter.setPen(pen)
                    
                    painter.drawLine(QPointF(node.x, node.y), QPointF(other.x, other.y))
                
                # Core line (bright!)
                core_color = self._blend_colors(node.color, other.color)
                core_color.setAlpha(int(200 * glow_factor))
                pen = QPen(core_color)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(QPointF(node.x, node.y), QPointF(other.x, other.y))
    
    def _draw_glowing_nodes(self, painter):
        """Draw nodes with glow effect"""
        for node in self.nodes:
            # Node size
            base_size = 12
            if node.selected:
                base_size = 18
            elif node.hovered:
                base_size = 15
            
            # Glow layers
            for i in range(4, 0, -1):
                gradient = QRadialGradient(QPointF(node.x, node.y), base_size + i*3)
                
                glow_color = QColor(node.color)
                glow_color.setAlpha(int(40 * (4-i) / 4))
                gradient.setColorAt(0, glow_color)
                
                transparent = QColor(node.color)
                transparent.setAlpha(0)
                gradient.setColorAt(1, transparent)
                
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(node.x, node.y), base_size + i*3, base_size + i*3)
            
            # Core node
            gradient = QRadialGradient(QPointF(node.x, node.y), base_size)
            gradient.setColorAt(0, node.color.lighter(150))
            gradient.setColorAt(0.7, node.color)
            gradient.setColorAt(1, node.color.darker(120))
            
            painter.setBrush(QBrush(gradient))
            
            # Border
            if node.selected:
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            else:
                painter.setPen(QPen(node.color.darker(), 1))
            
            painter.drawEllipse(QPointF(node.x, node.y), base_size, base_size)
    
    def _draw_labels(self, painter):
        """Draw node labels"""
        painter.setPen(QPen(QColor(229, 231, 235)))
        
        for node in self.nodes:
            if node.hovered or node.selected:
                # Draw label
                label = node.label
                if len(label) > 20:
                    label = label[:17] + "..."
                
                # Background for readability
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(label)
                text_height = fm.height()
                
                bg_rect = QRectF(node.x - text_width/2 - 5, 
                                node.y + 20, 
                                text_width + 10, 
                                text_height + 4)
                
                painter.fillRect(bg_rect, QColor(17, 24, 39, 200))
                painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, label)
    
    def _blend_colors(self, color1, color2):
        """Blend two colors"""
        r = (color1.red() + color2.red()) // 2
        g = (color1.green() + color2.green()) // 2
        b = (color1.blue() + color2.blue()) // 2
        return QColor(r, g, b)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        pos = event.pos()
        
        for node in self.nodes:
            dist = math.sqrt((pos.x() - node.x)**2 + (pos.y() - node.y)**2)
            if dist < 15:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.dragging = True
                    self.drag_node = node
                    node.selected = True
                    self.node_clicked.emit(node)
                break
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        pos = event.pos()
        
        if self.dragging and self.drag_node:
            self.drag_node.x = pos.x()
            self.drag_node.y = pos.y()
            self.update()
            return
        
        # Check hover
        old_hovered = self.hovered_node
        self.hovered_node = None
        
        for node in self.nodes:
            dist = math.sqrt((pos.x() - node.x)**2 + (pos.y() - node.y)**2)
            node.hovered = dist < 15
            if node.hovered:
                self.hovered_node = node
        
        if old_hovered != self.hovered_node:
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.dragging = False
        self.drag_node = None


class RelationshipVisualizerWindow(QMainWindow):
    """Main window for relationship visualizer"""
    
    def __init__(self, file_db):
        super().__init__()
        self.db = file_db
        self.setWindowTitle("🌟 Relationship Visualizer - Glowing Lines!")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Controls
        controls = self._create_controls()
        layout.addWidget(controls)
        
        # Canvas
        self.canvas = RelationshipCanvas()
        self.canvas.node_clicked.connect(self.on_node_clicked)
        layout.addWidget(self.canvas)
        
        # Info label
        self.info_label = QLabel("Click a node to see details • Drag to rearrange")
        self.info_label.setStyleSheet("color: #9ca3af; padding: 10px;")
        layout.addWidget(self.info_label)
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #111827; }
            QLabel { color: #e5e7eb; }
            QPushButton {
                background-color: #374151;
                color: #e5e7eb;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #4b5563; }
            QLineEdit, QComboBox {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
                padding: 6px;
                border-radius: 4px;
            }
        """)
        
        # Load initial data
        self.load_data()
    
    def _create_controls(self):
        """Create control panel"""
        controls = QWidget()
        layout = QHBoxLayout(controls)
        
        layout.addWidget(QLabel("Visualize:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Files", "By Project", "By Tag", "By Folder"])
        self.filter_combo.currentTextChanged.connect(self.load_data)
        layout.addWidget(self.filter_combo)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search project/tag...")
        self.search_input.returnPressed.connect(self.load_data)
        layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return controls
    
    def load_data(self):
        """Load relationship data from database"""
        from graph_store import FileGraphIntegration
        
        graph = FileGraphIntegration(self.db)
        graph.build_graph_from_database()
        
        # Create nodes
        nodes = []
        node_map = {}
        
        search_term = self.search_input.text().strip()
        filter_type = self.filter_combo.currentText()
        
        # Get files and their relationships
        cursor = self.db.conn.cursor()
        
        if search_term:
            # Search for specific project/tag
            cursor.execute("""
                SELECT id, filename, project, ai_tags
                FROM files
                WHERE (project LIKE ? OR ai_tags LIKE ?)
                AND status = 'active'
                AND hide_from_app = 0
                LIMIT 30
            """, (f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute("""
                SELECT id, filename, project, ai_tags
                FROM files
                WHERE status = 'active'
                AND hide_from_app = 0
                LIMIT 30
            """)
        
        # Create file nodes
        for file_id, filename, project, tags in cursor.fetchall():
            node = Node(f"file_{file_id}", filename, 'file')
            nodes.append(node)
            node_map[f"file_{file_id}"] = node
            
            # Create project node
            if project:
                project_key = f"project_{project}"
                if project_key not in node_map:
                    project_node = Node(project_key, project, 'project')
                    nodes.append(project_node)
                    node_map[project_key] = project_node
                
                # Connect
                node.add_connection(node_map[project_key])
                node_map[project_key].add_connection(node)
            
            # Create tag nodes
            if tags:
                for tag in [t.strip() for t in tags.split(',')][:2]:  # Limit to 2 tags
                    tag_key = f"tag_{tag}"
                    if tag_key not in node_map:
                        tag_node = Node(tag_key, tag, 'tag')
                        nodes.append(tag_node)
                        node_map[tag_key] = tag_node
                    
                    # Connect
                    node.add_connection(node_map[tag_key])
                    node_map[tag_key].add_connection(node)
        
        self.canvas.set_data(nodes)
        self.info_label.setText(f"Showing {len(nodes)} nodes • {sum(len(n.connections) for n in nodes)//2} connections")
    
    def on_node_clicked(self, node):
        """Handle node click"""
        self.info_label.setText(f"Selected: {node.label} ({node.type}) • {len(node.connections)} connections")


def show_visualizer(file_db):
    """Show the relationship visualizer window"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = RelationshipVisualizerWindow(file_db)
    window.show()
    
    return window


if __name__ == "__main__":
    print("🌟 Relationship Visualizer with GLOWING LINES!")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    
    app = QApplication(sys.argv)
    window = RelationshipVisualizerWindow(db)
    window.show()
    
    sys.exit(app.exec())

