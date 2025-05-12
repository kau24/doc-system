import sqlite3
import os
import json
from datetime import datetime

def backup_database():
    """Create a backup of the current database"""
    if os.path.exists('referral_system.db'):
        backup_name = f"referral_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            with open('referral_system.db', 'rb') as src, open(backup_name, 'wb') as dst:
                dst.write(src.read())
            print(f"Database backup created: {backup_name}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    return True  # No database to backup

def migrate_database():
    """Perform a full database migration including schema updates and data preservation"""
    if not backup_database():
        print("Aborting migration due to backup failure")
        return False
    
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    try:
        c.execute("BEGIN TRANSACTION")
        
        # === Update referrals table ===
        c.execute("PRAGMA table_info(referrals)")
        columns = {info[1]: info for info in c.fetchall()}
        
        new_columns = {
            'patient_dob': 'TEXT',
            'patient_phone': 'TEXT',
            'additional_details': 'TEXT',
            'creation_date': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'last_updated': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'priority': 'INTEGER DEFAULT 0',
            'gpt_summary': 'TEXT'  # ✅ New column for GPT-4 summary
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                print(f"Adding column {column_name} to referrals table")
                c.execute(f"ALTER TABLE referrals ADD COLUMN {column_name} {column_type}")

        # === Update consultations table ===
        c.execute("PRAGMA table_info(consultations)")
        cons_columns = {info[1]: info for info in c.fetchall()}
        
        new_cons_columns = {
            'diagnosis': 'TEXT',
            'treatment_plan': 'TEXT',
            'medications': 'TEXT',
            'follow_up_required': 'BOOLEAN DEFAULT 0',
            'follow_up_timeframe': 'TEXT'
        }
        
        for column_name, column_type in new_cons_columns.items():
            if column_name not in cons_columns:
                print(f"Adding column {column_name} to consultations table")
                c.execute(f"ALTER TABLE consultations ADD COLUMN {column_name} {column_type}")
        
        # === Update activity_logs table ===
        c.execute("PRAGMA table_info(activity_logs)")
        log_columns = {info[1]: info for info in c.fetchall()}
        
        new_log_columns = {
            'referral_id': 'TEXT',
            'ip_address': 'TEXT'
        }
        
        for column_name, column_type in new_log_columns.items():
            if column_name not in log_columns:
                print(f"Adding column {column_name} to activity_logs table")
                c.execute(f"ALTER TABLE activity_logs ADD COLUMN {column_name} {column_type}")
        
        # === Create referral_status_history table if not exists ===
        c.execute('''
        CREATE TABLE IF NOT EXISTS referral_status_history (
            id INTEGER PRIMARY KEY,
            referral_id TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_by INTEGER NOT NULL,
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comments TEXT
        )
        ''')

        c.execute("COMMIT")
        print("Database migration completed successfully!")
        return True
    
    except Exception as e:
        c.execute("ROLLBACK")
        print(f"Error during migration: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
