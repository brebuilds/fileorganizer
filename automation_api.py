#!/usr/bin/env python3
"""
Automation API for File Organizer
Provides REST API endpoints for integration with automation tools:
- n8n
- Make.com (Integromat)
- Zapier
- Custom webhooks
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from urllib.parse import urlparse, parse_qs
import os
from datetime import datetime


class AutomationAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for automation API"""
    
    # Will be set by the server
    file_db = None
    file_ops = None
    conversational_ai = None
    
    def _set_headers(self, status=200, content_type='application/json'):
        """Set response headers"""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, data, status=200):
        """Send JSON response"""
        self._set_headers(status)
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_error(self, message, status=400):
        """Send error response"""
        self._send_json({'error': message, 'success': False}, status)
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API documentation
        if path == '/' or path == '/api':
            self._send_json({
                'name': 'File Organizer Automation API',
                'version': '1.0',
                'endpoints': {
                    'GET /api/health': 'Health check',
                    'GET /api/stats': 'Get file statistics',
                    'GET /api/search?q=query': 'Search files',
                    'GET /api/folders': 'List monitored folders',
                    'POST /api/organize': 'Organize files (body: {folder, type})',
                    'POST /api/tag': 'Tag a file with AI (body: {path})',
                    'POST /api/chat': 'Chat with AI (body: {message})',
                    'POST /api/index': 'Index a folder (body: {path})'
                },
                'integrations': ['n8n', 'Make.com', 'Zapier', 'Hazel', 'Custom webhooks']
            })
        
        # Health check
        elif path == '/api/health':
            self._send_json({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected' if self.file_db else 'not initialized'
            })
        
        # Get statistics
        elif path == '/api/stats':
            if not self.file_db:
                self._send_error('Database not initialized')
                return
            
            stats = self.file_db.get_stats()
            self._send_json({
                'success': True,
                'stats': stats
            })
        
        # Search files
        elif path == '/api/search':
            if not self.file_db:
                self._send_error('Database not initialized')
                return
            
            params = parse_qs(parsed.query)
            query = params.get('q', [''])[0]
            limit = int(params.get('limit', ['20'])[0])
            
            if not query:
                self._send_error('Missing query parameter: q')
                return
            
            results = self.file_db.search_files(query, limit=limit)
            self._send_json({
                'success': True,
                'query': query,
                'count': len(results),
                'results': results
            })
        
        # List monitored folders
        elif path == '/api/folders':
            # Get from config
            from setup_wizard import load_user_profile
            profile = load_user_profile()
            
            if profile:
                folders = profile.get('monitored_folders', [])
                self._send_json({
                    'success': True,
                    'folders': folders
                })
            else:
                self._send_json({
                    'success': True,
                    'folders': [],
                    'message': 'No profile configured yet'
                })
        
        else:
            self._send_error('Endpoint not found', 404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else '{}'
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error('Invalid JSON in request body')
            return
        
        # Organize files
        if path == '/api/organize':
            if not self.file_ops:
                self._send_error('File operations not initialized')
                return
            
            folder = data.get('folder')
            org_type = data.get('type', 'by_type')  # by_type or by_project
            
            if not folder:
                self._send_error('Missing required field: folder')
                return
            
            if not os.path.exists(folder):
                self._send_error(f'Folder not found: {folder}')
                return
            
            try:
                if org_type == 'by_type':
                    results = self.file_ops.organize_by_type(folder)
                elif org_type == 'by_project':
                    from setup_wizard import load_user_profile
                    profile = load_user_profile()
                    
                    # Get files in folder
                    cursor = self.file_db.conn.cursor()
                    cursor.execute("""
                        SELECT id FROM files 
                        WHERE folder_location = ? AND status = 'active'
                    """, (folder,))
                    file_ids = [row[0] for row in cursor.fetchall()]
                    
                    results = self.file_ops.organize_by_project(file_ids, profile)
                else:
                    self._send_error(f'Invalid organization type: {org_type}')
                    return
                
                self._send_json({
                    'success': True,
                    'folder': folder,
                    'type': org_type,
                    'results': results
                })
            except Exception as e:
                self._send_error(f'Organization failed: {str(e)}', 500)
        
        # Tag file with AI
        elif path == '/api/tag':
            if not self.file_db:
                self._send_error('Database not initialized')
                return
            
            file_path = data.get('path')
            
            if not file_path:
                self._send_error('Missing required field: path')
                return
            
            if not os.path.exists(file_path):
                self._send_error(f'File not found: {file_path}')
                return
            
            try:
                from ai_tagger import AITagger
                from setup_wizard import load_user_profile
                
                profile = load_user_profile()
                tagger = AITagger(user_profile=profile)
                
                # Get file info
                cursor = self.file_db.conn.cursor()
                cursor.execute("""
                    SELECT filename, extension, content_text 
                    FROM files WHERE path = ?
                """, (file_path,))
                
                result = cursor.fetchone()
                if result:
                    filename, extension, content = result
                    tags = tagger.tag_file(filename, content or '', extension or '')
                    
                    # Update database
                    cursor.execute("""
                        UPDATE files 
                        SET ai_summary = ?, ai_tags = ?, project = ?
                        WHERE path = ?
                    """, (tags['summary'], ','.join(tags['tags']), tags['project'], file_path))
                    self.file_db.conn.commit()
                    
                    self._send_json({
                        'success': True,
                        'path': file_path,
                        'tags': tags
                    })
                else:
                    self._send_error('File not in database. Index it first.')
            except Exception as e:
                self._send_error(f'Tagging failed: {str(e)}', 500)
        
        # Chat with AI
        elif path == '/api/chat':
            if not self.conversational_ai:
                self._send_error('AI not initialized')
                return
            
            message = data.get('message')
            
            if not message:
                self._send_error('Missing required field: message')
                return
            
            try:
                result = self.conversational_ai.chat(message, [])
                self._send_json({
                    'success': True,
                    'message': message,
                    'response': result['response'],
                    'intent': result['intent']
                })
            except Exception as e:
                self._send_error(f'Chat failed: {str(e)}', 500)
        
        # Index folder
        elif path == '/api/index':
            if not self.file_db:
                self._send_error('Database not initialized')
                return
            
            folder_path = data.get('path')
            recursive = data.get('recursive', True)
            
            if not folder_path:
                self._send_error('Missing required field: path')
                return
            
            if not os.path.exists(folder_path):
                self._send_error(f'Folder not found: {folder_path}')
                return
            
            try:
                from file_indexer import FileIndexer
                
                indexer = FileIndexer(self.file_db)
                indexed, skipped = indexer.scan_folder(folder_path, recursive=recursive)
                
                self._send_json({
                    'success': True,
                    'path': folder_path,
                    'indexed': indexed,
                    'skipped': skipped
                })
            except Exception as e:
                self._send_error(f'Indexing failed: {str(e)}', 500)
        
        else:
            self._send_error('Endpoint not found', 404)
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[API] {self.address_string()} - {format % args}")


class AutomationAPIServer:
    """API server for automation integrations"""
    
    def __init__(self, port=8765, file_db=None, file_ops=None, conversational_ai=None):
        self.port = port
        self.server = None
        self.thread = None
        
        # Set class variables for handler
        AutomationAPIHandler.file_db = file_db
        AutomationAPIHandler.file_ops = file_ops
        AutomationAPIHandler.conversational_ai = conversational_ai
    
    def start(self):
        """Start the API server in background thread"""
        if self.thread and self.thread.is_alive():
            print(f"⚠️  API server already running on port {self.port}")
            return
        
        def run_server():
            self.server = HTTPServer(('localhost', self.port), AutomationAPIHandler)
            print(f"🚀 Automation API server started on http://localhost:{self.port}")
            print(f"📖 API docs: http://localhost:{self.port}/api")
            self.server.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the API server"""
        if self.server:
            self.server.shutdown()
            print("🛑 API server stopped")
    
    def is_running(self):
        """Check if server is running"""
        return self.thread and self.thread.is_alive()


if __name__ == "__main__":
    # Test the API server
    print("Testing Automation API Server...")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    
    # Start server
    api = AutomationAPIServer(port=8765, file_db=db)
    api.start()
    
    print("\n✅ Server is running!")
    print("\nTry these endpoints:")
    print("  • http://localhost:8765/api")
    print("  • http://localhost:8765/api/health")
    print("  • http://localhost:8765/api/stats")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Keep running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping server...")
        api.stop()
        db.close()

