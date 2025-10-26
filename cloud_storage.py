#!/usr/bin/env python3
"""
Cloud Storage Integration
Detects and manages cloud storage folders (Dropbox, iCloud, Google Drive, OneDrive, etc.)
"""

import os
from pathlib import Path


class CloudStorageDetector:
    """Detects installed cloud storage services and their sync folders"""
    
    def __init__(self):
        self.home = Path.home()
        self.detected_services = {}
        self.detect_all()
    
    def detect_all(self):
        """Detect all available cloud storage services"""
        self.detect_dropbox()
        self.detect_icloud()
        self.detect_google_drive()
        self.detect_onedrive()
        self.detect_box()
        self.detect_mega()
        self.detect_sync_com()
        self.detect_pcloud()
        
        return self.detected_services
    
    def detect_dropbox(self):
        """Detect Dropbox"""
        # Standard Dropbox location
        standard = self.home / "Dropbox"
        
        # Check info.json for custom location
        info_paths = [
            self.home / ".dropbox" / "info.json",
            self.home / "Library" / "Application Support" / "Dropbox" / "info.json"
        ]
        
        for info_path in info_paths:
            if info_path.exists():
                try:
                    import json
                    with open(info_path) as f:
                        data = json.load(f)
                        if 'personal' in data and 'path' in data['personal']:
                            path = Path(data['personal']['path'])
                            if path.exists():
                                self.detected_services['Dropbox'] = {
                                    'path': str(path),
                                    'icon': '📦',
                                    'type': 'sync',
                                    'active': True
                                }
                                return
                except:
                    pass
        
        # Fallback to standard location
        if standard.exists() and standard.is_dir():
            self.detected_services['Dropbox'] = {
                'path': str(standard),
                'icon': '📦',
                'type': 'sync',
                'active': True
            }
    
    def detect_icloud(self):
        """Detect iCloud Drive"""
        # iCloud Drive locations
        icloud_paths = [
            self.home / "Library" / "Mobile Documents" / "com~apple~CloudDocs",
            self.home / "iCloud Drive"
        ]
        
        for path in icloud_paths:
            if path.exists() and path.is_dir():
                self.detected_services['iCloud Drive'] = {
                    'path': str(path),
                    'icon': '☁️',
                    'type': 'sync',
                    'active': True,
                    'subfolders': {
                        'Desktop': str(path / "Desktop") if (path / "Desktop").exists() else None,
                        'Documents': str(path / "Documents") if (path / "Documents").exists() else None,
                        'Downloads': str(path / "Downloads") if (path / "Downloads").exists() else None
                    }
                }
                return
    
    def detect_google_drive(self):
        """Detect Google Drive"""
        # Google Drive locations (both old and new apps)
        drive_paths = [
            self.home / "Google Drive",
            self.home / "GoogleDrive",
            self.home / "Library" / "CloudStorage" / "GoogleDrive",
        ]
        
        # Check for Google Drive Stream/File Stream
        cloud_storage = self.home / "Library" / "CloudStorage"
        if cloud_storage.exists():
            for item in cloud_storage.iterdir():
                if 'GoogleDrive' in item.name:
                    drive_paths.append(item)
        
        for path in drive_paths:
            if path.exists() and path.is_dir():
                # Check for "My Drive" subfolder
                my_drive = path / "My Drive"
                final_path = my_drive if my_drive.exists() else path
                
                self.detected_services['Google Drive'] = {
                    'path': str(final_path),
                    'icon': '🔵',
                    'type': 'sync',
                    'active': True
                }
                return
    
    def detect_onedrive(self):
        """Detect Microsoft OneDrive"""
        onedrive_paths = [
            self.home / "OneDrive",
            self.home / "OneDrive - Personal",
            self.home / "Library" / "CloudStorage" / "OneDrive-Personal"
        ]
        
        # Check for business/work accounts
        cloud_storage = self.home / "Library" / "CloudStorage"
        if cloud_storage.exists():
            for item in cloud_storage.iterdir():
                if 'OneDrive' in item.name:
                    onedrive_paths.append(item)
        
        for path in onedrive_paths:
            if path.exists() and path.is_dir():
                name = "OneDrive"
                if "Personal" in str(path):
                    name = "OneDrive (Personal)"
                elif any(x in str(path) for x in ["Business", "Work", "Company"]):
                    name = "OneDrive (Business)"
                
                self.detected_services[name] = {
                    'path': str(path),
                    'icon': '🔷',
                    'type': 'sync',
                    'active': True
                }
                # Only return first one to avoid duplicates
                return
    
    def detect_box(self):
        """Detect Box"""
        box_paths = [
            self.home / "Box",
            self.home / "Box Sync",
            self.home / "Library" / "CloudStorage" / "Box-Box"
        ]
        
        for path in box_paths:
            if path.exists() and path.is_dir():
                self.detected_services['Box'] = {
                    'path': str(path),
                    'icon': '📫',
                    'type': 'sync',
                    'active': True
                }
                return
    
    def detect_mega(self):
        """Detect MEGA"""
        mega_paths = [
            self.home / "MEGA",
            self.home / "MEGAsync"
        ]
        
        for path in mega_paths:
            if path.exists() and path.is_dir():
                self.detected_services['MEGA'] = {
                    'path': str(path),
                    'icon': '🔴',
                    'type': 'sync',
                    'active': True
                }
                return
    
    def detect_sync_com(self):
        """Detect Sync.com"""
        sync_path = self.home / "Sync"
        
        if sync_path.exists() and sync_path.is_dir():
            self.detected_services['Sync.com'] = {
                'path': str(sync_path),
                'icon': '🔄',
                'type': 'sync',
                'active': True
            }
    
    def detect_pcloud(self):
        """Detect pCloud"""
        pcloud_paths = [
            self.home / "pCloudDrive",
            self.home / "pCloud Drive",
            Path("/Volumes/pCloud Drive")
        ]
        
        for path in pcloud_paths:
            if path.exists() and path.is_dir():
                self.detected_services['pCloud'] = {
                    'path': str(path),
                    'icon': '💾',
                    'type': 'mount',
                    'active': True
                }
                return
    
    def get_all_paths(self):
        """Get all detected cloud storage paths"""
        return [info['path'] for info in self.detected_services.values()]
    
    def get_service_info(self, service_name):
        """Get info about a specific service"""
        return self.detected_services.get(service_name)
    
    def is_cloud_path(self, path):
        """Check if a path is inside any cloud storage folder"""
        path = Path(path).resolve()
        for service_info in self.detected_services.values():
            service_path = Path(service_info['path']).resolve()
            try:
                path.relative_to(service_path)
                return True
            except ValueError:
                continue
        return False
    
    def get_service_for_path(self, path):
        """Get which cloud service a path belongs to"""
        path = Path(path).resolve()
        for service_name, service_info in self.detected_services.items():
            service_path = Path(service_info['path']).resolve()
            try:
                path.relative_to(service_path)
                return service_name
            except ValueError:
                continue
        return None


