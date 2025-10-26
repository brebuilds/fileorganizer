#!/usr/bin/env python3
"""
Setup Wizard for File Organizer
Collects user information on first launch
"""

import json
import os
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QCheckBox, QRadioButton,
    QButtonGroup, QPushButton, QWidget, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from cloud_storage import CloudStorageDetector


class WelcomePage(QWizardPage):
    """Welcome page"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to File Organizer!")
        
        layout = QVBoxLayout()
        
        # Welcome message
        welcome = QLabel(
            "Let's get you organized! 🎉\n\n"
            "This quick setup will customize the app for your needs.\n\n"
            "Your information stays private on your computer - "
            "nothing is sent to any servers."
        )
        welcome.setWordWrap(True)
        welcome_font = QFont()
        welcome_font.setPointSize(13)
        welcome.setFont(welcome_font)
        
        layout.addWidget(welcome)
        layout.addStretch()
        
        self.setLayout(layout)


class AboutYouPage(QWizardPage):
    """Collect basic info about the user"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("About You")
        self.setSubTitle("Help me understand what you do")
        
        layout = QVBoxLayout()
        
        # Name
        name_label = QLabel("What should I call you?")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your name or nickname")
        
        # Job/Role
        job_label = QLabel("What do you do?")
        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("e.g., Designer, Developer, Consultant, Student...")
        
        # Industry (optional)
        industry_label = QLabel("Industry or field? (optional)")
        self.industry_input = QLineEdit()
        self.industry_input.setPlaceholderText("e.g., Marketing, Tech, Healthcare...")
        
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addSpacing(15)
        layout.addWidget(job_label)
        layout.addWidget(self.job_input)
        layout.addSpacing(15)
        layout.addWidget(industry_label)
        layout.addWidget(self.industry_input)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Register fields for validation
        self.registerField("name*", self.name_input)
        self.registerField("job*", self.job_input)
        self.registerField("industry", self.industry_input)


