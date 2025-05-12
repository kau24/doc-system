import sqlite3

def update_database_schema():
    """Add new columns to the referrals table that were introduced in the enhanced version."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Check current columns in referrals table
    c.execute("PRAGMA table_info(referrals)")
    columns = [info[1] for info in c.fetchall()]

    # Track newly added columns for logging
    added_columns = []

    if 'patient_dob' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN patient_dob TEXT')
        added_columns.append('patient_dob')
    
    if 'patient_phone' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN patient_phone TEXT')
        added_columns.append('patient_phone')
    
    if 'additional_details' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN additional_details TEXT')
        added_columns.append('additional_details')
    
    if 'creation_date' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        added_columns.append('creation_date')
    
    if 'last_updated' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        added_columns.append('last_updated')
    
    if 'priority' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN priority INTEGER DEFAULT 0')
        added_columns.append('priority')

    # ✅ Add GPT-4 summary column
    if 'gpt_summary' not in columns:
        c.execute('ALTER TABLE referrals ADD COLUMN gpt_summary TEXT')
        added_columns.append('gpt_summary')

    conn.commit()
    conn.close()

    # Summary log
    if added_columns:
        print("The following columns were added to the 'referrals' table:")
        for col in added_columns:
            print(f" - {col}")
    else:
        print("No new columns were added. The database schema is already up to date.")

if __name__ == "__main__":
    update_database_schema()
