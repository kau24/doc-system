import streamlit as st
import sqlite3
import hashlib
import uuid
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io

# Import modules
from auth import login_user, register_user, hash_password
from database import init_db
from referral import create_referral, get_referrals_for_doctor, get_referral_details
from consultation import submit_consultation
from analytics import get_user_analytics, get_referral_analytics, get_doctor_performance_analytics
from email_service import send_referral_notification, send_consultation_notification
from ui import (render_login_page, render_dashboard, render_dashboard_home, 
               render_create_referral, render_view_referrals, render_view_consultations,
               render_analytics, render_profile, render_referral_details)
from styles import apply_page_styling  # Import styling function

# Initialize session state for pages
def init_session_state():
    """Initialize session state variables."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'email' not in st.session_state:
        st.session_state.email = ""

# Main application
def main():
    """Main function to run the Streamlit app."""
    # Apply styling
    apply_page_styling()
    
    # Initialize session state
    init_session_state()
    
    # Initialize database
    init_db()
    
    # Render the appropriate page based on the session state
    if not st.session_state.logged_in:
        render_login_page()
    else:
        if st.session_state.current_page == "dashboard":
            render_dashboard()
        elif st.session_state.current_page == "referral_details":
            render_referral_details()

if __name__ == "__main__":
    main()