class YourWorkPage(QWizardPage):
    """Collect info about projects/clients"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Your Work")
        self.setSubTitle("Tell me about your projects, clients, or areas of focus")
        
        layout = QVBoxLayout()
        
        # Projects/Clients
        projects_label = QLabel(
            "Main projects, clients, or brands you work with:\n"
            "(One per line - these will help me organize your files)"
        )
        self.projects_input = QTextEdit()
        self.projects_input.setPlaceholderText(
            "Examples:\n"
            "ClientA\n"
            "Brand X\n"
            "Personal Projects\n"
            "Side Hustle"
        )
        self.projects_input.setMaximumHeight(150)
        
        layout.addWidget(projects_label)
        layout.addWidget(self.projects_input)
        layout.addStretch()
        
        self.setLayout(layout)
        
        self.registerField("projects", self.projects_input, "plainText")


class FileLocationsPage(QWizardPage):
    """Select which folders to monitor - includes cloud storage detection"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("File Locations")
        self.setSubTitle("Which folders should I help organize?")
        self.custom_folders = []
        self.cloud_checkboxes = {}
        
        # Detect cloud storage
        self.cloud_detector = CloudStorageDetector()
        
        # Main layout with scroll area for many options
        main_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        
        # Standard locations section
        standard_label = QLabel("<b>Standard Locations:</b>")
        layout.addWidget(standard_label)
        
        self.downloads_check = QCheckBox("~/Downloads")
        self.downloads_check.setChecked(True)
        
        self.desktop_check = QCheckBox("~/Desktop")
        self.desktop_check.setChecked(True)
        
        self.documents_check = QCheckBox("~/Documents")
        self.documents_check.setChecked(True)
        
        self.pictures_check = QCheckBox("~/Pictures")
        self.movies_check = QCheckBox("~/Movies")
        self.music_check = QCheckBox("~/Music")
        
        layout.addWidget(self.downloads_check)
        layout.addWidget(self.desktop_check)
        layout.addWidget(self.documents_check)
        layout.addWidget(self.pictures_check)
        layout.addWidget(self.movies_check)
        layout.addWidget(self.music_check)
        
        # Cloud storage section
        if self.cloud_detector.detected_services:
            layout.addSpacing(15)
            cloud_label = QLabel("<b>☁️ Cloud Storage (Auto-detected):</b>")
            layout.addWidget(cloud_label)
            
            for service_name, service_info in self.cloud_detector.detected_services.items():
                checkbox = QCheckBox(f"{service_info['icon']} {service_name}")
                checkbox.setChecked(True)  # Default: monitor cloud storage
                checkbox.setToolTip(service_info['path'])
                layout.addWidget(checkbox)
                
                # Store reference to cloud checkbox
                self.cloud_checkboxes[service_name] = {
                    'checkbox': checkbox,
                    'path': service_info['path']
                }
                
                # Add iCloud subfolders as separate options
                if 'subfolders' in service_info:
                    for subfolder_name, subfolder_path in service_info['subfolders'].items():
                        if subfolder_path:
                            sub_check = QCheckBox(f"   → iCloud {subfolder_name}")
                            sub_check.setChecked(True)
                            sub_check.setToolTip(subfolder_path)
                            layout.addWidget(sub_check)
                            
                            # Store subfolder reference
                            self.cloud_checkboxes[f"iCloud_{subfolder_name}"] = {
                                'checkbox': sub_check,
                                'path': subfolder_path
                            }
        else:
            layout.addSpacing(15)
            no_cloud_label = QLabel("💡 No cloud storage detected\n"
                                   "Supported: Dropbox, iCloud, Google Drive,\n"
                                   "OneDrive, Box, MEGA, Sync.com, pCloud")
            no_cloud_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_cloud_label)
        
        # Custom folders section
        layout.addSpacing(15)
        custom_label = QLabel("<b>Custom Folders:</b>")
        layout.addWidget(custom_label)
        
        self.custom_list = QTextEdit()
        self.custom_list.setPlaceholderText(
            "Add custom folder paths (one per line):\n"
            "/Users/bre/Projects\n"
            "/Volumes/ExternalDrive/Work\n"
            "~/AnyFolder/Subfolder"
        )
        self.custom_list.setMaximumHeight(100)
        
        add_folder_btn = QPushButton("📁 Browse for Folder...")
        add_folder_btn.clicked.connect(self.browse_folder)
        
        layout.addWidget(self.custom_list)
        layout.addWidget(add_folder_btn)
        
        layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
        
        # Register fields
        self.registerField("monitor_downloads", self.downloads_check)
        self.registerField("monitor_desktop", self.desktop_check)
        self.registerField("monitor_documents", self.documents_check)
        self.registerField("monitor_pictures", self.pictures_check)
        self.registerField("monitor_movies", self.movies_check)
        self.registerField("monitor_music", self.music_check)
        self.registerField("custom_folders", self.custom_list, "plainText")
    
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Monitor",
            os.path.expanduser("~")
        )
        
        if folder:
            current = self.custom_list.toPlainText()
            if current:
                self.custom_list.setPlainText(current + "\n" + folder)
            else:
                self.custom_list.setPlainText(folder)


