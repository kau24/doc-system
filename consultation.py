import sqlite3
import os
from referral import save_uploaded_file
from email_service import send_consultation_notification

def submit_consultation(referral_id, doctor_id, assessment, recommendation, additional_info_needed, 
                       uploaded_files, status, diagnosis=None, treatment_plan=None, medications=None,
                       follow_up_required=False, follow_up_timeframe=None):
    """Submit a consultation response to a referral with enhanced fields."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Save uploaded files
    file_paths = []
    if uploaded_files:
        for file in uploaded_files:
            file_path = save_uploaded_file(file, doctor_id, f"{referral_id}_consultation")
            file_paths.append(file_path)
    
    # Get old status of the referral
    c.execute('SELECT status FROM referrals WHERE referral_id = ?', (referral_id,))
    old_status = c.fetchone()[0]
    
    # Insert consultation into database with enhanced fields
    c.execute('''
    INSERT INTO consultations (
        referral_id, consulting_doctor_id, assessment, diagnosis, recommendation, treatment_plan,
        medications, additional_information_needed, follow_up_required, follow_up_timeframe,
        attachment_paths, status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        referral_id, doctor_id, assessment, diagnosis, recommendation, treatment_plan,
        medications, additional_info_needed, 
        1 if follow_up_required else 0, follow_up_timeframe,
        ','.join(file_paths) if file_paths else None, status
    ))
    
    # Update referral status
    c.execute('''
    UPDATE referrals SET status = ?, last_updated = CURRENT_TIMESTAMP WHERE referral_id = ?
    ''', (status, referral_id))
    
    # Log the consultation activity
    c.execute('''
    INSERT INTO activity_logs (user_id, activity_type, activity_details, referral_id)
    VALUES (?, ?, ?, ?)
    ''', (doctor_id, 'Submit Consultation', f'Consultation for referral {referral_id} submitted', referral_id))
    
    # Log the status change in history table
    c.execute('''
    INSERT INTO referral_status_history (referral_id, old_status, new_status, changed_by)
    VALUES (?, ?, ?, ?)
    ''', (referral_id, old_status, status, doctor_id))
    
    # Get the referring doctor's email to send notification
    c.execute('''
    SELECT u.email FROM referrals r
    JOIN users u ON r.referring_doctor_id = u.id
    WHERE r.referral_id = ?
    ''', (referral_id,))
    
    referring_doctor_email = c.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    # Send email notification to referring doctor
    send_consultation_notification(referring_doctor_email, referral_id, status)
    
    return True