#!/usr/bin/env python3
"""
Reminder System for File Organizer
Smart reminders, nudges, and deadline tracking
"""

import os
from datetime import datetime, timedelta
from dateutil import parser
import sqlite3


class ReminderSystem:
    """Manages file-based reminders and context-aware nudges"""
    
    def __init__(self, db):
        self.db = db
    
    def create_reminder(self, file_id, reminder_type, reminder_date, message=None):
        """
        Create a reminder for a file
        
        reminder_type: 'deadline', 'follow_up', 'review', 'archive', 'custom'
        """
        cursor = self.db.conn.cursor()
        
        # Parse date if it's a string
        if isinstance(reminder_date, str):
            reminder_date = self._parse_date(reminder_date)
        
        cursor.execute("""
            INSERT INTO reminders 
            (file_id, reminder_type, reminder_date, message, is_active, created_date)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (
            file_id,
            reminder_type,
            reminder_date.isoformat() if isinstance(reminder_date, datetime) else reminder_date,
            message,
            datetime.now().isoformat()
        ))
        
        self.db.conn.commit()
        return cursor.lastrowid
    
    def _parse_date(self, date_str):
        """Parse natural language dates"""
        date_str = date_str.lower().strip()
        now = datetime.now()
        
        # Relative dates
        if 'tomorrow' in date_str:
            return now + timedelta(days=1)
        elif 'next week' in date_str:
            return now + timedelta(weeks=1)
        elif 'next month' in date_str:
            return now + timedelta(days=30)
        elif 'in' in date_str:
            # "in 3 days", "in 2 weeks", "in 1 month"
            parts = date_str.split()
            if len(parts) >= 3:
                try:
                    num = int(parts[1])
                    unit = parts[2]
                    if 'day' in unit:
                        return now + timedelta(days=num)
                    elif 'week' in unit:
                        return now + timedelta(weeks=num)
                    elif 'month' in unit:
                        return now + timedelta(days=num*30)
                    elif 'hour' in unit:
                        return now + timedelta(hours=num)
                except:
                    pass
        
        # Try to parse as date
        try:
            return parser.parse(date_str)
        except:
            # Default to tomorrow if can't parse
            return now + timedelta(days=1)
    
    def get_due_reminders(self, include_overdue=True):
        """Get all reminders that are due or overdue"""
        cursor = self.db.conn.cursor()
        
        now = datetime.now().isoformat()
        
        if include_overdue:
            cursor.execute("""
                SELECT r.id, r.file_id, r.reminder_type, r.reminder_date, r.message,
                       f.filename, f.path, f.project
                FROM reminders r
                JOIN files f ON r.file_id = f.id
                WHERE r.is_active = 1 
                  AND r.reminder_date <= ?
                  AND r.triggered_date IS NULL
                ORDER BY r.reminder_date ASC
            """, (now,))
        else:
            cursor.execute("""
                SELECT r.id, r.file_id, r.reminder_type, r.reminder_date, r.message,
                       f.filename, f.path, f.project
                FROM reminders r
                JOIN files f ON r.file_id = f.id
                WHERE r.is_active = 1 
                  AND r.reminder_date <= ?
                  AND r.reminder_date >= ?
                  AND r.triggered_date IS NULL
                ORDER BY r.reminder_date ASC
            """, (now, datetime.now().date().isoformat()))
        
        columns = ['id', 'file_id', 'reminder_type', 'reminder_date', 'message',
                   'filename', 'path', 'project']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def mark_reminder_triggered(self, reminder_id):
        """Mark a reminder as triggered"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE reminders
            SET triggered_date = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), reminder_id))
        self.db.conn.commit()
    
    def dismiss_reminder(self, reminder_id):
        """Dismiss/deactivate a reminder"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE reminders
            SET is_active = 0
            WHERE id = ?
        """, (reminder_id,))
        self.db.conn.commit()
    
    def snooze_reminder(self, reminder_id, snooze_duration_minutes=60):
        """Snooze a reminder"""
        cursor = self.db.conn.cursor()
        
        # Get current reminder date
        cursor.execute("SELECT reminder_date FROM reminders WHERE id = ?", (reminder_id,))
        current_date = cursor.fetchone()[0]
        
        # Add snooze duration
        new_date = datetime.fromisoformat(current_date) + timedelta(minutes=snooze_duration_minutes)
        
        cursor.execute("""
            UPDATE reminders
            SET reminder_date = ?, triggered_date = NULL
            WHERE id = ?
        """, (new_date.isoformat(), reminder_id))
        
        self.db.conn.commit()
    
    def get_nudges(self, limit=5):
        """
        Generate context-aware nudges based on learned patterns
        Returns proactive suggestions for the user
        """
        nudges = []
        cursor = self.db.conn.cursor()
        
        # Nudge 1: Files you haven't touched in a while from active projects
        cursor.execute("""
            SELECT f.id, f.filename, f.path, f.project, f.last_accessed
            FROM files f
            WHERE f.project IS NOT NULL 
              AND f.project != ''
              AND f.status = 'active'
              AND (f.last_accessed IS NULL OR f.last_accessed < ?)
            ORDER BY f.modified_date DESC
            LIMIT 5
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        
        for row in cursor.fetchall():
            file_id, filename, path, project, last_accessed = row
            nudges.append({
                'type': 'stale_project_file',
                'priority': 7,
                'message': f"📂 Haven't opened '{filename}' from {project} in a week",
                'file_id': file_id,
                'path': path,
                'action': 'review'
            })
        
        # Nudge 2: Messy folders (>20 files in Downloads/Desktop)
        common_folders = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents")
        ]
        
        for folder in common_folders:
            cursor.execute("""
                SELECT COUNT(*) FROM files
                WHERE folder_location = ?
                  AND status = 'active'
            """, (folder,))
            
            count = cursor.fetchone()[0]
            if count > 20:
                nudges.append({
                    'type': 'messy_folder',
                    'priority': 8,
                    'message': f"🧹 {os.path.basename(folder)} has {count} files - time to organize?",
                    'folder': folder,
                    'file_count': count,
                    'action': 'organize'
                })
        
        # Nudge 3: Files without tags from last week
        cursor.execute("""
            SELECT COUNT(*) FROM files
            WHERE (ai_tags IS NULL OR ai_tags = '')
              AND modified_date > ?
              AND status = 'active'
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        
        untagged_count = cursor.fetchone()[0]
        if untagged_count > 5:
            nudges.append({
                'type': 'untagged_files',
                'priority': 5,
                'message': f"🏷️ {untagged_count} recent files need AI tagging",
                'count': untagged_count,
                'action': 'tag'
            })
        
        # Nudge 4: Duplicate files taking up space
        cursor.execute("""
            SELECT COUNT(*), SUM(size) FROM files
            WHERE is_duplicate = 1
              AND status = 'active'
        """)
        
        dup_row = cursor.fetchone()
        if dup_row and dup_row[0] > 0:
            dup_count, dup_size = dup_row
            dup_size_mb = (dup_size or 0) / (1024 * 1024)
            if dup_size_mb > 10:
                nudges.append({
                    'type': 'duplicates',
                    'priority': 6,
                    'message': f"📦 {dup_count} duplicate files using {dup_size_mb:.1f} MB",
                    'count': dup_count,
                    'size_mb': dup_size_mb,
                    'action': 'clean_duplicates'
                })
        
        # Nudge 5: Screenshots piling up
        cursor.execute("""
            SELECT COUNT(*) FROM files
            WHERE is_screenshot = 1
              AND status = 'active'
              AND modified_date > ?
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        
        screenshot_count = cursor.fetchone()[0]
        if screenshot_count > 10:
            nudges.append({
                'type': 'screenshots',
                'priority': 6,
                'message': f"📸 {screenshot_count} screenshots from last week - organize them?",
                'count': screenshot_count,
                'action': 'organize_screenshots'
            })
        
        # Sort by priority and limit
        nudges.sort(key=lambda x: x['priority'], reverse=True)
        return nudges[:limit]
    
    def get_upcoming_reminders(self, days_ahead=7):
        """Get reminders coming up in the next N days"""
        cursor = self.db.conn.cursor()
        
        now = datetime.now().isoformat()
        future = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        
        cursor.execute("""
            SELECT r.id, r.file_id, r.reminder_type, r.reminder_date, r.message,
                   f.filename, f.path, f.project
            FROM reminders r
            JOIN files f ON r.file_id = f.id
            WHERE r.is_active = 1 
              AND r.reminder_date > ?
              AND r.reminder_date <= ?
              AND r.triggered_date IS NULL
            ORDER BY r.reminder_date ASC
        """, (now, future))
        
        columns = ['id', 'file_id', 'reminder_type', 'reminder_date', 'message',
                   'filename', 'path', 'project']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def check_and_notify(self):
        """
        Check for due reminders and generate notifications
        Returns list of reminders that should be shown to user
        """
        due_reminders = self.get_due_reminders()
        
        notifications = []
        for reminder in due_reminders:
            # Determine notification message
            if reminder['message']:
                msg = reminder['message']
            else:
                msg = f"Reminder: {reminder['filename']}"
            
            # Calculate how overdue
            reminder_date = datetime.fromisoformat(reminder['reminder_date'])
            now = datetime.now()
            overdue_hours = (now - reminder_date).total_seconds() / 3600
            
            if overdue_hours > 24:
                urgency = "overdue"
                days = int(overdue_hours / 24)
                msg += f" (overdue by {days} day{'s' if days > 1 else ''})"
            elif overdue_hours > 1:
                urgency = "due"
                msg += f" (due {int(overdue_hours)} hours ago)"
            else:
                urgency = "due_now"
            
            notifications.append({
                'id': reminder['id'],
                'message': msg,
                'urgency': urgency,
                'file_id': reminder['file_id'],
                'filename': reminder['filename'],
                'path': reminder['path'],
                'type': reminder['reminder_type']
            })
        
        return notifications


if __name__ == "__main__":
    # Test the reminder system
    from file_indexer import FileDatabase
    
    print("Testing Reminder System...")
    
    db = FileDatabase()
    reminder_system = ReminderSystem(db)
    
    # Get nudges
    print("\n📢 Current Nudges:")
    nudges = reminder_system.get_nudges()
    for i, nudge in enumerate(nudges, 1):
        print(f"{i}. [{nudge['priority']}] {nudge['message']}")
    
    # Get due reminders
    print("\n⏰ Due Reminders:")
    due = reminder_system.get_due_reminders()
    if due:
        for reminder in due:
            print(f"- {reminder['filename']}: {reminder['message']}")
    else:
        print("No reminders due")
    
    # Get upcoming reminders
    print("\n📅 Upcoming (Next 7 Days):")
    upcoming = reminder_system.get_upcoming_reminders(7)
    if upcoming:
        for reminder in upcoming:
            print(f"- {reminder['reminder_date']}: {reminder['filename']}")
    else:
        print("No upcoming reminders")
    
    db.close()
    print("\n✅ Reminder system test complete!")