class FileTypesPage(QWizardPage):
    """Ask about file types"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("File Types")
        self.setSubTitle("What kinds of files do you work with most?")
        
        layout = QVBoxLayout()
        
        info = QLabel("Select all that apply:")
        layout.addWidget(info)
        layout.addSpacing(10)
        
        # Common file types
        self.pdfs_check = QCheckBox("PDFs (documents, invoices, reports)")
        self.pdfs_check.setChecked(True)
        
        self.images_check = QCheckBox("Images & Screenshots")
        self.images_check.setChecked(True)
        
        self.docs_check = QCheckBox("Word/Pages documents")
        
        self.spreadsheets_check = QCheckBox("Excel/Numbers spreadsheets")
        
        self.presentations_check = QCheckBox("PowerPoint/Keynote presentations")
        
        self.code_check = QCheckBox("Code files")
        
        self.other_input = QLineEdit()
        self.other_input.setPlaceholderText("Other types (comma-separated)...")
        
        layout.addWidget(self.pdfs_check)
        layout.addWidget(self.images_check)
        layout.addWidget(self.docs_check)
        layout.addWidget(self.spreadsheets_check)
        layout.addWidget(self.presentations_check)
        layout.addWidget(self.code_check)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Other:"))
        layout.addWidget(self.other_input)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self.registerField("ft_pdfs", self.pdfs_check)
        self.registerField("ft_images", self.images_check)
        self.registerField("ft_docs", self.docs_check)
        self.registerField("ft_spreadsheets", self.spreadsheets_check)
        self.registerField("ft_presentations", self.presentations_check)
        self.registerField("ft_code", self.code_check)
        self.registerField("ft_other", self.other_input)


class OrganizationStylePage(QWizardPage):
    """Ask about organization preferences"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Organization Style")
        self.setSubTitle("How do you naturally think about your files?")
        
        layout = QVBoxLayout()
        
        info = QLabel("When you're looking for a file, you usually think:")
        layout.addWidget(info)
        layout.addSpacing(10)
        
        self.style_group = QButtonGroup()
        
        self.by_project = QRadioButton("By project/client (\"I need the file from Project X\")")
        self.by_project.setChecked(True)  # Default
        
        self.by_type = QRadioButton("By type (\"I need that invoice\" or \"I need that screenshot\")")
        
        self.by_time = QRadioButton("By time (\"I need something from last week\")")
        
        self.by_status = QRadioButton("By status (\"I need something I'm working on\" or \"done\")")
        
        self.style_group.addButton(self.by_project, 1)
        self.style_group.addButton(self.by_type, 2)
        self.style_group.addButton(self.by_time, 3)
        self.style_group.addButton(self.by_status, 4)
        
        layout.addWidget(self.by_project)
        layout.addWidget(self.by_type)
        layout.addWidget(self.by_time)
        layout.addWidget(self.by_status)
        
        layout.addStretch()
        self.setLayout(layout)
        
        self.registerField("org_style", self.by_project)


class PainPointsPage(QWizardPage):
    """Ask about specific challenges"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Your Biggest Challenge")
        self.setSubTitle("What's the most frustrating thing about file organization for you?")
        
        layout = QVBoxLayout()
        
        self.pain_input = QTextEdit()
        self.pain_input.setPlaceholderText(
            "Be honest! Examples:\n\n"
            "- I can never find anything when I need it\n"
            "- Files pile up with terrible names like 'Document(3).pdf'\n"
            "- Everything ends up in Downloads and I forget about it\n"
            "- I start organizing but never finish\n"
            "- I have 5 different systems and none of them work"
        )
        self.pain_input.setMaximumHeight(200)
        
        layout.addWidget(self.pain_input)
        layout.addStretch()
        
        self.setLayout(layout)
        
        self.registerField("pain_points", self.pain_input, "plainText")


class FinalPage(QWizardPage):
    """Final confirmation page"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("All Set! 🎉")
        
        layout = QVBoxLayout()
        
        message = QLabel(
            "Perfect! I now understand your situation.\n\n"
            "Your personal AI assistant is ready to help you:\n"
            "• Find files when you need them\n"
            "• Organize the chaos automatically\n"
            "• Keep things manageable\n\n"
            "Click Finish to start organizing!\n\n"
            "PS: You can update these settings anytime by clicking\n"
            "the gear icon in the menu bar."
        )
        message.setWordWrap(True)
        message_font = QFont()
        message_font.setPointSize(12)
        message.setFont(message_font)
        
        layout.addWidget(message)
        layout.addStretch()
        
        self.setLayout(layout)


