#!/usr/bin/env python3
"""
GUI Enhancements for File Organizer v4.0
New tabs and features for PyQt6 GUI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QGroupBox, QDialog, QDialogButtonBox, QProgressBar, QMessageBox,
    QListWidgetItem, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, timedelta
import os


class RemindersWidget(QWidget):
    """Widget for managing reminders and nudges"""
    
    def __init__(self, reminder_system):
        super().__init__()
        self.reminder_system = reminder_system
        self.init_ui()
        self.refresh_reminders()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📅 Reminders & Nudges")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Tabs for different types
        from PyQt6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        
        # Due reminders tab
        due_widget = QWidget()
        due_layout = QVBoxLayout()
        self.due_list = QListWidget()
        due_layout.addWidget(QLabel("⏰ Due Reminders:"))
        due_layout.addWidget(self.due_list)
        due_widget.setLayout(due_layout)
        tabs.addTab(due_widget, "Due")
        
        # Upcoming reminders tab
        upcoming_widget = QWidget()
        upcoming_layout = QVBoxLayout()
        self.upcoming_list = QListWidget()
        upcoming_layout.addWidget(QLabel("📅 Upcoming:"))
        upcoming_layout.addWidget(self.upcoming_list)
        upcoming_widget.setLayout(upcoming_layout)
        tabs.addTab(upcoming_widget, "Upcoming")
        
        # Smart nudges tab
        nudges_widget = QWidget()
        nudges_layout = QVBoxLayout()
        self.nudges_list = QListWidget()
        nudges_layout.addWidget(QLabel("💡 Smart Suggestions:"))
        nudges_layout.addWidget(self.nudges_list)
        nudges_widget.setLayout(nudges_layout)
        tabs.addTab(nudges_widget, "Nudges")
        
        layout.addWidget(tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_reminders)
        button_layout.addWidget(refresh_btn)
        
        dismiss_btn = QPushButton("✖️ Dismiss")
        dismiss_btn.clicked.connect(self.dismiss_selected)
        button_layout.addWidget(dismiss_btn)
        
        snooze_btn = QPushButton("⏰ Snooze")
        snooze_btn.clicked.connect(self.snooze_selected)
        button_layout.addWidget(snooze_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def refresh_reminders(self):
        """Refresh all reminder lists"""
        # Due reminders
        self.due_list.clear()
        due = self.reminder_system.get_due_reminders()
        for reminder in due:
            msg = f"{reminder['filename']}: {reminder['message'] or 'Reminder'}"
            self.due_list.addItem(msg)
        
        # Upcoming reminders
        self.upcoming_list.clear()
        upcoming = self.reminder_system.get_upcoming_reminders(days_ahead=7)
        for reminder in upcoming:
            date = datetime.fromisoformat(reminder['reminder_date']).strftime('%m/%d')
            msg = f"[{date}] {reminder['filename']}"
            self.upcoming_list.addItem(msg)
        
        # Nudges
        self.nudges_list.clear()
        nudges = self.reminder_system.get_nudges(limit=10)
        for nudge in nudges:
            item = QListWidgetItem(nudge['message'])
            if nudge['priority'] >= 8:
                item.setForeground(QColor('#ef4444'))  # Red for high priority
            elif nudge['priority'] >= 6:
                item.setForeground(QColor('#f59e0b'))  # Orange for medium
            self.nudges_list.addItem(item)
    
    def dismiss_selected(self):
        """Dismiss selected reminder"""
        # Implementation would get selected reminder ID and dismiss it
        self.refresh_reminders()
    
    def snooze_selected(self):
        """Snooze selected reminder"""
        # Implementation would snooze selected reminder
        self.refresh_reminders()


class SmartFoldersWidget(QWidget):
    """Widget for managing smart folders"""
    
    def __init__(self, smart_folders):
        super().__init__()
        self.smart_folders = smart_folders
        self.init_ui()
        self.refresh_folders()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📁 Smart Folders")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Folder list
        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.show_folder_contents)
        layout.addWidget(self.folder_list)
        
        # File count label
        self.count_label = QLabel("Select a folder to view contents")
        layout.addWidget(self.count_label)
        
        # Contents list
        self.contents_list = QListWidget()
        layout.addWidget(self.contents_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ New Folder")
        new_btn.clicked.connect(self.create_new_folder)
        button_layout.addWidget(new_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_folders)
        button_layout.addWidget(refresh_btn)
        
        execute_btn = QPushButton("▶️ Execute")
        execute_btn.clicked.connect(self.execute_selected_folder)
        button_layout.addWidget(execute_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def refresh_folders(self):
        """Refresh smart folder list"""
        self.folder_list.clear()
        folders = self.smart_folders.get_all_smart_folders()
        
        for folder in folders:
            count = self.smart_folders.get_file_count(folder['id'])
            item_text = f"{folder['icon']} {folder['name']} ({count} files)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, folder['id'])
            self.folder_list.addItem(item)
    
    def show_folder_contents(self, item):
        """Show contents of selected smart folder"""
        folder_id = item.data(Qt.ItemDataRole.UserRole)
        results = self.smart_folders.execute_smart_folder(folder_id)
        
        self.contents_list.clear()
        self.count_label.setText(f"📊 {len(results)} files in this folder")
        
        for file in results[:50]:  # Limit to 50 for performance
            self.contents_list.addItem(file['filename'])
    
    def execute_selected_folder(self):
        """Execute selected smart folder"""
        current = self.folder_list.currentItem()
        if current:
            self.show_folder_contents(current)
    
    def create_new_folder(self):
        """Show dialog to create new smart folder"""
        # Would show a dialog to create new folder
        QMessageBox.information(self, "Create Smart Folder", "Smart folder creation dialog would appear here")


class BookmarksWidget(QWidget):
    """Widget for managing bookmarks"""
    
    def __init__(self, bookmark_manager):
        super().__init__()
        self.bookmark_manager = bookmark_manager
        self.init_ui()
        self.refresh_bookmarks()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔖 Bookmarks")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.search_bookmarks)
        self.search_box.setPlaceholderText("Search bookmarks...")
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)
        
        # Bookmarks table
        self.bookmarks_table = QTableWidget()
        self.bookmarks_table.setColumnCount(4)
        self.bookmarks_table.setHorizontalHeaderLabels(["Title", "URL", "Tags", "Accessed"])
        header = self.bookmarks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.bookmarks_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Bookmark")
        add_btn.clicked.connect(self.add_bookmark)
        button_layout.addWidget(add_btn)
        
        open_btn = QPushButton("🌐 Open")
        open_btn.clicked.connect(self.open_selected)
        button_layout.addWidget(open_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def refresh_bookmarks(self):
        """Refresh bookmarks table"""
        bookmarks = self.bookmark_manager.get_all_bookmarks(limit=100)
        self.bookmarks_table.setRowCount(len(bookmarks))
        
        for i, bm in enumerate(bookmarks):
            self.bookmarks_table.setItem(i, 0, QTableWidgetItem(bm['title']))
            self.bookmarks_table.setItem(i, 1, QTableWidgetItem(bm['url']))
            self.bookmarks_table.setItem(i, 2, QTableWidgetItem(', '.join(bm['tags'])))
            self.bookmarks_table.setItem(i, 3, QTableWidgetItem(str(bm['access_count'])))
    
    def search_bookmarks(self):
        """Search bookmarks"""
        query = self.search_box.text()
        if query:
            results = self.bookmark_manager.search_bookmarks(query=query)
            self.bookmarks_table.setRowCount(len(results))
            for i, bm in enumerate(results):
                self.bookmarks_table.setItem(i, 0, QTableWidgetItem(bm['title']))
                self.bookmarks_table.setItem(i, 1, QTableWidgetItem(bm['url']))
                self.bookmarks_table.setItem(i, 2, QTableWidgetItem(', '.join(bm['tags'])))
                self.bookmarks_table.setItem(i, 3, QTableWidgetItem(str(bm['access_count'])))
        else:
            self.refresh_bookmarks()
    
    def add_bookmark(self):
        """Add new bookmark"""
        # Would show dialog to add bookmark
        QMessageBox.information(self, "Add Bookmark", "Bookmark creation dialog would appear here")
    
    def open_selected(self):
        """Open selected bookmark in browser"""
        current_row = self.bookmarks_table.currentRow()
        if current_row >= 0:
            url_item = self.bookmarks_table.item(current_row, 1)
            if url_item:
                import webbrowser
                webbrowser.open(url_item.text())
    
    def delete_selected(self):
        """Delete selected bookmark"""
        # Would delete selected bookmark
        QMessageBox.information(self, "Delete", "Delete functionality would be implemented here")


class BulkOperationsDialog(QDialog):
    """Dialog for bulk operations with preview"""
    
    def __init__(self, bulk_ops, file_ids, parent=None):
        super().__init__(parent)
        self.bulk_ops = bulk_ops
        self.file_ids = file_ids
        self.operation_type = None
        self.preview_data = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📦 Bulk Operations")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Operation selection
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("Operation:"))
        
        self.op_combo = QComboBox()
        self.op_combo.addItems(["Rename", "Move", "Delete"])
        self.op_combo.currentTextChanged.connect(self.operation_changed)
        op_layout.addWidget(self.op_combo)
        layout.addLayout(op_layout)
        
        # Operation-specific controls (will be shown/hidden based on operation)
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        layout.addWidget(self.controls_widget)
        
        # Preview area
        layout.addWidget(QLabel("Preview:"))
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.execute_operation)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
    
    def operation_changed(self, operation):
        """Update UI based on selected operation"""
        # Clear previous controls
        for i in reversed(range(self.controls_layout.count())):
            self.controls_layout.itemAt(i).widget().setParent(None)
        
        if operation == "Rename":
            # Add rename controls
            self.controls_layout.addWidget(QLabel("Pattern:"))
            self.pattern_edit = QLineEdit()
            self.controls_layout.addWidget(self.pattern_edit)
            
            self.controls_layout.addWidget(QLabel("Replacement:"))
            self.replacement_edit = QLineEdit()
            self.controls_layout.addWidget(self.replacement_edit)
            
            preview_btn = QPushButton("🔍 Preview")
            preview_btn.clicked.connect(self.preview_rename)
            self.controls_layout.addWidget(preview_btn)
        
        elif operation == "Move":
            # Add move controls
            self.controls_layout.addWidget(QLabel("Destination:"))
            dest_layout = QHBoxLayout()
            self.dest_edit = QLineEdit()
            dest_layout.addWidget(self.dest_edit)
            browse_btn = QPushButton("📁 Browse")
            browse_btn.clicked.connect(self.browse_destination)
            dest_layout.addWidget(browse_btn)
            self.controls_layout.addLayout(dest_layout)
            
            preview_btn = QPushButton("🔍 Preview")
            preview_btn.clicked.connect(self.preview_move)
            self.controls_layout.addWidget(preview_btn)
        
        elif operation == "Delete":
            # Add delete controls
            self.permanent_check = QCheckBox("Permanent delete (cannot undo)")
            self.controls_layout.addWidget(self.permanent_check)
            
            preview_btn = QPushButton("🔍 Preview")
            preview_btn.clicked.connect(self.preview_delete)
            self.controls_layout.addWidget(preview_btn)
    
    def preview_rename(self):
        """Preview rename operation"""
        pattern = self.pattern_edit.text()
        replacement = self.replacement_edit.text()
        
        if not pattern:
            QMessageBox.warning(self, "Error", "Pattern cannot be empty")
            return
        
        self.preview_data = self.bulk_ops.preview_rename(self.file_ids, pattern, replacement)
        self.show_preview()
    
    def preview_move(self):
        """Preview move operation"""
        destination = self.dest_edit.text()
        
        if not destination:
            QMessageBox.warning(self, "Error", "Destination cannot be empty")
            return
        
        self.preview_data = self.bulk_ops.preview_move(self.file_ids, destination)
        self.show_preview()
    
    def preview_delete(self):
        """Preview delete operation"""
        permanent = self.permanent_check.isChecked()
        self.preview_data = self.bulk_ops.preview_delete(self.file_ids, permanent)
        self.show_preview()
    
    def show_preview(self):
        """Show preview in list"""
        self.preview_list.clear()
        
        if isinstance(self.preview_data, list):
            for item in self.preview_data:
                if 'old_name' in item and 'new_name' in item:
                    text = f"{item['old_name']} → {item['new_name']}"
                    if not item.get('safe', True):
                        text += " ⚠️ (target exists)"
                elif 'filename' in item:
                    text = item['filename']
                else:
                    text = str(item)
                
                self.preview_list.addItem(text)
        elif isinstance(self.preview_data, dict) and 'files' in self.preview_data:
            for file in self.preview_data['files']:
                self.preview_list.addItem(file['filename'])
            
            # Show summary
            self.preview_list.addItem("")
            self.preview_list.addItem(f"Total: {self.preview_data['total_count']} files")
            self.preview_list.addItem(f"Size: {self.preview_data['total_size_mb']:.2f} MB")
    
    def browse_destination(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_edit.setText(folder)
    
    def execute_operation(self):
        """Execute the bulk operation"""
        if not self.preview_data:
            QMessageBox.warning(self, "Error", "Please preview first")
            return
        
        operation = self.op_combo.currentText()
        
        # Show progress
        self.progress.show()
        self.progress.setMaximum(len(self.file_ids))
        
        # Execute based on operation type
        if operation == "Rename":
            result = self.bulk_ops.execute_rename(self.preview_data)
        elif operation == "Move":
            result = self.bulk_ops.execute_move(self.preview_data, create_folder=True)
        elif operation == "Delete":
            permanent = self.permanent_check.isChecked()
            result = self.bulk_ops.execute_delete(self.file_ids, permanent=permanent)
        
        # Show result
        success_count = len(result.get('success', []))
        failed_count = len(result.get('failed', []))
        
        QMessageBox.information(
            self,
            "Complete",
            f"Operation complete!\n\nSuccess: {success_count}\nFailed: {failed_count}"
        )
        
        self.accept()


if __name__ == "__main__":
    print("GUI Enhancements module loaded!")
    print("This module provides:")
    print("  - RemindersWidget")
    print("  - SmartFoldersWidget")
    print("  - BookmarksWidget")
    print("  - BulkOperationsDialog")

