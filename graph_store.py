#!/usr/bin/env python3
"""
Graph Database for File Relationships
Tracks connections between files, projects, and tags
Enables graph-based queries like "show me everything related to Project X"
"""

import sqlite3
import json
from datetime import datetime
from collections import defaultdict, deque


class FileGraphStore:
    """
    Graph database built on SQLite for file relationship tracking
    Nodes: files, projects, tags, people
    Edges: relationships with weights and types
    """
    
    def __init__(self, db_conn):
        self.conn = db_conn
        self.init_graph_schema()
    
    def init_graph_schema(self):
        """Initialize graph tables"""
        cursor = self.conn.cursor()
        
        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                node_id TEXT NOT NULL,
                label TEXT,
                properties TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(node_type, node_id)
            )
        """)
        
        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_node INTEGER NOT NULL,
                to_node INTEGER NOT NULL,
                edge_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                properties TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_node) REFERENCES graph_nodes(id),
                FOREIGN KEY (to_node) REFERENCES graph_nodes(id)
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_node_type ON graph_nodes(node_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edge_from ON graph_edges(from_node)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edge_to ON graph_edges(to_node)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edge_type ON graph_edges(edge_type)")
        
        self.conn.commit()
    
    def add_node(self, node_type, node_id, label=None, properties=None):
        """Add or update a node"""
        cursor = self.conn.cursor()
        
        props_json = json.dumps(properties) if properties else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO graph_nodes 
            (node_type, node_id, label, properties)
            VALUES (?, ?, ?, ?)
        """, (node_type, node_id, label, props_json))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_node_pk(self, node_type, node_id):
        """Get internal node PK"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM graph_nodes 
            WHERE node_type = ? AND node_id = ?
        """, (node_type, node_id))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def add_edge(self, from_type, from_id, to_type, to_id, edge_type, weight=1.0, properties=None):
        """Add or update an edge between nodes"""
        # Get or create nodes
        from_pk = self.get_node_pk(from_type, from_id)
        if not from_pk:
            from_pk = self.add_node(from_type, from_id)
        
        to_pk = self.get_node_pk(to_type, to_id)
        if not to_pk:
            to_pk = self.add_node(to_type, to_id)
        
        cursor = self.conn.cursor()
        props_json = json.dumps(properties) if properties else None
        
        # Check if edge exists
        cursor.execute("""
            SELECT id, weight FROM graph_edges
            WHERE from_node = ? AND to_node = ? AND edge_type = ?
        """, (from_pk, to_pk, edge_type))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update weight (increase strength)
            edge_id, old_weight = existing
            new_weight = old_weight + weight
            cursor.execute("""
                UPDATE graph_edges 
                SET weight = ?, updated_at = ?, properties = ?
                WHERE id = ?
            """, (new_weight, datetime.now().isoformat(), props_json, edge_id))
        else:
            # Create new edge
            cursor.execute("""
                INSERT INTO graph_edges
                (from_node, to_node, edge_type, weight, properties)
                VALUES (?, ?, ?, ?, ?)
            """, (from_pk, to_pk, edge_type, weight, props_json))
        
        self.conn.commit()
    
    def get_neighbors(self, node_type, node_id, edge_type=None, direction='both'):
        """
        Get neighboring nodes
        direction: 'out' (outgoing), 'in' (incoming), 'both'
        """
        pk = self.get_node_pk(node_type, node_id)
        if not pk:
            return []
        
        cursor = self.conn.cursor()
        neighbors = []
        
        # Outgoing edges
        if direction in ['out', 'both']:
            query = """
                SELECT n.node_type, n.node_id, n.label, e.edge_type, e.weight
                FROM graph_edges e
                JOIN graph_nodes n ON e.to_node = n.id
                WHERE e.from_node = ?
            """
            if edge_type:
                query += " AND e.edge_type = ?"
                cursor.execute(query, (pk, edge_type))
            else:
                cursor.execute(query, (pk,))
            
            neighbors.extend(cursor.fetchall())
        
        # Incoming edges
        if direction in ['in', 'both']:
            query = """
                SELECT n.node_type, n.node_id, n.label, e.edge_type, e.weight
                FROM graph_edges e
                JOIN graph_nodes n ON e.from_node = n.id
                WHERE e.to_node = ?
            """
            if edge_type:
                query += " AND e.edge_type = ?"
                cursor.execute(query, (pk, edge_type))
            else:
                cursor.execute(query, (pk,))
            
            neighbors.extend(cursor.fetchall())
        
        return neighbors
    
    def find_path(self, from_type, from_id, to_type, to_id, max_depth=5):
        """Find shortest path between two nodes (BFS)"""
        from_pk = self.get_node_pk(from_type, from_id)
        to_pk = self.get_node_pk(to_type, to_id)
        
        if not from_pk or not to_pk:
            return None
        
        if from_pk == to_pk:
            return []
        
        # BFS
        queue = deque([(from_pk, [])])
        visited = {from_pk}
        
        while queue and len(queue[0][1]) < max_depth:
            current_pk, path = queue.popleft()
            
            # Get all neighbors
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT to_node, edge_type FROM graph_edges WHERE from_node = ?
                UNION
                SELECT from_node, edge_type FROM graph_edges WHERE to_node = ?
            """, (current_pk, current_pk))
            
            for neighbor_pk, edge_type in cursor.fetchall():
                if neighbor_pk in visited:
                    continue
                
                new_path = path + [(current_pk, edge_type, neighbor_pk)]
                
                if neighbor_pk == to_pk:
                    return new_path
                
                visited.add(neighbor_pk)
                queue.append((neighbor_pk, new_path))
        
        return None  # No path found
    
    def get_subgraph(self, node_type, node_id, max_depth=2):
        """Get subgraph around a node"""
        pk = self.get_node_pk(node_type, node_id)
        if not pk:
            return {'nodes': [], 'edges': []}
        
        visited_nodes = set()
        edges = []
        
        # BFS to collect nodes and edges
        queue = deque([(pk, 0)])
        visited_nodes.add(pk)
        
        while queue:
            current_pk, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Get edges
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT from_node, to_node, edge_type, weight
                FROM graph_edges
                WHERE from_node = ? OR to_node = ?
            """, (current_pk, current_pk))
            
            for from_pk, to_pk, edge_type, weight in cursor.fetchall():
                edges.append({
                    'from': from_pk,
                    'to': to_pk,
                    'type': edge_type,
                    'weight': weight
                })
                
                # Add neighbor to queue
                neighbor = to_pk if from_pk == current_pk else from_pk
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        # Get node details
        cursor.execute("""
            SELECT id, node_type, node_id, label
            FROM graph_nodes
            WHERE id IN ({})
        """.format(','.join('?' * len(visited_nodes))), tuple(visited_nodes))
        
        nodes = [
            {
                'pk': row[0],
                'type': row[1],
                'id': row[2],
                'label': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        return {'nodes': nodes, 'edges': edges}
    
    def get_stats(self):
        """Get graph statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM graph_nodes")
        node_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM graph_edges")
        edge_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT node_type, COUNT(*) 
            FROM graph_nodes 
            GROUP BY node_type
        """)
        nodes_by_type = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT edge_type, COUNT(*) 
            FROM graph_edges 
            GROUP BY edge_type
        """)
        edges_by_type = dict(cursor.fetchall())
        
        return {
            'total_nodes': node_count,
            'total_edges': edge_count,
            'nodes_by_type': nodes_by_type,
            'edges_by_type': edges_by_type
        }


class FileGraphIntegration:
    """Integrates graph database with File Organizer"""
    
    def __init__(self, file_db):
        self.file_db = file_db
        self.graph = FileGraphStore(file_db.conn)
    
    def build_graph_from_database(self):
        """Build graph from existing file database"""
        cursor = self.file_db.conn.cursor()
        
        # Get all files
        cursor.execute("""
            SELECT id, path, filename, project, ai_tags
            FROM files WHERE status = 'active'
        """)
        
        files = cursor.fetchall()
        
        for file_id, path, filename, project, tags in files:
            # Add file node
            self.graph.add_node('file', str(file_id), label=filename)
            
            # Link to project
            if project:
                self.graph.add_node('project', project, label=project)
                self.graph.add_edge('file', str(file_id), 'project', project, 'belongs_to')
            
            # Link to tags
            if tags:
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag:
                        self.graph.add_node('tag', tag, label=tag)
                        self.graph.add_edge('file', str(file_id), 'tag', tag, 'tagged_with')
        
        # Add file relationships (files accessed together)
        cursor.execute("""
            SELECT file1_id, file2_id, strength
            FROM file_relationships
        """)
        
        for file1, file2, strength in cursor.fetchall():
            self.graph.add_edge(
                'file', str(file1),
                'file', str(file2),
                'related_to',
                weight=strength
            )
        
        return self.graph.get_stats()
    
    def find_all_project_files(self, project_name):
        """Get all files connected to a project"""
        neighbors = self.graph.get_neighbors('project', project_name, direction='in')
        
        file_ids = [int(node_id) for node_type, node_id, label, edge_type, weight in neighbors 
                   if node_type == 'file']
        
        if not file_ids:
            return []
        
        # Get file details
        cursor = self.file_db.conn.cursor()
        placeholders = ','.join('?' * len(file_ids))
        cursor.execute(f"""
            SELECT filename, path, ai_summary
            FROM files
            WHERE id IN ({placeholders})
        """, file_ids)
        
        return [
            {'filename': row[0], 'path': row[1], 'summary': row[2]}
            for row in cursor.fetchall()
        ]
    
    def find_files_by_tag(self, tag):
        """Get all files with a specific tag"""
        neighbors = self.graph.get_neighbors('tag', tag, direction='in')
        
        file_ids = [int(node_id) for node_type, node_id, label, edge_type, weight in neighbors 
                   if node_type == 'file']
        
        if not file_ids:
            return []
        
        cursor = self.file_db.conn.cursor()
        placeholders = ','.join('?' * len(file_ids))
        cursor.execute(f"""
            SELECT filename, path
            FROM files
            WHERE id IN ({placeholders})
        """, file_ids)
        
        return [{'filename': row[0], 'path': row[1]} for row in cursor.fetchall()]


if __name__ == "__main__":
    print("🕸️  Graph Database for File Relationships")
    print("="*60)
    
    # Test with actual database
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    graph_integration = FileGraphIntegration(db)
    
    print("\n1️⃣  Building graph from database...")
    stats = graph_integration.build_graph_from_database()
    
    print(f"   ✅ Graph built!")
    print(f"   📊 Stats:")
    print(f"      • Nodes: {stats['total_nodes']}")
    print(f"      • Edges: {stats['total_edges']}")
    print(f"      • Node types: {stats['nodes_by_type']}")
    print(f"      • Edge types: {stats['edges_by_type']}")
    
    # Test project query
    print("\n2️⃣  Testing graph queries...")
    
    # Get all projects
    cursor = db.conn.cursor()
    cursor.execute("SELECT DISTINCT project FROM files WHERE project IS NOT NULL LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        project = result[0]
        print(f"   🔍 Finding all files for project '{project}'...")
        files = graph_integration.find_all_project_files(project)
        print(f"      Found {len(files)} files")
        for f in files[:3]:
            print(f"      • {f['filename']}")
    
    db.close()
    
    print("\n" + "="*60)
    print("✅ Graph database ready!")
    print("\nFeatures:")
    print("  • Track file relationships")
    print("  • Project-based queries")
    print("  • Tag-based discovery")
    print("  • Path finding between files")
    print("  • Subgraph extraction")

