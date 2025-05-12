import json
from datetime import datetime
import sqlite3
import uuid
import os
import streamlit as st
from email_service import send_referral_notification

# ✅ Import GPT summary function
from gpt_tools import get_gpt4_summary

def save_uploaded_file(uploaded_file, doctor_id, referral_id):
    """Save an uploaded file to a directory and return the file path."""
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    directory = f'uploads/{doctor_id}/{referral_id}'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

    
def create_referral(referring_doctor_id, referred_doctor_email, patient_details, clinical_info, 
                    diagnosis, reason, urgency, notes, uploaded_files, additional_details=None):
    """Create a new referral in the database with dynamic column handling."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    try:
        # Check if the referred doctor exists in the system
        c.execute('SELECT id FROM users WHERE email = ?', (referred_doctor_email,))
        referred_doctor = c.fetchone()
        referred_doctor_id = referred_doctor[0] if referred_doctor else None
        
        # Generate unique referral ID
        referral_id = str(uuid.uuid4())
        
        # Save uploaded files
        file_paths = []
        if uploaded_files:
            for file in uploaded_files:
                file_path = save_uploaded_file(file, referring_doctor_id, referral_id)
                file_paths.append(file_path)
        
        # Convert additional details to JSON for storage
        additional_details_json = json.dumps(additional_details) if additional_details else None
        
        # Get table columns dynamically
        c.execute("PRAGMA table_info(referrals)")
        columns = [info[1] for info in c.fetchall()]
        
        # ✅ Generate GPT summary based on referral data
        gpt_summary = None
        if 'gpt_summary' in columns:
            try:
                gpt_input = {
                    'patient_name': patient_details['name'],
                    'patient_age': patient_details['age'],
                    'patient_gender': patient_details['gender'],
                    'clinical_information': clinical_info,
                    'diagnosis': diagnosis,
                    'reason_for_referral': reason,
                    'medical_history': additional_details.get('medical_history') if additional_details else "",
                    'medications': additional_details.get('medications') if additional_details else ""
                }
                gpt_summary = get_gpt4_summary(gpt_input)
            except Exception as e:
                print(f"GPT Summary generation failed: {e}")
        
        # Build dynamic insert query
        query_columns = ["referral_id", "referring_doctor_id", "referred_doctor_id", "referred_doctor_email",
                         "patient_name", "patient_age", "patient_gender", "patient_id",
                         "clinical_information", "diagnosis", "reason_for_referral",
                         "urgency", "additional_notes", "attachment_paths", "status"]
        
        query_values = [referral_id, referring_doctor_id, referred_doctor_id, referred_doctor_email,
                        patient_details['name'], patient_details['age'], patient_details['gender'], patient_details['id'],
                        clinical_info, diagnosis, reason,
                        urgency, notes, ','.join(file_paths) if file_paths else None, 'Pending']
        
        # Add additional columns if they exist in the database
        if 'patient_dob' in columns:
            query_columns.append("patient_dob")
            query_values.append(patient_details.get('dob'))
            
        if 'patient_phone' in columns:
            query_columns.append("patient_phone")
            query_values.append(patient_details.get('phone', ''))
            
        if 'additional_details' in columns:
            query_columns.append("additional_details")
            query_values.append(additional_details_json)
            
        if 'creation_date' in columns:
            query_columns.append("creation_date")
            query_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
        if 'last_updated' in columns:
            query_columns.append("last_updated")
            query_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        if 'gpt_summary' in columns:
            query_columns.append("gpt_summary")
            query_values.append(gpt_summary)

        # Construct the SQL query
        placeholders = ", ".join(["?" for _ in query_values])
        sql = f"INSERT INTO referrals ({', '.join(query_columns)}) VALUES ({placeholders})"
        
        # Execute the query
        c.execute(sql, query_values)
        
        # Check activity_logs table columns
        c.execute("PRAGMA table_info(activity_logs)")
        log_columns = [info[1] for info in c.fetchall()]
        
        # Construct activity log insert based on available columns
        log_columns_to_insert = ["user_id", "activity_type", "activity_details"]
        log_values = [referring_doctor_id, 'Create Referral', f'Referral {referral_id} created']
        
        if 'referral_id' in log_columns:
            log_columns_to_insert.append("referral_id")
            log_values.append(referral_id)
        
        log_placeholders = ", ".join(["?" for _ in log_values])
        log_sql = f"INSERT INTO activity_logs ({', '.join(log_columns_to_insert)}) VALUES ({log_placeholders})"
        
        c.execute(log_sql, log_values)
        
        conn.commit()
        
        # Send email notification
        send_referral_notification(referred_doctor_email, referral_id)
        
        return referral_id
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating referral: {e}")
        raise e
        
    finally:
        conn.close()


def get_referrals_for_doctor(doctor_id, role):
    """Get all referrals for a doctor based on their role."""
    conn = sqlite3.connect('referral_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get the doctor's email
    c.execute('SELECT email FROM users WHERE id = ?', (doctor_id,))
    result = c.fetchone()
    doctor_email = result[0] if result else None
    
    print(f"Fetching referrals for doctor ID={doctor_id}, email={doctor_email}, role={role}")
    
    if role == 'Referring Doctor':
        # Get referrals created by this doctor
        c.execute('''
        SELECT r.*, u.full_name as referred_doctor_name
        FROM referrals r
        LEFT JOIN users u ON r.referred_doctor_id = u.id
        WHERE r.referring_doctor_id = ?
        ORDER BY r.referral_date DESC
        ''', (doctor_id,))
    else:
        # Get referrals sent to this doctor's email or directly to them
        query = '''
        SELECT r.*, u.full_name as referring_doctor_name
        FROM referrals r
        JOIN users u ON r.referring_doctor_id = u.id
        WHERE r.referred_doctor_id = ? OR r.referred_doctor_email = ?
        ORDER BY r.referral_date DESC
        '''
        c.execute(query, (doctor_id, doctor_email))
    
    referrals = [dict(row) for row in c.fetchall()]
    print(f"Found {len(referrals)} referrals")
    
    conn.close()
    return referrals


def get_referral_details(referral_id):
    """Get detailed information about a specific referral with dynamic column handling."""
    conn = sqlite3.connect('referral_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Get all referral information dynamically
        c.execute('''
        SELECT r.*, 
               ref_doc.full_name as referring_doctor_name, 
               ref_doc.specialization as referring_doctor_specialization,
               ref_doc.hospital as referring_doctor_hospital,
               ref_doc.email as referring_doctor_email,
               cons_doc.full_name as referred_doctor_name,
               cons_doc.specialization as referred_doctor_specialization,
               cons_doc.hospital as referred_doctor_hospital
        FROM referrals r
        JOIN users ref_doc ON r.referring_doctor_id = ref_doc.id
        LEFT JOIN users cons_doc ON r.referred_doctor_id = cons_doc.id
        WHERE r.referral_id = ?
        ''', (referral_id,))
        
        referral = dict(c.fetchone())
        
        # Get consultation information dynamically
        c.execute("PRAGMA table_info(consultations)")
        cons_columns = [info[1] for info in c.fetchall()]
        
        cons_query = f'''
        SELECT c.*, u.full_name as consulting_doctor_name
        FROM consultations c
        JOIN users u ON c.consulting_doctor_id = u.id
        WHERE c.referral_id = ?
        ORDER BY c.consultation_date DESC
        '''
        
        c.execute(cons_query, (referral_id,))
        
        consultation = c.fetchone()
        if consultation:
            referral['consultation'] = dict(consultation)
        
        return referral
        
    except Exception as e:
        print(f"Error retrieving referral details: {e}")
        raise e
        
    finally:
        conn.close()
