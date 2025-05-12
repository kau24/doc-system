import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import io
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import requests


from auth import login_user, register_user, hash_password
from referral import create_referral, get_referrals_for_doctor, get_referral_details
from consultation import submit_consultation
from analytics import get_user_analytics, get_referral_analytics, get_doctor_performance_analytics
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def debug_referral_system():
    """Show debugging information about referrals in the system."""
    st.header("System Debugging Information")
    
    conn = sqlite3.connect('referral_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Show current user information
    st.subheader("Your Account Information")
    st.write(f"User ID: {st.session_state.user_id}")
    st.write(f"Username: {st.session_state.username}")
    st.write(f"Role: {st.session_state.user_role}")
    
    # Get and show email
    c.execute('SELECT email FROM users WHERE id = ?', (st.session_state.user_id,))
    email = c.fetchone()[0]
    st.write(f"Email: {email}")
    
    # Show all users
    st.subheader("All Users in System")
    c.execute('SELECT id, username, email, role FROM users')
    users = c.fetchall()
    users_data = [{"ID": user["id"], "Username": user["username"], "Email": user["email"], "Role": user["role"]} for user in users]
    st.table(users_data)
    
    # Show all referrals
    st.subheader("All Referrals in System")
    c.execute('''
    SELECT r.referral_id, r.patient_name, r.urgency, r.status, 
           ref.username as referring_doctor, ref.id as referring_id,
           r.referred_doctor_email, cons.username as consulting_doctor, r.referred_doctor_id
    FROM referrals r
    JOIN users ref ON r.referring_doctor_id = ref.id
    LEFT JOIN users cons ON r.referred_doctor_id = cons.id
    ''')
    
    referrals = c.fetchall()
    referrals_data = []
    for r in referrals:
        referrals_data.append({
            "Referral ID": r["referral_id"],
            "Patient": r["patient_name"],
            "From": r["referring_doctor"],
            "From ID": r["referring_id"],
            "To Email": r["referred_doctor_email"],
            "To Doctor": r["consulting_doctor"] or "Not assigned",
            "To ID": r["referred_doctor_id"] or "N/A",
            "Status": r["status"],
            "Urgency": r["urgency"]
        })
    st.table(referrals_data)
    
    conn.close()

    # Add button to fix database issues
    if st.button("Repair Referral Links"):
        repair_referral_links()
        st.success("Database repair attempted. Please refresh the page.")

def repair_referral_links():
    """Fix missing doctor ID links in referrals table."""
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Start a transaction
    c.execute("BEGIN TRANSACTION")
    
    try:
        # Find referrals with missing doctor IDs
        c.execute('''
        SELECT r.referral_id, r.referred_doctor_email, u.id as doctor_id
        FROM referrals r
        JOIN users u ON r.referred_doctor_email = u.email
        WHERE r.referred_doctor_id IS NULL
        ''')
        
        updates = c.fetchall()
        
        for update in updates:
            referral_id, email, doctor_id = update
            # Update the referral with the correct doctor ID
            c.execute('''
            UPDATE referrals 
            SET referred_doctor_id = ? 
            WHERE referral_id = ? AND referred_doctor_email = ?
            ''', (doctor_id, referral_id, email))
            
            print(f"Updated referral {referral_id} with doctor ID {doctor_id} for email {email}")
        
        # Commit changes
        c.execute("COMMIT")
        print(f"Updated {len(updates)} referrals")
        
    except Exception as e:
        # Roll back in case of error
        c.execute("ROLLBACK")
        print(f"Error repairing database: {e}")
    
    finally:
        conn.close()



def render_login_page():
    """Render the login page."""
    from styles import PRIMARY_COLOR, SECONDARY_COLOR, BACKGROUND_COLOR
    
    # Custom CSS for login page
    login_css = f"""
    <style>
        .login-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .login-header {{
            color: {PRIMARY_COLOR};
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 2rem;
        }}
        
        .login-logo {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        
        .tab-content {{
            background-color: {BACKGROUND_COLOR};
            padding: 2rem;
            border-radius: 5px;
        }}
    </style>
    """
    
    st.markdown(login_css, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">Medical Referral System</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-logo">🏥</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if username and password:
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user[1]
                    st.session_state.user_id = user[0]
                    st.session_state.user_role = user[3]
                    st.session_state.email = user[2]
                    st.session_state.current_page = "dashboard"
                    st.success(f"Welcome back, {user[1]}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please fill in all fields")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.subheader("Register")
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        email = st.text_input("Email", key="email")
        full_name = st.text_input("Full Name", key="full_name")
        specialization = st.text_input("Medical Specialization", key="specialization")
        hospital = st.text_input("Hospital/Clinic", key="hospital")
        role = st.selectbox("Role", options=["Referring Doctor", "Consulting Doctor", "Both"], key="role")
        
        if st.button("Register"):
            if new_username and new_password and confirm_password and email and full_name and role:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success = register_user(new_username, new_password, email, full_name, specialization, hospital, role)
                    if success:
                        st.success("Registration successful! You can now login.")
                    else:
                        st.error("Username or email already exists")
            else:
                st.warning("Please fill in all required fields")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard():
    """Render the main dashboard page."""
    st.title(f"Welcome, Dr. {st.session_state.username}")
    
    # Sidebar for navigation
    with st.sidebar:
        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            ["Dashboard", "Create Referral", "View Referrals", "View Consultations", "Analytics", "Profile"],
            key="dashboard_page"
        )
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = None
            st.session_state.user_role = ""
            st.session_state.email = ""
            st.session_state.current_page = "login"
            st.rerun()
    
    # Main content based on selected page
    if page == "Dashboard":
        render_dashboard_home()
    elif page == "Create Referral":
        render_create_referral()
    elif page == "View Referrals":
        render_view_referrals()
    elif page == "View Consultations":
        render_view_consultations()
    elif page == "Analytics":
        render_analytics()
    elif page == "Profile":
        render_profile()

def render_dashboard_home():
    """Render the dashboard home page."""
    from styles import metric_card, format_status_badge, format_urgency_badge, STATUS_COLORS
    
    st.markdown('<div class="main-header">Dashboard</div>', unsafe_allow_html=True)
    
    # Display overview metrics
    col1, col2, col3 = st.columns(3)
    
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Count pending referrals
    if st.session_state.user_role in ["Consulting Doctor", "Both"]:
        c.execute('''
        SELECT COUNT(*) FROM referrals 
        WHERE status = 'Pending' AND 
              (referred_doctor_id = ? OR referred_doctor_email = (SELECT email FROM users WHERE id = ?))
        ''', (st.session_state.user_id, st.session_state.user_id))
        pending_referrals = c.fetchone()[0]
        
        with col1:
            st.markdown(metric_card("Pending Consultations", pending_referrals), unsafe_allow_html=True)
    
    # Count sent referrals
    if st.session_state.user_role in ["Referring Doctor", "Both"]:
        c.execute('''
        SELECT COUNT(*) FROM referrals 
        WHERE referring_doctor_id = ?
        ''', (st.session_state.user_id,))
        sent_referrals = c.fetchone()[0]
        
        with col2:
            st.markdown(metric_card("Sent Referrals", sent_referrals), unsafe_allow_html=True)
    
    # Count completed consultations
    c.execute('''
    SELECT COUNT(*) FROM consultations 
    WHERE consulting_doctor_id = ?
    ''', (st.session_state.user_id,))
    completed_consultations = c.fetchone()[0]
    
    with col3:
        st.markdown(metric_card("Completed Consultations", completed_consultations), unsafe_allow_html=True)
    
    # Recent activity
    st.markdown('<div class="sub-header">Recent Activity</div>', unsafe_allow_html=True)
    c.execute('''
    SELECT a.activity_type, a.activity_details, a.timestamp
    FROM activity_logs a
    WHERE a.user_id = ?
    ORDER BY a.timestamp DESC
    LIMIT 5
    ''', (st.session_state.user_id,))
    
    activities = c.fetchall()
    if activities:
        for activity in activities:
            st.text(f"{activity[0]} - {activity[1]} ({activity[2]})")
    else:
        st.info("No recent activity")
    
    # Recent referrals
    if st.session_state.user_role in ["Referring Doctor", "Both"]:
        st.subheader("Recent Referrals Sent")
        c.execute('''
        SELECT r.patient_name, r.status, r.referral_date, r.referral_id
        FROM referrals r
        WHERE r.referring_doctor_id = ?
        ORDER BY r.referral_date DESC
        LIMIT 5
        ''', (st.session_state.user_id,))
        
        referrals = c.fetchall()
        if referrals:
            for ref in referrals:
                st.markdown(f"**Patient:** {ref[0]} | **Status:** {ref[1]} | **Date:** {ref[2]}")
                if st.button(f"View Details {ref[3]}", key=f"ref_{ref[3]}"):
                    st.session_state.selected_referral = ref[3]
                    st.session_state.current_page = "referral_details"
                    st.rerun()
        else:
            st.info("No referrals sent yet")
    
    # Recent consultations to do
    if st.session_state.user_role in ["Consulting Doctor", "Both"]:
        st.subheader("Pending Consultations")
        c.execute('''
        SELECT r.patient_name, r.urgency, r.referral_date, r.referral_id
        FROM referrals r
        WHERE r.status = 'Pending' AND 
              (r.referred_doctor_id = ? OR r.referred_doctor_email = (SELECT email FROM users WHERE id = ?))
        ORDER BY 
            CASE r.urgency
                WHEN 'Emergency' THEN 1
                WHEN 'Urgent' THEN 2
                WHEN 'Routine' THEN 3
                ELSE 4
            END,
            r.referral_date DESC
        LIMIT 5
        ''', (st.session_state.user_id, st.session_state.user_id))
        
        consultations = c.fetchall()
        if consultations:
            for cons in consultations:
                st.markdown(f"**Patient:** {cons[0]} | **Urgency:** {cons[1]} | **Date:** {cons[2]}")
                if st.button(f"Review {cons[3]}", key=f"cons_{cons[3]}"):
                    st.session_state.selected_referral = cons[3]
                    st.session_state.current_page = "referral_details"
                    st.rerun()
        else:
            st.info("No pending consultations")
    
    conn.close()
    # Add a debug section at the bottom for administrators
    st.markdown("---")
    with st.expander("System Diagnostics (Admin)"):
        debug_referral_system()

def search_openfda_medications(search_term):
    """Search OpenFDA database for medications matching the search term."""
    if not search_term or len(search_term) < 3:
        return []
    
    # Log the search attempt
    print(f"Searching OpenFDA for: {search_term}")
    
    api_url = "https://api.fda.gov/drug/label.json"
    params = {
        "search": f"(openfda.brand_name:{search_term} OR openfda.generic_name:{search_term})",
        "limit": 15
    }
    
    try:
        # Print the full URL being requested for debugging
        full_url = f"{api_url}?search={params['search']}&limit={params['limit']}"
        print(f"Making request to: {full_url}")
        
        # Make the API request
        response = requests.get(api_url, params=params)
        
        # Print response status for debugging
        print(f"OpenFDA API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if any results were returned
            if 'results' in data and len(data['results']) > 0:
                print(f"Found {len(data['results'])} results from OpenFDA")
                
                results = []
                for result in data['results']:
                    if 'openfda' in result:
                        # Extract medication information
                        brand_names = result['openfda'].get('brand_name', ["Unknown"])
                        generic_names = result['openfda'].get('generic_name', [""])
                        
                        print(f"Found medication: {brand_names[0]} ({generic_names[0] if generic_names else ''})")
                        
                        # Get dosage forms if available
                        dosage_forms = result['openfda'].get('dosage_form', ["Tablet"])
                        # Get strengths if available
                        strengths = result['openfda'].get('strength', ["N/A"])
                        
                        for brand_name in brand_names:
                            for generic_name in generic_names:
                                name = f"{brand_name} ({generic_name})" if generic_name else brand_name
                                dosages = []
                                
                                for strength in strengths:
                                    for form in dosage_forms:
                                        dosages.append(f"{strength} {form}")
                                
                                if not dosages:
                                    dosages = ["N/A"]
                                
                                # Avoid duplicate entries
                                if not any(res["name"] == name for res in results):
                                    results.append({
                                        "name": name,
                                        "dosages": dosages,
                                        "route": result['openfda'].get('route', ["Oral"])[0] if 'route' in result['openfda'] else "Oral"
                                    })
                
                print(f"Processed {len(results)} unique medications")
                return results
            else:
                print("No results found in OpenFDA response")
                # Try a more generic search as fallback
                if ' ' in search_term:
                    first_word = search_term.split()[0]
                    print(f"Trying fallback search with first word only: {first_word}")
                    return search_openfda_medications(first_word)
                return []
        else:
            print(f"Error from OpenFDA API: {response.text}")
            return []
            
    except Exception as e:
        print(f"Exception in OpenFDA search: {str(e)}")
        return []

def search_openfda_medications_alternative(search_term):
    """Alternative approach using a different OpenFDA endpoint."""
    if not search_term or len(search_term) < 3:
        return []
    
    print(f"Using alternative search for: {search_term}")
    
    # Use the drug NDC endpoint instead
    api_url = "https://api.fda.gov/drug/ndc.json"
    params = {
        "search": f"(brand_name:{search_term} OR generic_name:{search_term})",
        "limit": 15
    }
    
    try:
        response = requests.get(api_url, params=params)
        print(f"Alternative API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'results' in data and len(data['results']) > 0:
                print(f"Found {len(data['results'])} results from alternative API")
                
                results = []
                for result in data['results']:
                    brand_name = result.get('brand_name', "Unknown")
                    generic_name = result.get('generic_name', "")
                    
                    name = f"{brand_name} ({generic_name})" if generic_name else brand_name
                    
                    # Get dosage forms and strengths
                    if 'dosage_form' in result:
                        dosage_form = result['dosage_form']
                    else:
                        dosage_form = "Tablet"
                    
                    if 'active_ingredients' in result and len(result['active_ingredients']) > 0:
                        strengths = [f"{ing.get('strength', 'N/A')}" for ing in result['active_ingredients']]
                    else:
                        strengths = ["N/A"]
                    
                    dosages = [f"{strength} {dosage_form}" for strength in strengths]
                    
                    # Get route
                    route = result.get('route', ["Oral"])[0] if isinstance(result.get('route'), list) else result.get('route', "Oral")
                    
                    # Add to results if not duplicate
                    if not any(res["name"] == name for res in results):
                        results.append({
                            "name": name,
                            "dosages": dosages,
                            "route": route
                        })
                
                return results
            else:
                print("No results found in alternative API")
                return []
        else:
            print(f"Error from alternative API: {response.text}")
            return []
            
    except Exception as e:
        print(f"Exception in alternative search: {str(e)}")
        return []

# Fallback medication database if all APIs fail
COMMON_MEDICATIONS = [
    {"name": "Aspirin (acetylsalicylic acid)", "dosages": ["81mg Tablet", "325mg Tablet"], "route": "Oral"},
    {"name": "Atorvastatin (Lipitor)", "dosages": ["10mg Tablet", "20mg Tablet", "40mg Tablet", "80mg Tablet"], "route": "Oral"},
    {"name": "Lisinopril", "dosages": ["5mg Tablet", "10mg Tablet", "20mg Tablet", "40mg Tablet"], "route": "Oral"},
    {"name": "Metformin", "dosages": ["500mg Tablet", "850mg Tablet", "1000mg Tablet", "500mg ER Tablet"], "route": "Oral"},
    {"name": "Amlodipine", "dosages": ["2.5mg Tablet", "5mg Tablet", "10mg Tablet"], "route": "Oral"},
    {"name": "Metoprolol", "dosages": ["25mg Tablet", "50mg Tablet", "100mg Tablet"], "route": "Oral"},
    {"name": "Gabapentin", "dosages": ["100mg Capsule", "300mg Capsule", "400mg Capsule", "600mg Tablet"], "route": "Oral"},
    {"name": "Omeprazole", "dosages": ["10mg Capsule", "20mg Capsule", "40mg Capsule"], "route": "Oral"},
    {"name": "Prednisone", "dosages": ["5mg Tablet", "10mg Tablet", "20mg Tablet"], "route": "Oral"},
    {"name": "Ibuprofen", "dosages": ["200mg Tablet", "400mg Tablet", "600mg Tablet", "800mg Tablet"], "route": "Oral"},
]

def search_local_medications(search_term):
    """Search the local fallback medication database."""
    if not search_term:
        return []
    
    search_term = search_term.lower()
    return [med for med in COMMON_MEDICATIONS if search_term in med["name"].lower()]

def render_create_referral():
    """Render the page for creating a new referral with enhanced form elements and OpenFDA medication lookup."""
    from styles import PRIMARY_COLOR, SECONDARY_COLOR
    
    st.markdown('<div class="main-header">Create New Referral</div>', unsafe_allow_html=True)

    # Institution Information (Header)
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Medical Consultation/Referral Form")
            hospital = st.text_input("Hospital/Institution", value="")
            department = st.text_input("Department", value="")
        with col2:
            st.image("logo.png", width=100) if os.path.exists("logo.png") else st.write("📋")
        st.markdown('</div>', unsafe_allow_html=True)

    # Urgency Selection
    st.subheader("Referral Priority")
    urgency = st.radio("Urgency", options=["Routine", "Urgent", "Emergency"], horizontal=True)
    expected_timeframe = st.selectbox("Expected Response Timeframe", 
                                      options=["Within 24 hours", "Within 3 days", "Within 1 week", "Within 2 weeks", "Next available"])
    
    # Patient Information
    st.subheader("Patient Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        patient_name = st.text_input("Patient Name")
        patient_id = st.text_input("Patient ID/MRN")
    with col2:
        patient_dob = st.date_input("Date of Birth")
        patient_gender = st.selectbox("Gender", options=["Male", "Female", "Other"])
    with col3:
        patient_phone = st.text_input("Phone Number")
        needs_interpreter = st.checkbox("Needs Interpreter")
        if needs_interpreter:
            patient_language = st.text_input("Primary Language")
    
    # Clinical Information with Structured Fields
    st.subheader("Clinical Information")
    
    # Medical History Checkboxes
    st.write("**Medical History**")
    col1, col2, col3 = st.columns(3)
    with col1:
        diabetes = st.checkbox("Diabetes")
        hypertension = st.checkbox("Hypertension")
        heart_disease = st.checkbox("Heart Disease")
    with col2:
        respiratory_disease = st.checkbox("Respiratory Disease")
        kidney_disease = st.checkbox("Kidney Disease")
        liver_disease = st.checkbox("Liver Disease")
    with col3:
        cancer = st.checkbox("Cancer")
        autoimmune = st.checkbox("Autoimmune Disease")
        other_history = st.checkbox("Other")
    
    if other_history:
        other_history_text = st.text_input("Specify Other History")
    
    # Medications with OpenFDA lookup
    st.write("**Current Medications**")
    
    # Add OpenFDA medication database lookup
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.write("Search medications from FDA database:")
    
    # Initialize session state variables for medication search
    if 'medication_search' not in st.session_state:
        st.session_state.medication_search = ""
    if 'search_clicked' not in st.session_state:
        st.session_state.search_clicked = False
    if 'selected_medications' not in st.session_state:
        st.session_state.selected_medications = []

    # Handle search input and button
    col1, col2 = st.columns([3, 1])
    with col1:
        medication_search = st.text_input("Search medications", 
                                        value=st.session_state.medication_search,
                                        placeholder="Enter at least 3 characters to search...")
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("Search")
        
    # Set the session state for next run
    st.session_state.medication_search = medication_search
    search_clicked = search_button or st.session_state.search_clicked
    # Reset the search clicked flag
    st.session_state.search_clicked = False

    # Get results from OpenFDA
    if medication_search and len(medication_search) >= 3 and search_clicked:
        with st.spinner("Searching medications..."):
            # Try the primary search function
            med_results = search_openfda_medications(medication_search)
            
            # If no results, try the alternative API
            if not med_results:
                st.info("Trying alternative medication database...")
                med_results = search_openfda_medications_alternative(medication_search)
                
                # If still no results, fall back to local database
                if not med_results:
                    st.info("Using local medication database...")
                    med_results = search_local_medications(medication_search)
        
        if med_results:
            st.success(f"Found {len(med_results)} medications")
            
            # Create dropdown for medications
            med_names = [med["name"] for med in med_results]
            selected_med_name = st.selectbox("Select medication", options=["-- Select a medication --"] + med_names)
            
            if selected_med_name != "-- Select a medication --":
                # Find the selected medication details
                selected_med = next((med for med in med_results if med["name"] == selected_med_name), None)
                
                if selected_med:
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_dosage = st.selectbox("Dosage", options=selected_med["dosages"])
                    with col2:
                        selected_frequency = st.selectbox("Frequency", options=[
                            "Once daily", "Twice daily", "Three times daily", 
                            "Four times daily", "Every 8 hours", "Every 12 hours", 
                            "As needed", "Before meals", "With meals", "At bedtime"
                        ])
                    
                    route = selected_med.get("route", "Oral")
                    
                    # Button to add the medication to the list
                    if st.button("Add This Medication"):
                        full_med_entry = f"{selected_med_name} {selected_dosage} {selected_frequency} (Route: {route})"
                        
                        st.session_state.selected_medications.append(full_med_entry)
                        st.success(f"Added: {full_med_entry}")
                        st.rerun()
        else:
            st.warning(f"No medications found matching '{medication_search}'. Try more common medications like 'aspirin', 'metformin', or 'lisinopril'.")
            
            # Provide some common medications as suggestions
            common_meds = ["aspirin", "metformin", "lisinopril", "atorvastatin", "amlodipine"]
            st.write("You can try searching for these common medications:")
            cols = st.columns(len(common_meds))
            
            for i, med in enumerate(common_meds):
                if cols[i].button(med):
                    # Set the search term and trigger search
                    st.session_state.medication_search = med
                    # This simulates clicking the search button
                    st.session_state.search_clicked = True
                    st.rerun()

    # Display currently selected medications
    if st.session_state.selected_medications:
        st.write("Currently selected medications:")
        
        for i, med in enumerate(st.session_state.selected_medications):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"{i+1}. {med}")
            with col2:
                if st.button("Remove", key=f"remove_med_{i}"):
                    st.session_state.selected_medications.pop(i)
                    st.rerun()
        
        if st.button("Clear All Medications"):
            st.session_state.selected_medications = []
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Still allow free text entry for custom medications or complex regimens
    medications_text = st.text_area("Additional medications with dosages", 
                                   height=100,
                                   help="Include any other medications with name, dosage, frequency, and duration.")
    
    # Allergies
    st.write("**Allergies**")
    has_allergies = st.checkbox("Patient has allergies")
    if has_allergies:
        allergies = st.text_area("List allergies and reactions", height=80)
    
    # Vital Signs
    st.write("**Vital Signs (if relevant)**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bp = st.text_input("BP (mmHg)", placeholder="120/80")
    with col2:
        pulse = st.text_input("Pulse (bpm)", placeholder="72")
    with col3:
        temp = st.text_input("Temp (°C)", placeholder="37.0")
    with col4:
        spo2 = st.text_input("SpO2 (%)", placeholder="98")
    
    # Clinical Summary
    st.write("**Clinical Summary**")
    clinical_info = st.text_area("Clinical History and Presentation", 
                                height=150,
                                help="Include relevant history, current symptoms, and physical examination findings.")
    diagnosis = st.text_area("Working Diagnosis", 
                           height=100, 
                           help="Current diagnosis or differential diagnoses being considered.")
    
    # Referral Details
    st.subheader("Referral Details")
    col1, col2 = st.columns(2)
    with col1:
        reason_categories = ["Consultation", "Treatment", "Procedure", "Second Opinion", "Test/Investigation", "Other"]
        reason_category = st.selectbox("Reason Category", options=reason_categories)
        reason = st.text_area("Specific Reason for Referral", 
                             height=100,
                             help="Specify the clinical question or reason for the consultation.")
    with col2:
        referred_doctor_email = st.text_input("Consulting Doctor's Email", 
                                             help="Email of the doctor you're referring to.")
        referred_doctor_specialty = st.text_input("Consulting Doctor's Specialty")
        notes = st.text_area("Special Instructions or Questions", 
                            height=100,
                            help="Specific questions you'd like answered or special instructions.")
    
    # Previous Investigations
    st.subheader("Previous Investigations")
    has_previous_investigations = st.checkbox("Previous investigations performed")
    if has_previous_investigations:
        investigation_types = st.multiselect("Investigation Types", 
                                            options=["Lab Tests", "X-Ray", "CT", "MRI", "Ultrasound", 
                                                    "Pathology", "ECG", "Other"])
        investigation_notes = st.text_area("Investigation Details", height=100)
    
    # Attachments
    st.subheader("Attachments")
    uploaded_files = st.file_uploader("Upload relevant documents or images", 
                                     accept_multiple_files=True,
                                     type=["jpg", "jpeg", "png", "pdf", "dcm"])
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} files")
    
    # Submit button
    if st.button("Submit Referral"):
        if not (patient_name and patient_dob and patient_gender and patient_id and 
                clinical_info and reason and urgency and referred_doctor_email):
            st.error("Please fill in all required fields")
        else:
            # Compile all the medical history into a structured format
            medical_history = []
            if diabetes: medical_history.append("Diabetes")
            if hypertension: medical_history.append("Hypertension")
            if heart_disease: medical_history.append("Heart Disease")
            if respiratory_disease: medical_history.append("Respiratory Disease")
            if kidney_disease: medical_history.append("Kidney Disease")
            if liver_disease: medical_history.append("Liver Disease")
            if cancer: medical_history.append("Cancer")
            if autoimmune: medical_history.append("Autoimmune Disease")
            if other_history and 'other_history_text' in locals(): 
                medical_history.append(f"Other: {other_history_text}")
            
            # Compile medications
            all_medications = []
            
            # Add medications from FDA database selection
            if st.session_state.selected_medications:
                all_medications.extend(st.session_state.selected_medications)
            
            # Add manually entered medications
            if medications_text:
                all_medications.append(f"Additional medications: {medications_text}")
            
            # Format the final medication list
            final_medications = "\n".join(all_medications)
            
            # Compile allergies
            allergy_info = allergies if has_allergies and 'allergies' in locals() else "No known allergies"
            
            # Compile vital signs
            vital_signs = {
                "BP": bp if 'bp' in locals() and bp else "Not recorded",
                "Pulse": pulse if 'pulse' in locals() and pulse else "Not recorded",
                "Temp": temp if 'temp' in locals() and temp else "Not recorded",
                "SpO2": spo2 if 'spo2' in locals() and spo2 else "Not recorded"
            }
            
            # Compile investigations
            investigations = {
                "performed": has_previous_investigations,
                "types": investigation_types if has_previous_investigations and 'investigation_types' in locals() else [],
                "notes": investigation_notes if has_previous_investigations and 'investigation_notes' in locals() else ""
            }
            
            # Calculate age from DOB
            today = datetime.now().date()
            patient_age = today.year - patient_dob.year - ((today.month, today.day) < (patient_dob.month, patient_dob.day))
            
            # Create patient details dictionary
            patient_details = {
                'name': patient_name,
                'age': patient_age,
                'dob': patient_dob.strftime("%Y-%m-%d"),
                'gender': patient_gender,
                'id': patient_id,
                'phone': patient_phone if 'patient_phone' in locals() and patient_phone else "",
                'language': patient_language if needs_interpreter and 'patient_language' in locals() else "",
                'needs_interpreter': needs_interpreter
            }
            
            # Additional referral details
            referral_details = {
                'urgency': urgency,
                'timeframe': expected_timeframe,
                'category': reason_category,
                'specialty': referred_doctor_specialty,
                'hospital': hospital,
                'department': department,
                'medical_history': medical_history,
                'medications': final_medications,
                'allergies': allergy_info,
                'vital_signs': vital_signs,
                'investigations': investigations
            }
            
            # Create the referral
            try:
                from referral import create_referral
                
                referral_id = create_referral(
                    st.session_state.user_id, referred_doctor_email, patient_details,
                    clinical_info, diagnosis, reason, urgency, notes, uploaded_files,
                    additional_details=referral_details
                )
                
                st.success(f"Referral created successfully! Referral ID: {referral_id}")
                st.info("An email notification has been sent to the consulting doctor.")
                
                # Clear the selected medications after successful submission
                st.session_state.selected_medications = []
                
                if 'last_email' in st.session_state:
                    with st.expander("Email Preview"):
                        st.write(f"**To:** {st.session_state.last_email['to']}")
                        st.write(f"**Subject:** {st.session_state.last_email['subject']}")
                        st.write(f"**Message:**\n{st.session_state.last_email['message']}")
            
            except Exception as e:
                st.error(f"Error creating referral: {str(e)}")
                st.exception(e)

def render_view_referrals():
    """Render the page for viewing referrals."""
    from styles import format_status_badge, format_urgency_badge
    
    st.markdown('<div class="main-header">View Referrals</div>', unsafe_allow_html=True)
    
    # Filter options
    st.markdown('<div class="sub-header">Filter Options</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", options=["All", "Pending", "In Progress", "Completed", "Closed"])
        with col2:
            urgency_filter = st.selectbox("Urgency", options=["All", "Routine", "Urgent", "Emergency"])
        with col3:
            date_range = st.date_input("Date Range", value=[datetime.now().date() - pd.Timedelta(days=30), datetime.now().date()])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Get referrals for the doctor
    referrals = get_referrals_for_doctor(st.session_state.user_id, st.session_state.user_role)
    
    # Apply filters
    filtered_referrals = referrals
    if status_filter != "All":
        filtered_referrals = [r for r in filtered_referrals if r['status'] == status_filter]
    if urgency_filter != "All":
        filtered_referrals = [r for r in filtered_referrals if r['urgency'] == urgency_filter]
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_referrals = [r for r in filtered_referrals if 
                             start_date <= datetime.strptime(r['referral_date'].split()[0], '%Y-%m-%d').date() <= end_date]
    
    # Display referrals
    if filtered_referrals:
        st.markdown(f'<div class="sub-header">Found {len(filtered_referrals)} referrals</div>', unsafe_allow_html=True)
        
        for ref in filtered_referrals:
            with st.expander(f"Patient: {ref['patient_name']} - {format_status_badge(ref['status'])} - Date: {ref['referral_date'].split()[0]}", expanded=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Patient ID:** {ref['patient_id']}")
                    st.write(f"**Age:** {ref['patient_age']}")
                    st.write(f"**Gender:** {ref['patient_gender']}")
                with col2:
                    st.markdown(f"**Urgency:** {format_urgency_badge(ref['urgency'])}", unsafe_allow_html=True)
                    if st.session_state.user_role in ["Referring Doctor", "Both"]:
                        referred_name = ref.get('referred_doctor_name', 'Not in system')
                        st.write(f"**Referred To:** {referred_name}")
                    else:
                        st.write(f"**Referred By:** {ref['referring_doctor_name']}")
                
                st.write(f"**Reason for Referral:** {ref['reason_for_referral']}")
                
                st.markdown('<div style="text-align: center; margin-top: 15px;">', unsafe_allow_html=True)
                if st.button(f"View Full Details", key=f"view_{ref['referral_id']}"):
                    st.session_state.selected_referral = ref['referral_id']
                    st.session_state.current_page = "referral_details"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No referrals found matching your criteria")


def render_view_consultations():
    """Render the page for viewing consultations."""
    st.header("View Consultations")
    
    conn = sqlite3.connect('referral_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get consultations based on the doctor's role
    if st.session_state.user_role in ["Referring Doctor", "Both"]:
        # Get consultations for referrals made by this doctor
        c.execute('''
        SELECT c.*, 
               r.patient_name, r.referral_date, r.urgency,
               u.full_name as consulting_doctor_name
        FROM consultations c
        JOIN referrals r ON c.referral_id = r.referral_id
        JOIN users u ON c.consulting_doctor_id = u.id
        WHERE r.referring_doctor_id = ?
        ORDER BY c.consultation_date DESC
        ''', (st.session_state.user_id,))
    else:
        # Get consultations made by this doctor
        c.execute('''
        SELECT c.*, 
               r.patient_name, r.referral_date, r.urgency,
               u.full_name as referring_doctor_name
        FROM consultations c
        JOIN referrals r ON c.referral_id = r.referral_id
        JOIN users u ON r.referring_doctor_id = u.id
        WHERE c.consulting_doctor_id = ?
        ORDER BY c.consultation_date DESC
        ''', (st.session_state.user_id,))
    
    consultations = [dict(row) for row in c.fetchall()]
    conn.close()
    
    if consultations:
        st.subheader(f"Found {len(consultations)} consultations")
        
        for cons in consultations:
            with st.expander(f"Patient: {cons['patient_name']} - Status: {cons['status']} - Date: {cons['consultation_date'].split()[0]}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.session_state.user_role in ["Referring Doctor", "Both"]:
                        st.write(f"**Consulting Doctor:** {cons['consulting_doctor_name']}")
                    else:
                        st.write(f"**Referring Doctor:** {cons['referring_doctor_name']}")
                    st.write(f"**Referral Date:** {cons['referral_date'].split()[0]}")
                    st.write(f"**Consultation Date:** {cons['consultation_date'].split()[0]}")
                with col2:
                    st.write(f"**Urgency:** {cons['urgency']}")
                    st.write(f"**Status:** {cons['status']}")
                
                st.write("**Assessment:**")
                st.write(cons['assessment'])
                
                st.write("**Recommendation:**")
                st.write(cons['recommendation'])
                
                if cons['additional_information_needed']:
                    st.write("**Additional Information Needed:**")
                    st.write(cons['additional_information_needed'])
                
                if st.button(f"View Full Details", key=f"view_cons_{cons['referral_id']}"):
                    st.session_state.selected_referral = cons['referral_id']
                    st.session_state.current_page = "referral_details"
                    st.rerun()
    else:
        st.info("No consultations found")


def render_analytics():
    """Render the analytics page."""
    from styles import PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR
    
    st.markdown('<div class="main-header">Analytics Dashboard</div>', unsafe_allow_html=True)
    
    # Create a common theme for all charts
    plotly_layout = dict(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#212121'),
        title_font=dict(color=PRIMARY_COLOR),
        colorway=[PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR, '#FF9800', '#F44336', '#9C27B0', '#2196F3'],
        margin=dict(t=50, b=50, l=50, r=50),
    )
    
    tab1, tab2, tab3 = st.tabs(["System Statistics", "Referral Metrics", "Doctor Performance"])
    
    with tab1:
        st.markdown('<div class="sub-header">User Statistics</div>', unsafe_allow_html=True)
        user_analytics = get_user_analytics()
        
        # Registration over time
        if not user_analytics['registration_data'].empty:
            st.write("User Registration Over Time")
            fig = px.line(user_analytics['registration_data'], 
                        x='Registration Date', 
                        y='Count',
                        title='User Registrations')
            fig.update_layout(**plotly_layout)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # User distribution by role
        with col1:
            if not user_analytics['role_data'].empty:
                st.write("Users by Role")
                fig = px.pie(user_analytics['role_data'], 
                            names='Role', 
                            values='Count',
                            title='User Distribution by Role')
                fig.update_layout(**plotly_layout)
                st.plotly_chart(fig, use_container_width=True)
        
        # User distribution by specialization
        with col2:
            if not user_analytics['specialization_data'].empty:
                st.write("Users by Specialization")
                fig = px.bar(user_analytics['specialization_data'], 
                            x='Specialization', 
                            y='Count',
                            title='User Distribution by Specialization')
                fig.update_layout(**plotly_layout)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Referral Metrics")
        referral_analytics = get_referral_analytics()
        
        # Referrals over time
        if not referral_analytics['referral_date_data'].empty:
            st.write("Referrals Over Time")
            fig = px.line(referral_analytics['referral_date_data'], 
                        x='Referral Date', 
                        y='Count',
                        title='Referral Volume')
            fig.update_layout(**plotly_layout)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # Referrals by status
        with col1:
            if not referral_analytics['status_data'].empty:
                st.write("Referrals by Status")
                fig = px.pie(referral_analytics['status_data'], 
                            names='Status', 
                            values='Count',
                            title='Referral Distribution by Status')
                fig.update_layout(**plotly_layout)
                st.plotly_chart(fig, use_container_width=True)
        
        # Referrals by urgency
        with col2:
            if not referral_analytics['urgency_data'].empty:
                st.write("Referrals by Urgency")
                fig = px.bar(referral_analytics['urgency_data'], 
                            x='Urgency', 
                            y='Count',
                            title='Referral Distribution by Urgency')
                fig.update_layout(**plotly_layout)
                st.plotly_chart(fig, use_container_width=True)
        
        # Average response time
        st.metric("Average Response Time", f"{referral_analytics['avg_response_time']:.2f} days")
    
    with tab3:
        st.subheader("Doctor Performance")
        doctor_analytics = get_doctor_performance_analytics()
        
        col1, col2 = st.columns(2)
        
        # Top referring doctors
        with col1:
            if not doctor_analytics['top_referring_doctors'].empty:
                st.write("Top Referring Doctors")
                fig = px.bar(doctor_analytics['top_referring_doctors'], 
                            x='Doctor', 
                            y='Referral Count',
                            title='Top Referring Doctors')
                fig.update_layout(**plotly_layout)
                st.plotly_chart(fig, use_container_width=True)
        
        # Top consulting doctors
        with col2:
            if not doctor_analytics['top_consulting_doctors'].empty:
                st.write("Top Consulting Doctors")
                fig = px.bar(doctor_analytics['top_consulting_doctors'], 
                            x='Doctor', 
                            y='Consultation Count',
                            title='Top Consulting Doctors')
                fig.update_layout(**plotly_layout)
                st.plotly_chart(fig, use_container_width=True)
        
        # Doctor response times
        if not doctor_analytics['doctor_response_times'].empty:
            st.write("Doctor Response Times")
            fig = px.bar(doctor_analytics['doctor_response_times'], 
                        x='Doctor', 
                        y='Average Response Time (days)',
                        title='Average Response Time by Doctor')
            fig.update_layout(**plotly_layout)
            st.plotly_chart(fig, use_container_width=True)


def render_profile():
    """Render the user profile page."""
    st.header("User Profile")
    
    conn = sqlite3.connect('referral_system.db')
    c = conn.cursor()
    
    # Get user details
    c.execute('''
    SELECT username, email, full_name, specialization, hospital, role, registration_date
    FROM users
    WHERE id = ?
    ''', (st.session_state.user_id,))
    
    user = c.fetchone()
    conn.close()
    
    if user:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            st.write(f"**Full Name:** {user[2]}")
            st.write(f"**Username:** {user[0]}")
            st.write(f"**Email:** {user[1]}")
            st.write(f"**Role:** {user[5]}")
            st.write(f"**Registration Date:** {user[6]}")
        
        with col2:
            st.subheader("Professional Information")
            st.write(f"**Specialization:** {user[3] or 'Not specified'}")
            st.write(f"**Hospital/Clinic:** {user[4] or 'Not specified'}")
        
        # User statistics
        st.subheader("Your Statistics")
        
        conn = sqlite3.connect('referral_system.db')
        c = conn.cursor()
        
        # Count referrals
        c.execute('''
        SELECT COUNT(*) FROM referrals WHERE referring_doctor_id = ?
        ''', (st.session_state.user_id,))
        referral_count = c.fetchone()[0]
        
        # Count consultations
        c.execute('''
        SELECT COUNT(*) FROM consultations WHERE consulting_doctor_id = ?
        ''', (st.session_state.user_id,))
        consultation_count = c.fetchone()[0]
        
        # Calculate average response time
        c.execute('''
        SELECT AVG(julianday(c.consultation_date) - julianday(r.referral_date))
        FROM consultations c
        JOIN referrals r ON c.referral_id = r.referral_id
        WHERE c.consulting_doctor_id = ?
        ''', (st.session_state.user_id,))
        avg_response_time = c.fetchone()[0] or 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Referrals Created", referral_count)
        with col2:
            st.metric("Consultations Provided", consultation_count)
        with col3:
            st.metric("Avg Response Time", f"{avg_response_time:.2f} days")
        
        # Update profile form
        st.subheader("Update Profile")
        
        with st.form("update_profile"):
            new_full_name = st.text_input("Full Name", value=user[2])
            new_email = st.text_input("Email", value=user[1])
            new_specialization = st.text_input("Specialization", value=user[3] or "")
            new_hospital = st.text_input("Hospital/Clinic", value=user[4] or "")
            
            old_password = st.text_input("Current Password (required to update)", type="password")
            new_password = st.text_input("New Password (leave blank to keep current)", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Update Profile")
            
            if submit:
                if old_password:
                    # Verify old password
                    c.execute('''
                    SELECT id FROM users 
                    WHERE id = ? AND password = ?
                    ''', (st.session_state.user_id, hash_password(old_password)))
                    
                    if c.fetchone():
                        updates = []
                        params = []
                        
                        if new_full_name != user[2]:
                            updates.append("full_name = ?")
                            params.append(new_full_name)
                        
                        if new_email != user[1]:
                            updates.append("email = ?")
                            params.append(new_email)
                        
                        if new_specialization != (user[3] or ""):
                            updates.append("specialization = ?")
                            params.append(new_specialization)
                        
                        if new_hospital != (user[4] or ""):
                            updates.append("hospital = ?")
                            params.append(new_hospital)
                        
                        if new_password:
                            if new_password == confirm_password:
                                updates.append("password = ?")
                                params.append(hash_password(new_password))
                            else:
                                st.error("New passwords do not match")
                        
                        if updates:
                            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                            params.append(st.session_state.user_id)
                            
                            try:
                                c.execute(query, params)
                                conn.commit()
                                st.success("Profile updated successfully!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Email already in use")
                        else:
                            st.info("No changes to update")
                    else:
                        st.error("Current password is incorrect")
                else:
                    st.error("Current password is required to update profile")
        
        conn.close()


def render_referral_details():
    """Render the page for viewing detailed referral information with enhanced layout."""
    from styles import PRIMARY_COLOR, STATUS_COLORS, URGENCY_COLORS, format_status_badge, format_urgency_badge
    import json
    
    if 'selected_referral' not in st.session_state:
        st.error("No referral selected")
        return
    
    referral_id = st.session_state.selected_referral
    referral = get_referral_details(referral_id)
    
    # Parse additional details if present
    additional_details = {}
    if 'additional_details' in referral and referral.get('additional_details'):
        try:
            additional_details = json.loads(referral['additional_details'])
        except:
            additional_details = {}
    
    # Header with status indicator
    st.markdown(f'<div class="main-header">Referral Details</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**Referral ID:** {referral_id}")
        st.markdown(f"**Created:** {referral.get('creation_date', referral.get('referral_date', '')).split()[0]}")
    with col2:
        st.markdown(f"**Status:** {format_status_badge(referral['status'])}", unsafe_allow_html=True)
        st.markdown(f"**Urgency:** {format_urgency_badge(referral['urgency'])}", unsafe_allow_html=True)
    with col3:
        # Add a button to go back
        if st.button("Back to List", key="back_button"):
            st.session_state.current_page = "dashboard"
            st.session_state.pop('selected_referral', None)
            st.rerun()
    
    # Rest of the function with if checks for all attributes...
    # (your existing render_referral_details code with checks for existence of each field)
    
    # Display tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Patient Information", 
        "Clinical Information", 
        "Referral Details", 
        "Consultation Response",
        "AI Recommendations"
    ])
    
    with tab1:
        st.subheader("Patient Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {referral['patient_name']}")
            st.markdown(f"**ID/MRN:** {referral['patient_id']}")
            st.markdown(f"**Gender:** {referral['patient_gender']}")
            if 'patient_dob' in referral and referral['patient_dob']:
                st.markdown(f"**Date of Birth:** {referral['patient_dob']}")
            st.markdown(f"**Age:** {referral['patient_age']}")
        
        with col2:
            if 'patient_phone' in referral and referral['patient_phone']:
                st.markdown(f"**Phone:** {referral['patient_phone']}")
            
            # Display language and interpreter needs if present
            if additional_details.get('needs_interpreter'):
                st.markdown(f"**Primary Language:** {additional_details.get('language', 'Not specified')}")
                st.markdown("**Needs Interpreter:** Yes")
        
        # Display medical history if available
        if additional_details.get('medical_history'):
            st.subheader("Medical History")
            history_items = additional_details.get('medical_history', [])
            if history_items:
                for item in history_items:
                    st.markdown(f"• {item}")
            else:
                st.markdown("No significant medical history recorded")
        
        # Display allergies if available
        if additional_details.get('allergies'):
            st.subheader("Allergies")
            st.markdown(additional_details.get('allergies', 'No allergies recorded'))
        
        # Display current medications if available
        if additional_details.get('medications'):
            st.subheader("Current Medications")
            st.markdown(additional_details.get('medications', 'No medications recorded'))
    
    with tab2:
        st.subheader("Clinical Information")
        
        # Display vital signs if available
        vital_signs = additional_details.get('vital_signs', {})
        if vital_signs:
            st.markdown("**Vital Signs:**")
            cols = st.columns(4)
            if vital_signs.get('BP') and vital_signs.get('BP') != "Not recorded":
                cols[0].metric("BP (mmHg)", vital_signs.get('BP'))
            if vital_signs.get('Pulse') and vital_signs.get('Pulse') != "Not recorded":
                cols[1].metric("Pulse (bpm)", vital_signs.get('Pulse'))
            if vital_signs.get('Temp') and vital_signs.get('Temp') != "Not recorded":
                cols[2].metric("Temp (°C)", vital_signs.get('Temp'))
            if vital_signs.get('SpO2') and vital_signs.get('SpO2') != "Not recorded":
                cols[3].metric("SpO2 (%)", vital_signs.get('SpO2'))
        
        st.markdown("**Clinical History and Presentation:**")
        st.markdown(referral['clinical_information'])
        
        if referral['diagnosis']:
            st.markdown("**Working Diagnosis:**")
            st.markdown(referral['diagnosis'])
        
        # Display previous investigations if available
        investigations = additional_details.get('investigations', {})
        if investigations and investigations.get('performed'):
            st.subheader("Previous Investigations")
            st.markdown("**Types:**")
            for inv_type in investigations.get('types', []):
                st.markdown(f"• {inv_type}")
            if investigations.get('notes'):
                st.markdown("**Notes:**")
                st.markdown(investigations.get('notes'))
        
        # Display attachments if any
        if referral['attachment_paths']:
            st.subheader("Attachments")
            paths = referral['attachment_paths'].split(',')
            
            for path in paths:
                file_name = os.path.basename(path)
                file_ext = os.path.splitext(file_name)[1].lower()
                
                try:
                    if file_ext in ['.jpg', '.jpeg', '.png']:
                        with open(path, "rb") as file:
                            img = Image.open(io.BytesIO(file.read()))
                            st.image(img, caption=file_name, width=300)
                    else:
                        st.markdown(f"**File:** {file_name}")
                        st.download_button(
                            label=f"Download {file_name}",
                            data=open(path, "rb").read(),
                            file_name=file_name,
                            key=f"download_{file_name}"
                        )
                except FileNotFoundError:
                    st.error(f"File {file_name} not found")
    
    with tab3:
        st.subheader("Referral Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Referring Doctor Information:**")
            st.markdown(f"**Name:** {referral['referring_doctor_name']}")
            st.markdown(f"**Specialization:** {referral['referring_doctor_specialization'] or 'Not specified'}")
            st.markdown(f"**Hospital/Clinic:** {referral['referring_doctor_hospital'] or 'Not specified'}")
            st.markdown(f"**Email:** {referral['referring_doctor_email']}")
            
            if additional_details.get('department'):
                st.markdown(f"**Department:** {additional_details.get('department')}")
            
            # Display expected response timeframe if available
            if additional_details.get('timeframe'):
                st.markdown(f"**Expected Response:** {additional_details.get('timeframe')}")
        
        with col2:
            st.markdown("**Consulting Doctor Information:**")
            if referral['referred_doctor_name']:
                st.markdown(f"**Name:** {referral['referred_doctor_name']}")
                st.markdown(f"**Specialization:** {referral['referred_doctor_specialization'] or 'Not specified'}")
                st.markdown(f"**Hospital/Clinic:** {referral['referred_doctor_hospital'] or 'Not specified'}")
            else:
                st.markdown(f"**Email:** {referral['referred_doctor_email']}")
            
            if additional_details.get('specialty'):
                st.markdown(f"**Specialty:** {additional_details.get('specialty')}")
        
        st.markdown("**Reason for Referral:**")
        
        # Display reason category if available
        if additional_details.get('category'):
            st.markdown(f"**Category:** {additional_details.get('category')}")
        
        st.markdown(referral['reason_for_referral'])
        
        if referral['additional_notes']:
            st.markdown("**Additional Notes/Instructions:**")
            st.markdown(referral['additional_notes'])
    
    with tab4:
        st.subheader("Consultation Response")
        
        # Check if there's a consultation response
        if 'consultation' in referral:
            consultation = referral['consultation']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Responded By:** {consultation['consulting_doctor_name']}")
                st.markdown(f"**Response Date:** {consultation['consultation_date'].split()[0]}")
            with col2:
                st.markdown(f"**Status:** {format_status_badge(consultation['status'])}", unsafe_allow_html=True)
                if consultation.get('follow_up_required'):
                    st.markdown(f"**Follow-up Required:** Yes, {consultation.get('follow_up_timeframe', 'timeframe not specified')}")
            
            st.markdown("**Assessment:**")
            st.markdown(consultation['assessment'])
            
            if consultation.get('diagnosis'):
                st.markdown("**Diagnosis:**")
                st.markdown(consultation['diagnosis'])
            
            st.markdown("**Recommendation:**")
            st.markdown(consultation['recommendation'])
            
            if consultation.get('treatment_plan'):
                st.markdown("**Treatment Plan:**")
                st.markdown(consultation['treatment_plan'])
            
            if consultation.get('medications'):
                st.markdown("**Medications:**")
                st.markdown(consultation['medications'])
            
            if consultation['additional_information_needed']:
                st.markdown("**Additional Information Needed:**")
                st.markdown(consultation['additional_information_needed'])
            
            # Display attachments if any
            if consultation['attachment_paths']:
                st.subheader("Consultation Attachments")
                paths = consultation['attachment_paths'].split(',')
                
                for path in paths:
                    file_name = os.path.basename(path)
                    file_ext = os.path.splitext(file_name)[1].lower()
                    
                    try:
                        if file_ext in ['.jpg', '.jpeg', '.png']:
                            with open(path, "rb") as file:
                                img = Image.open(io.BytesIO(file.read()))
                                st.image(img, caption=file_name, width=300)
                        else:
                            st.markdown(f"**File:** {file_name}")
                            st.download_button(
                                label=f"Download {file_name}",
                                data=open(path, "rb").read(),
                                file_name=file_name,
                                key=f"download_cons_{file_name}"
                            )
                    except FileNotFoundError:
                        st.error(f"File {file_name} not found")
        else:
            st.info("No consultation response provided yet.")
            
    with tab5:
        st.subheader("GPT-4 AI Recommendations")

        prompt = f"""
        Generate a concise medical consultation summary and actionable recommendations based on the following referral details:

        Patient Information:
        - Name: {referral['patient_name']}
        - Age: {referral['patient_age']}
        - Gender: {referral['patient_gender']}
        - Medical History: {additional_details.get('medical_history', 'Not provided')}
        - Current Medications: {additional_details.get('medications', 'Not provided')}
        - Allergies: {additional_details.get('allergies', 'Not provided')}

        Clinical Information:
        {referral['clinical_information']}

        Diagnosis:
        {referral.get('diagnosis', 'Not provided')}

        Reason for Referral:
        {referral['reason_for_referral']}
        """

        if st.button("Generate AI Recommendations"):
            with st.spinner("Generating recommendations via GPT-4..."):
                try:
                    completion = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert medical consultant providing clear and concise recommendations."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    ai_response = completion.choices[0].message.content
                    st.markdown(ai_response)
                except Exception as e:
                    st.error(f"Failed to generate GPT-4 response: {str(e)}")

    # Form for submitting consultation response - enhanced version
    is_consulting_doctor = (
        st.session_state.user_role in ["Consulting Doctor", "Both"] and
        (referral['referred_doctor_id'] == st.session_state.user_id or
         referral['referred_doctor_email'] == st.session_state.email)
    )
    
    if is_consulting_doctor and referral['status'] == 'Pending':
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.subheader("Provide Consultation")
        
        with st.form("consultation_form"):
            assessment = st.text_area("Assessment", height=150, 
                                    help="Provide your clinical assessment of the case.")
            
            diagnosis = st.text_area("Diagnosis", height=100,
                                   help="Enter your diagnosis or differential diagnoses.")
            
            recommendation = st.text_area("Recommendation", height=150,
                                        help="Provide your recommendations for management.")
            
            treatment_plan = st.text_area("Treatment Plan", height=100,
                                        help="Outline the treatment plan if applicable.")
            
            medications = st.text_area("Medications", height=100,
                                     help="List recommended medications with dosages if applicable.")
            
            additional_info = st.text_area("Additional Information Needed (if any)", height=100,
                                         help="List any additional information or tests needed from the referring doctor.")
            
            follow_up_required = st.checkbox("Follow-up Required")
            follow_up_timeframe = ""
            if follow_up_required:
                follow_up_timeframe = st.selectbox(
                    "Follow-up Timeframe",
                    options=["1 week", "2 weeks", "1 month", "3 months", "6 months", "As needed"]
                )
            
            status = st.selectbox("Status", options=["In Progress", "Completed", "Requires Additional Information"])
            
            uploaded_files = st.file_uploader(
                "Upload relevant documents or images", 
                accept_multiple_files=True,
                type=["jpg", "jpeg", "png", "pdf", "dcm"]
            )
            
            submit = st.form_submit_button("Submit Consultation")
            
            if submit:
                if assessment and recommendation:
                    # Updated submission with enhanced fields
                    success = submit_consultation(
                        referral_id, st.session_state.user_id,
                        assessment, recommendation, additional_info,
                        uploaded_files, status,
                        diagnosis=diagnosis,
                        treatment_plan=treatment_plan,
                        medications=medications,
                        follow_up_required=follow_up_required,
                        follow_up_timeframe=follow_up_timeframe
                    )
                    
                    if success:
                        st.success("Consultation submitted successfully!")
                        # Log the activity
                        conn = sqlite3.connect('referral_system.db')
                        c = conn.cursor()
                        c.execute('''
                        INSERT INTO activity_logs (user_id, activity_type, activity_details, referral_id)
                        VALUES (?, ?, ?, ?)
                        ''', (st.session_state.user_id, 'Submit Consultation', f'Consultation for referral {referral_id} submitted', referral_id))
                        conn.commit()
                        conn.close()
                        
                        st.rerun()
                else:
                    st.error("Assessment and Recommendation are required")
        st.markdown('</div>', unsafe_allow_html=True)