class SetupWizard(QWizard):
    """Main setup wizard"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("File Organizer - Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage)
        
        # Set minimum size
        self.setMinimumSize(600, 500)
        
        # Add pages
        self.addPage(WelcomePage())
        self.addPage(AboutYouPage())
        self.addPage(YourWorkPage())
        self.addPage(FileLocationsPage())
        self.addPage(FileTypesPage())
        self.addPage(OrganizationStylePage())
        self.addPage(PainPointsPage())
        self.addPage(FinalPage())
        
        # Custom button text
        self.setButtonText(QWizard.WizardButton.FinishButton, "Let's Go!")
    
    def get_user_profile(self):
        """Extract all collected data into a profile dict"""
        
        # Get organization style
        style_map = {
            1: "project",
            2: "type", 
            3: "time",
            4: "status"
        }
        
        # Find checked radio button
        org_style = "project"  # default
        for page_id in self.pageIds():
            page = self.page(page_id)
            if isinstance(page, OrganizationStylePage):
                checked_id = page.style_group.checkedId()
                org_style = style_map.get(checked_id, "project")
                break
        
        # Collect file types
        file_types = []
        if self.field("ft_pdfs"):
            file_types.append("PDFs")
        if self.field("ft_images"):
            file_types.append("Images/Screenshots")
        if self.field("ft_docs"):
            file_types.append("Word/Pages documents")
        if self.field("ft_spreadsheets"):
            file_types.append("Spreadsheets")
        if self.field("ft_presentations"):
            file_types.append("Presentations")
        if self.field("ft_code"):
            file_types.append("Code files")
        
        other = self.field("ft_other")
        if other:
            file_types.extend([t.strip() for t in other.split(",") if t.strip()])
        
        # Collect monitored folders with full paths
        import os
        folders = []
        
        # Standard folders
        if self.field("monitor_downloads"):
            folders.append(os.path.expanduser("~/Downloads"))
        if self.field("monitor_desktop"):
            folders.append(os.path.expanduser("~/Desktop"))
        if self.field("monitor_documents"):
            folders.append(os.path.expanduser("~/Documents"))
        if self.field("monitor_pictures"):
            folders.append(os.path.expanduser("~/Pictures"))
        if self.field("monitor_movies"):
            folders.append(os.path.expanduser("~/Movies"))
        if self.field("monitor_music"):
            folders.append(os.path.expanduser("~/Music"))
        
        # Cloud storage folders
        for page_id in self.pageIds():
            page = self.page(page_id)
            if isinstance(page, FileLocationsPage):
                for service_name, service_data in page.cloud_checkboxes.items():
                    if service_data['checkbox'].isChecked():
                        path = service_data['path']
                        if os.path.exists(path) and os.path.isdir(path):
                            folders.append(path)
                break
        
        # Add custom folders
        custom_text = self.field("custom_folders")
        if custom_text:
            custom_paths = [p.strip() for p in custom_text.split("\n") if p.strip()]
            for path in custom_paths:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded) and os.path.isdir(expanded):
                    folders.append(expanded)
        
        # Parse projects (one per line)
        projects_text = self.field("projects")
        projects = [p.strip() for p in projects_text.split("\n") if p.strip()]
        
        profile = {
            "name": self.field("name"),
            "job": self.field("job"),
            "industry": self.field("industry") or "Not specified",
            "projects": projects,
            "monitored_folders": folders,
            "file_types": file_types,
            "organization_style": org_style,
            "pain_points": self.field("pain_points"),
            "setup_completed": True
        }
        
        return profile


def get_config_path():
    """Get the path to config file"""
    config_dir = os.path.expanduser("~/.fileorganizer")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def save_user_profile(profile):
    """Save user profile to config file"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(profile, f, indent=2)
    print(f"Profile saved to {config_path}")


def load_user_profile():
    """Load user profile from config file"""
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None


def needs_setup():
    """Check if setup wizard needs to run"""
    profile = load_user_profile()
    return profile is None or not profile.get("setup_completed", False)


if __name__ == "__main__":
    # Test the wizard
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    
    if wizard.exec():
        profile = wizard.get_user_profile()
        save_user_profile(profile)
        print("Setup completed!")
        print(json.dumps(profile, indent=2))
    else:
        print("Setup cancelled")
    
    sys.exit()