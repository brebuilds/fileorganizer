#!/usr/bin/env python3
"""
Export Manager - Generate index files of all records
Supports multiple formats: JSON, CSV, HTML, Markdown
"""

import json
import csv
from datetime import datetime
from pathlib import Path
import os


class ExportManager:
    """Exports file database to various formats"""
    
    def __init__(self, file_db):
        self.file_db = file_db
    
    def export_to_json(self, output_path=None, include_content=False):
        """
        Export complete index to JSON
        
        Args:
            output_path: Where to save (default: ~/.fileorganizer/exports/)
            include_content: Include full file content (makes file large)
        """
        if output_path is None:
            export_dir = os.path.expanduser("~/.fileorganizer/exports")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(export_dir, f"file_index_{timestamp}.json")
        
        cursor = self.file_db.conn.cursor()
        
        # Build query based on whether to include content
        if include_content:
            query = """
                SELECT id, path, filename, extension, size, 
                       created_date, modified_date, last_indexed,
                       mime_type, folder_location, content_text,
                       ai_summary, ai_tags, project, status,
                       access_count, last_accessed
                FROM files WHERE status = 'active'
                ORDER BY filename
            """
        else:
            query = """
                SELECT id, path, filename, extension, size, 
                       created_date, modified_date, last_indexed,
                       mime_type, folder_location,
                       ai_summary, ai_tags, project, status,
                       access_count, last_accessed
                FROM files WHERE status = 'active'
                ORDER BY filename
            """
        
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description]
        files = []
        
        for row in cursor.fetchall():
            file_data = dict(zip(columns, row))
            
            # Get tags for this file
            cursor.execute("SELECT tag FROM tags WHERE file_id = ?", (file_data['id'],))
            file_data['tags_list'] = [tag[0] for tag in cursor.fetchall()]
            
            files.append(file_data)
        
        # Get statistics
        stats = self.file_db.get_stats()
        
        # Get learned patterns
        patterns = self.file_db.get_learned_patterns()
        
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_files': len(files),
                'database_stats': stats,
                'learned_patterns_count': len(patterns),
                'content_included': include_content
            },
            'files': files,
            'statistics': stats,
            'learned_patterns': patterns[:20]  # Top 20 patterns
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_path, len(files)
    
    def export_to_csv(self, output_path=None):
        """Export to CSV format (spreadsheet-friendly)"""
        if output_path is None:
            export_dir = os.path.expanduser("~/.fileorganizer/exports")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(export_dir, f"file_index_{timestamp}.csv")
        
        cursor = self.file_db.conn.cursor()
        cursor.execute("""
            SELECT filename, extension, size, modified_date, 
                   folder_location, ai_summary, ai_tags, project,
                   access_count, path
            FROM files WHERE status = 'active'
            ORDER BY filename
        """)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Filename', 'Extension', 'Size (bytes)', 'Modified Date',
                'Location', 'Summary', 'Tags', 'Project', 
                'Access Count', 'Full Path'
            ])
            
            # Data
            for row in cursor.fetchall():
                writer.writerow(row)
        
        cursor.execute("SELECT COUNT(*) FROM files WHERE status = 'active'")
        count = cursor.fetchone()[0]
        
        return output_path, count
    
    def export_to_html(self, output_path=None):
        """Export to beautiful HTML catalog"""
        if output_path is None:
            export_dir = os.path.expanduser("~/.fileorganizer/exports")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(export_dir, f"file_index_{timestamp}.html")
        
        cursor = self.file_db.conn.cursor()
        cursor.execute("""
            SELECT filename, extension, size, modified_date, 
                   folder_location, ai_summary, ai_tags, project,
                   access_count, path
            FROM files WHERE status = 'active'
            ORDER BY filename
        """)
        
        files = cursor.fetchall()
        stats = self.file_db.get_stats()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>File Index - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1400px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .search-box {{
            margin-bottom: 20px;
        }}
        .search-box input {{
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-collapse: collapse;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f8f9ff;
        }}
        .tag {{
            display: inline-block;
            background: #e0e7ff;
            color: #4c51bf;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin: 2px;
        }}
        .project {{
            color: #667eea;
            font-weight: 600;
        }}
        .summary {{
            color: #666;
            font-size: 14px;
            max-width: 400px;
        }}
    </style>
    <script>
        function searchFiles() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('filesTable');
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td');
                let txtValue = '';
                for (let j = 0; j < td.length; j++) {{
                    txtValue += td[j].textContent || td[j].innerText;
                }}
                if (txtValue.toLowerCase().indexOf(filter) > -1) {{
                    tr[i].style.display = '';
                }} else {{
                    tr[i].style.display = 'none';
                }}
            }}
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>📁 File Index</h1>
        <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Total Files</h3>
            <div class="value">{stats['total_files']}</div>
        </div>
        <div class="stat-card">
            <h3>Folders Monitored</h3>
            <div class="value">{len(stats.get('by_folder', {}))}</div>
        </div>
        <div class="stat-card">
            <h3>File Types</h3>
            <div class="value">{len(stats.get('by_extension', {}))}</div>
        </div>
        <div class="stat-card">
            <h3>Tagged Files</h3>
            <div class="value">{len(stats.get('top_tags', {}))}</div>
        </div>
    </div>
    
    <div class="search-box">
        <input type="text" id="searchInput" onkeyup="searchFiles()" 
               placeholder="🔍 Search files, tags, projects...">
    </div>
    
    <table id="filesTable">
        <thead>
            <tr>
                <th>Filename</th>
                <th>Summary</th>
                <th>Tags</th>
                <th>Project</th>
                <th>Location</th>
                <th>Modified</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for row in files:
            filename, ext, size, modified, location, summary, tags, project, access_count, path = row
            
            # Format tags
            tags_html = ''
            if tags:
                for tag in tags.split(','):
                    tags_html += f'<span class="tag">{tag.strip()}</span> '
            
            # Format project
            project_html = f'<span class="project">{project}</span>' if project else '-'
            
            # Format summary
            summary_html = f'<div class="summary">{summary}</div>' if summary else '-'
            
            # Shorten location
            location_short = Path(location).name if location else '-'
            
            html += f"""
            <tr>
                <td><strong>{filename}</strong></td>
                <td>{summary_html}</td>
                <td>{tags_html if tags_html else '-'}</td>
                <td>{project_html}</td>
                <td>{location_short}</td>
                <td>{modified[:10] if modified else '-'}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        return output_path, len(files)
    
    def export_to_markdown(self, output_path=None):
        """Export to Markdown format"""
        if output_path is None:
            export_dir = os.path.expanduser("~/.fileorganizer/exports")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(export_dir, f"file_index_{timestamp}.md")
        
        cursor = self.file_db.conn.cursor()
        cursor.execute("""
            SELECT filename, extension, folder_location, 
                   ai_summary, ai_tags, project, modified_date
            FROM files WHERE status = 'active'
            ORDER BY project, filename
        """)
        
        files = cursor.fetchall()
        stats = self.file_db.get_stats()
        
        md = f"""# 📁 File Index

Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

