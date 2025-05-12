import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration for email service
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

def send_email(recipient_email, subject, message, html_message=None, attachments=None):
    """Send an actual email using SMTP with optional HTML content."""
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach plain text message
        msg.attach(MIMEText(message, 'plain'))
        
        # Attach HTML message if provided
        if html_message:
            msg.attach(MIMEText(html_message, 'html'))
        
        # Attach files if provided
        if attachments:
            for attachment in attachments:
                with open(attachment, 'rb') as file:
                    part = MIMEApplication(file.read(), Name=os.path.basename(attachment))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                    msg.attach(part)
        
        # Connect to server and send email
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()  # Secure the connection
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent to {recipient_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Store in session state for UI display (fallback)
        if 'last_email' not in st.session_state:
            st.session_state.last_email = {}
        
        st.session_state.last_email = {
            'to': recipient_email,
            'subject': subject,
            'message': message,
            'error': str(e)
        }
        return False

def get_referral_email_template(referral, referral_id):
    """Get HTML email template for referral notification."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #006E3B; color: white; padding: 10px 20px; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ font-size: 12px; color: #777; padding: 10px 20px; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .priority-high {{ color: #D32F2F; font-weight: bold; }}
            .priority-medium {{ color: #F57C00; font-weight: bold; }}
            .priority-normal {{ color: #388E3C; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Medical Referral Notification</h2>
            </div>
            <div class="content">
                <p>Dear Doctor,</p>
                
                <p>You have received a new patient referral from Dr. {referral['referring_doctor']}.</p>
                
                <table>
                    <tr>
                        <th>Referral ID</th>
                        <td>{referral_id}</td>
                    </tr>
                    <tr>
                        <th>Patient Name</th>
                        <td>{referral['patient_name']}</td>
                    </tr>
                    <tr>
                        <th>Urgency</th>
                        <td class="priority-{'high' if referral['urgency'] == 'Emergency' else 'medium' if referral['urgency'] == 'Urgent' else 'normal'}">{referral['urgency']}</td>
                    </tr>
                </table>
                
                <p>Please log in to the Doctor Referral System to view complete patient information and provide your consultation.</p>
                
                <p>Reason for Referral:</p>
                <p>{referral['reason_for_referral']}</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>© {datetime.now().year} Doctor Referral System</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_consultation_email_template(consultation, referral_id, status, referring_doctor):
    """Get HTML email template for consultation notification."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #006E3B; color: white; padding: 10px 20px; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ font-size: 12px; color: #777; padding: 10px 20px; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .status-completed {{ color: #388E3C; font-weight: bold; }}
            .status-inprogress {{ color: #2196F3; font-weight: bold; }}
            .status-additional {{ color: #9C27B0; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Consultation Response</h2>
            </div>
            <div class="content">
                <p>Dear Dr. {referring_doctor},</p>
                
                <p>A consultation response has been submitted by Dr. {consultation['consulting_doctor']} for your referral.</p>
                
                <table>
                    <tr>
                        <th>Referral ID</th>
                        <td>{referral_id}</td>
                    </tr>
                    <tr>
                        <th>Patient Name</th>
                        <td>{consultation['patient_name']}</td>
                    </tr>
                    <tr>
                        <th>Status</th>
                        <td class="status-{'completed' if status == 'Completed' else 'inprogress' if status == 'In Progress' else 'additional'}">{status}</td>
                    </tr>
                </table>
                
                {f"<p><strong>Additional Information Needed:</strong></p><p>{consultation.get('additional_information_needed', '')}</p>" if status == 'Requires Additional Information' else ""}
                
                <p>Please log in to the Doctor Referral System to view the complete consultation details.</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>© {datetime.now().year} Doctor Referral System</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_referral_notification(recipient_email, referral_id):
    """Send an email notification for a new referral."""
    # Get referral details for personalized email
    conn = sqlite3.connect('referral_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
    SELECT r.*, u.full_name as referring_doctor
    FROM referrals r
    JOIN users u ON r.referring_doctor_id = u.id
    WHERE r.referral_id = ?
    ''', (referral_id,))
    
    referral = dict(c.fetchone())
    conn.close()
    
    # Create a more informative email message
    message = f"""
Dear Doctor,

A new referral (ID: {referral_id}) has been sent to you by Dr. {referral['referring_doctor']}.

Patient: {referral['patient_name']}
Urgency: {referral['urgency']}
Reason: {referral['reason_for_referral']}

Please log in to the system to view the complete details and provide your consultation.

This is an automated message. Please do not reply to this email.
    """
    
    subject = f"New Medical Referral - {referral['urgency']} - {referral['patient_name']}"
    
    # Get HTML template
    html_message = get_referral_email_template(referral, referral_id)
    
    # Send the actual email
    success = send_email(recipient_email, subject, message, html_message)
    
    # Store in session state for UI preview (even if email sending fails)
    if 'last_email' not in st.session_state:
        st.session_state.last_email = {}
    
    st.session_state.last_email = {
        'to': recipient_email,
        'subject': subject,
        'message': message,
        'success': success
    }

def send_consultation_notification(recipient_email, referral_id, status):
    """Send an email notification for a consultation response."""
    # Get consultation details for personalized email
    conn = sqlite3.connect('referral_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
    SELECT c.*, r.patient_name, u.full_name as consulting_doctor
    FROM consultations c
    JOIN referrals r ON c.referral_id = r.referral_id
    JOIN users u ON c.consulting_doctor_id = u.id
    WHERE c.referral_id = ? ORDER BY c.consultation_date DESC LIMIT 1
    ''', (referral_id,))
    
    consultation = dict(c.fetchone())
    
    # Get referring doctor's details
    c.execute('''
    SELECT u.full_name
    FROM referrals r
    JOIN users u ON r.referring_doctor_id = u.id
    WHERE r.referral_id = ?
    ''', (referral_id,))
    
    referring_doctor = c.fetchone()[0]
    conn.close()
    
    # Create a more informative email message
    message = f"""
Dear Dr. {referring_doctor},

A consultation response for referral (ID: {referral_id}) has been submitted by Dr. {consultation['consulting_doctor']}.

Patient: {consultation['patient_name']}
Status: {status}

{consultation.get('additional_information_needed', '') if status == 'Requires Additional Information' else ''}

Please log in to the system to view the complete consultation details.

This is an automated message. Please do not reply to this email.
    """
    
    subject = f"Consultation Response - {status} - Referral ID: {referral_id}"
    
    # Get HTML template
    html_message = get_consultation_email_template(consultation, referral_id, status, referring_doctor)
    
    # Send the actual email
    success = send_email(recipient_email, subject, message, html_message)
    
    # Store in session state for UI preview
    if 'last_email' not in st.session_state:
        st.session_state.last_email = {}
    
    st.session_state.last_email = {
        'to': recipient_email,
        'subject': subject,
        'message': message,
        'success': success
    }

def render_email_settings():
    """Render the email settings page."""
    st.header("Email Server Configuration")
    
    # Display current settings
    st.subheader("Current Email Settings")
    st.write(f"**SMTP Server:** {os.getenv('EMAIL_SERVER', 'Not configured')}")
    st.write(f"**SMTP Port:** {os.getenv('EMAIL_PORT', 'Not configured')}")
    st.write(f"**Email Username:** {os.getenv('EMAIL_USERNAME', 'Not configured')}")
    
    # Form to update settings
    st.subheader("Update Email Settings")
    with st.form("email_settings_form"):
        server = st.text_input("SMTP Server", value=os.getenv("EMAIL_SERVER", ""))
        port = st.number_input("SMTP Port", min_value=1, max_value=65535, value=int(os.getenv("EMAIL_PORT", 587)))
        username = st.text_input("Email Username", value=os.getenv("EMAIL_USERNAME", ""))
        password = st.text_input("Email Password", type="password")
        
        submit = st.form_submit_button("Save Settings")
        
        if submit:
            # Update .env file
            with open(".env", "w") as f:
                f.write(f"EMAIL_SERVER={server}\n")
                f.write(f"EMAIL_PORT={port}\n")
                f.write(f"EMAIL_USERNAME={username}\n")
                if password:
                    f.write(f"EMAIL_PASSWORD={password}\n")
                else:
                    f.write(f"EMAIL_PASSWORD={os.getenv('EMAIL_PASSWORD', '')}\n")
            
            st.success("Email settings updated successfully! Please restart the application for changes to take effect.")

def render_email_test():
    """Render a page to test email sending."""
    st.header("Test Email Configuration")
    
    with st.form("test_email_form"):
        recipient = st.text_input("Recipient Email")
        subject = st.text_input("Subject", value="Test Email from Doctor Referral System")
        message = st.text_area("Message", value="This is a test email to verify the email server configuration.")
        
        submit = st.form_submit_button("Send Test Email")
        
        if submit:
            if recipient:
                # Create HTML version of the message
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #006E3B; color: white; padding: 10px 20px; }}
                        .content {{ padding: 20px; background-color: #f9f9f9; }}
                        .footer {{ font-size: 12px; color: #777; padding: 10px 20px; text-align: center; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Test Email</h2>
                        </div>
                        <div class="content">
                            <p>{message}</p>
                            <p>If you're seeing this email, your email configuration is working correctly!</p>
                        </div>
                        <div class="footer">
                            <p>This is an automated message from the Doctor Referral System.</p>
                            <p>© {datetime.now().year} Doctor Referral System</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                success = send_email(recipient, subject, message, html_message)
                if success:
                    st.success(f"Test email sent successfully to {recipient}")
                else:
                    st.error("Failed to send test email. Check server logs for details.")
            else:
                st.warning("Please enter a recipient email address")