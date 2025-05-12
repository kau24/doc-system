import hashlib
import sqlite3

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email, full_name, specialization, hospital, role):
    """Register a new user in the database."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    hashed_password = hash_password(password)
    
    try:
        c.execute('''
        INSERT INTO users (username, password, email, full_name, specialization, hospital, role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, email, full_name, specialization, hospital, role))
        
        user_id = c.lastrowid
        
        # Log the registration activity
        c.execute('''
        INSERT INTO activity_logs (user_id, activity_type, activity_details)
        VALUES (?, ?, ?)
        ''', (user_id, 'Registration', f'User {username} registered as {role}'))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    """Authenticate a user and return user details if successful."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    hashed_password = hash_password(password)
    
    c.execute('''
    SELECT id, username, email, role FROM users 
    WHERE username = ? AND password = ?
    ''', (username, hashed_password))
    
    user = c.fetchone()
    
    if user:
        # Log the login activity
        c.execute('''
        INSERT INTO activity_logs (user_id, activity_type, activity_details)
        VALUES (?, ?, ?)
        ''', (user[0], 'Login', f'User {username} logged in'))
        conn.commit()
    
    conn.close()
    return user