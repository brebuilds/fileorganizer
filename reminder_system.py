#!/usr/bin/env python3
"""
Smart Reminders & Nudges System
Proactive notifications for files and tasks
"""

from datetime import datetime, timedelta
import json


class ReminderSystem:
    """Manage file reminders and smart nudges"""
    
    def __init__(self, file_db):
        self.db = file_db
    
    def create_reminder(self, file_id, reminder_date, message, reminder_type='manual'):
        """
        Create a reminder for a file
        
        Args:
            file_id: File database ID
            reminder_date: When to trigger (ISO format or datetime)
            message: Reminder message
            reminder_type: Type of reminder (manual, auto, nudge)
        """
        if isinstance(reminder_date, datetime):
            reminder_date = reminder_date.isoformat()
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (file_id, reminder_type, reminder_date, message, created_date, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (file_id, reminder_type, reminder_date, message, datetime.now().isoformat()))
        
        self.db.conn.commit()
        return cursor.lastrowid
    
    def get_due_reminders(self):
        """Get all reminders that are due now"""
        cursor = self.db.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT r.id, r.file_id, r.reminder_type, r.reminder_date, r.message,
                   f.filename, f.path
            FROM reminders r
            LEFT JOIN files f ON r.file_id = f.id
            WHERE r.is_active = 1
            AND r.reminder_date <= ?
            ORDER BY r.reminder_date
        """, (now,))
        
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                'id': row[0],
                'file_id': row[1],
                'type': row[2],
                'reminder_date': row[3],
                'message': row[4],
                'filename': row[5],
                'path': row[6]
            })
        
        return reminders
    
    def mark_triggered(self, reminder_id):
        """Mark a reminder as triggered"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE reminders
            SET is_active = 0, triggered_date = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), reminder_id))
        self.db.conn.commit()
    
    def generate_smart_nudges(self):
        """Generate automatic nudges based on file patterns"""
        nudges = []
        cursor = self.db.conn.cursor()
        
        # Nudge 1: Files not accessed in 2+ weeks
        two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
        cursor.execute("""
            SELECT id, filename, path, last_accessed
            FROM files
            WHERE last_accessed < ?
            AND ai_tags LIKE '%important%'
            AND status = 'active'
            AND hide_from_app = 0
            LIMIT 5
        """, (two_weeks_ago,))
        
        for row in cursor.fetchall():
            nudges.append({
                'type': 'unaccessed_important',
                'file_id': row[0],
                'filename': row[1],
                'path': row[2],
                'message': f"You haven't looked at '{row[1]}' in 2+ weeks. Still important?"
            })
        
        # Nudge 2: Old files in Downloads
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("""
            SELECT id, filename, path, created_date
            FROM files
            WHERE folder_location LIKE '%Downloads%'
            AND created_date < ?
            AND status = 'active'
            AND hide_from_app = 0
            LIMIT 5
        """, (thirty_days_ago,))
        
        for row in cursor.fetchall():
            nudges.append({
                'type': 'old_download',
                'file_id': row[0],
                'filename': row[1],
                'path': row[2],
                'message': f"'{row[1]}' has been in Downloads for 30+ days. Archive it?"
            })
        
        # Nudge 3: Untagged files
        cursor.execute("""
            SELECT id, filename, path
            FROM files
            WHERE (ai_tags IS NULL OR ai_tags = '')
            AND status = 'active'
            AND hide_from_app = 0
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            nudges.append({
                'type': 'untagged',
                'file_id': row[0],
                'filename': row[1],
                'path': row[2],
                'message': f"'{row[1]}' hasn't been tagged yet. Want me to AI-tag it?"
            })
        
        return nudges
    
    def get_upcoming_reminders(self, days=7):
        """Get reminders coming up in the next N days"""
        cursor = self.db.conn.cursor()
        now = datetime.now().isoformat()
        future = (datetime.now() + timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT r.id, r.file_id, r.reminder_type, r.reminder_date, r.message,
                   f.filename, f.path
            FROM reminders r
            LEFT JOIN files f ON r.file_id = f.id
            WHERE r.is_active = 1
            AND r.reminder_date BETWEEN ? AND ?
            ORDER BY r.reminder_date
        """, (now, future))
        
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                'id': row[0],
                'file_id': row[1],
                'type': row[2],
                'reminder_date': row[3],
                'message': row[4],
                'filename': row[5],
                'path': row[6]
            })
        
        return reminders
    
    def cancel_reminder(self, reminder_id):
        """Cancel a reminder"""
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
        self.db.conn.commit()


if __name__ == "__main__":
    print("🔔 Reminder & Nudge System")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    reminders = ReminderSystem(db)
    
    # Check for due reminders
    due = reminders.get_due_reminders()
    print(f"\n⏰ Due Reminders: {len(due)}")
    
    # Get upcoming reminders
    upcoming = reminders.get_upcoming_reminders(days=7)
    print(f"📅 Upcoming (7 days): {len(upcoming)}")
    
    # Generate smart nudges
    print("\n💡 Generating smart nudges...")
    nudges = reminders.generate_smart_nudges()
    
    if nudges:
        print(f"\n🎯 Smart Nudges ({len(nudges)}):\n")
        for nudge in nudges[:5]:
            print(f"   • {nudge['message']}")
            print(f"     File: {nudge['filename']}")
            print()
    else:
        print("✨ No nudges needed - everything looks good!")
    
    db.close()