## 📊 Statistics

- **Total Files**: {stats['total_files']}
- **Folders Monitored**: {len(stats.get('by_folder', {}))}
- **File Types**: {len(stats.get('by_extension', {}))}

## 📂 Files by Project

"""
        
        # Group by project
        by_project = {}
        for row in files:
            filename, ext, location, summary, tags, project, modified = row
            project_key = project or "Uncategorized"
            
            if project_key not in by_project:
                by_project[project_key] = []
            by_project[project_key].append(row)
        
        # Write each project section
        for project, project_files in sorted(by_project.items()):
            md += f"\n### {project}\n\n"
            
            for row in project_files:
                filename, ext, location, summary, tags, _, modified = row
                
                md += f"**{filename}**\n"
                if summary:
                    md += f"- Summary: {summary}\n"
                if tags:
                    md += f"- Tags: {tags}\n"
                md += f"- Location: {Path(location).name if location else 'Unknown'}\n"
                md += f"- Modified: {modified[:10] if modified else 'Unknown'}\n"
                md += "\n"
        
        with open(output_path, 'w') as f:
            f.write(md)
        
        return output_path, len(files)
    
    def export_all_formats(self):
        """Export to all supported formats"""
        results = {}
        
        print("📤 Exporting file index to all formats...")
        
        # JSON
        print("  → JSON...", end=" ")
        json_path, json_count = self.export_to_json()
        results['json'] = {'path': json_path, 'count': json_count}
        print(f"✅ {json_count} files")
        
        # CSV
        print("  → CSV...", end=" ")
        csv_path, csv_count = self.export_to_csv()
        results['csv'] = {'path': csv_path, 'count': csv_count}
        print(f"✅ {csv_count} files")
        
        # HTML
        print("  → HTML...", end=" ")
        html_path, html_count = self.export_to_html()
        results['html'] = {'path': html_path, 'count': html_count}
        print(f"✅ {html_count} files")
        
        # Markdown
        print("  → Markdown...", end=" ")
        md_path, md_count = self.export_to_markdown()
        results['markdown'] = {'path': md_path, 'count': md_count}
        print(f"✅ {md_count} files")
        
        return results


if __name__ == "__main__":
    print("📤 File Index Export Manager")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    exporter = ExportManager(db)
    
    print("\nExporting to all formats...\n")
    results = exporter.export_all_formats()
    
    print("\n" + "="*60)
    print("✅ Export complete!")
    print("\nGenerated files:")
    for format_name, info in results.items():
        print(f"  • {format_name.upper()}: {info['path']}")
    
    print(f"\nLocation: ~/.fileorganizer/exports/")
    print("Open HTML file in browser for interactive catalog!")
    
    db.close()

