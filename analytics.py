import sqlite3
import pandas as pd

def get_user_analytics():
    """Get analytics data about users in the system."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Get registration counts by date
    c.execute('''
    SELECT date(registration_date) as reg_date, COUNT(*) as count
    FROM users
    GROUP BY date(registration_date)
    ORDER BY reg_date
    ''')
    
    registration_data = pd.DataFrame(c.fetchall(), columns=['Registration Date', 'Count'])
    
    # Get user counts by role
    c.execute('''
    SELECT role, COUNT(*) as count
    FROM users
    GROUP BY role
    ''')
    
    role_data = pd.DataFrame(c.fetchall(), columns=['Role', 'Count'])
    
    # Get user counts by specialization
    c.execute('''
    SELECT specialization, COUNT(*) as count
    FROM users
    WHERE specialization IS NOT NULL
    GROUP BY specialization
    ''')
    
    specialization_data = pd.DataFrame(c.fetchall(), columns=['Specialization', 'Count'])
    
    conn.close()
    return {
        'registration_data': registration_data,
        'role_data': role_data,
        'specialization_data': specialization_data
    }

def get_referral_analytics():
    """Get analytics data about referrals in the system."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Get referral counts by date
    c.execute('''
    SELECT date(referral_date) as ref_date, COUNT(*) as count
    FROM referrals
    GROUP BY date(referral_date)
    ORDER BY ref_date
    ''')
    
    referral_date_data = pd.DataFrame(c.fetchall(), columns=['Referral Date', 'Count'])
    
    # Get referral counts by status
    c.execute('''
    SELECT status, COUNT(*) as count
    FROM referrals
    GROUP BY status
    ''')
    
    status_data = pd.DataFrame(c.fetchall(), columns=['Status', 'Count'])
    
    # Get referral counts by urgency
    c.execute('''
    SELECT urgency, COUNT(*) as count
    FROM referrals
    GROUP BY urgency
    ''')
    
    urgency_data = pd.DataFrame(c.fetchall(), columns=['Urgency', 'Count'])
    
    # Get average response time (days between referral and consultation)
    c.execute('''
    SELECT AVG(julianday(c.consultation_date) - julianday(r.referral_date)) as avg_response_time
    FROM referrals r
    JOIN consultations c ON r.referral_id = c.referral_id
    ''')
    
    avg_response_time = c.fetchone()[0] or 0
    
    conn.close()
    return {
        'referral_date_data': referral_date_data,
        'status_data': status_data,
        'urgency_data': urgency_data,
        'avg_response_time': avg_response_time
    }

def get_doctor_performance_analytics():
    """Get analytics data about doctor performance in the system."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Get top referring doctors
    c.execute('''
    SELECT u.full_name, COUNT(*) as referral_count
    FROM referrals r
    JOIN users u ON r.referring_doctor_id = u.id
    GROUP BY r.referring_doctor_id
    ORDER BY referral_count DESC
    LIMIT 10
    ''')
    
    top_referring_doctors = pd.DataFrame(c.fetchall(), columns=['Doctor', 'Referral Count'])
    
    # Get top consulting doctors
    c.execute('''
    SELECT u.full_name, COUNT(*) as consultation_count
    FROM consultations c
    JOIN users u ON c.consulting_doctor_id = u.id
    GROUP BY c.consulting_doctor_id
    ORDER BY consultation_count DESC
    LIMIT 10
    ''')
    
    top_consulting_doctors = pd.DataFrame(c.fetchall(), columns=['Doctor', 'Consultation Count'])
    
    # Get average response time by doctor
    c.execute('''
    SELECT u.full_name, 
           AVG(julianday(c.consultation_date) - julianday(r.referral_date)) as avg_response_time
    FROM consultations c
    JOIN referrals r ON c.referral_id = r.referral_id
    JOIN users u ON c.consulting_doctor_id = u.id
    GROUP BY c.consulting_doctor_id
    ORDER BY avg_response_time
    ''')
    
    doctor_response_times = pd.DataFrame(c.fetchall(), columns=['Doctor', 'Average Response Time (days)'])
    
    conn.close()
    return {
        'top_referring_doctors': top_referring_doctors,
        'top_consulting_doctors': top_consulting_doctors,
        'doctor_response_times': doctor_response_times
    }