def get_cloud_storage_summary():
    """Get a formatted summary of detected cloud storage"""
    detector = CloudStorageDetector()
    
    if not detector.detected_services:
        return "No cloud storage services detected"
    
    summary = "Detected Cloud Storage:\n"
    for name, info in detector.detected_services.items():
        summary += f"  {info['icon']} {name}: {info['path']}\n"
        
        # Add iCloud subfolders if available
        if 'subfolders' in info:
            for subfolder_name, subfolder_path in info['subfolders'].items():
                if subfolder_path:
                    summary += f"     → {subfolder_name}\n"
    
    return summary


if __name__ == "__main__":
    # Test cloud storage detection
    print("🔍 Detecting Cloud Storage Services...\n")
    
    detector = CloudStorageDetector()
    
    if detector.detected_services:
        print(f"✅ Found {len(detector.detected_services)} cloud storage service(s):\n")
        
        for name, info in detector.detected_services.items():
            print(f"{info['icon']} {name}")
            print(f"   Path: {info['path']}")
            print(f"   Type: {info['type']}")
            
            if 'subfolders' in info:
                print(f"   Subfolders:")
                for subfolder_name, subfolder_path in info['subfolders'].items():
                    if subfolder_path:
                        print(f"      → {subfolder_name}: {subfolder_path}")
            print()
    else:
        print("❌ No cloud storage services detected")
        print("\nSupported services:")
        print("  - Dropbox")
        print("  - iCloud Drive")
        print("  - Google Drive")
        print("  - OneDrive")
        print("  - Box")
        print("  - MEGA")
        print("  - Sync.com")
        print("  - pCloud")
    
    # Test path checking
    print("\n" + "="*60)
    print("Testing path detection:")
    
    test_paths = [
        str(Path.home() / "Dropbox" / "test.txt"),
        str(Path.home() / "Documents" / "test.txt"),
        str(Path.home() / "Google Drive" / "My Drive" / "test.txt")
    ]
    
    for test_path in test_paths:
        is_cloud = detector.is_cloud_path(test_path)
        service = detector.get_service_for_path(test_path)
        print(f"\n{test_path}")
        print(f"  Is cloud storage? {is_cloud}")
        if service:
            print(f"  Service: {service}")

