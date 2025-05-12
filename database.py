import sqlite3

def init_db():
    """Initialize the SQLite database with enhanced tables for comprehensive referral system."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        specialization TEXT,
        hospital TEXT,
        department TEXT,
        role TEXT NOT NULL,
        profile_picture TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Create referrals table with gpt_summary added
    c.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY,
        referral_id TEXT UNIQUE NOT NULL,
        referring_doctor_id INTEGER NOT NULL,
        referred_doctor_id INTEGER,
        referred_doctor_email TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        patient_age INTEGER NOT NULL,
        patient_gender TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        patient_dob TEXT,
        patient_phone TEXT,
        clinical_information TEXT NOT NULL,
        diagnosis TEXT,
        reason_for_referral TEXT NOT NULL,
        urgency TEXT NOT NULL,
        additional_notes TEXT,
        attachment_paths TEXT,
        additional_details TEXT,
        gpt_summary TEXT,  -- ✅ New column for AI-generated summary
        status TEXT DEFAULT 'Pending',
        priority INTEGER DEFAULT 0,
        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referring_doctor_id) REFERENCES users (id),
        FOREIGN KEY (referred_doctor_id) REFERENCES users (id)
    )
    ''')
    
    # Create consultations table with enhanced fields
    c.execute('''
    CREATE TABLE IF NOT EXISTS consultations (
        id INTEGER PRIMARY KEY,
        referral_id TEXT NOT NULL,
        consulting_doctor_id INTEGER NOT NULL,
        assessment TEXT NOT NULL,
        diagnosis TEXT,
        recommendation TEXT NOT NULL,
        treatment_plan TEXT,
        medications TEXT,
        additional_information_needed TEXT,
        follow_up_required BOOLEAN DEFAULT 0,
        follow_up_timeframe TEXT,
        attachment_paths TEXT,
        status TEXT NOT NULL,
        consultation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referral_id) REFERENCES referrals (referral_id),
        FOREIGN KEY (consulting_doctor_id) REFERENCES users (id)
    )
    ''')
    
    # Create a log table for analytics with enhanced tracking
    c.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL,
        activity_details TEXT,
        referral_id TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (referral_id) REFERENCES referrals (referral_id)
    )
    ''')
    
    # Create table for tracking referral status changes
    c.execute('''
    CREATE TABLE IF NOT EXISTS referral_status_history (
        id INTEGER PRIMARY KEY,
        referral_id TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        comments TEXT,
        FOREIGN KEY (referral_id) REFERENCES referrals (referral_id),
        FOREIGN KEY (changed_by) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
