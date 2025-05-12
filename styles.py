# styles.py

# Color palette
PRIMARY_COLOR = "#006E3B"       # Dark Green
SECONDARY_COLOR = "#40A86A"     # Medium Green
ACCENT_COLOR = "#8BD3A8"        # Light Green
BACKGROUND_COLOR = "#F0F7F2"    # Very Light Green/Off-White
TEXT_COLOR = "#212121"          # Dark Gray for text
ERROR_COLOR = "#D32F2F"         # Red for errors
SUCCESS_COLOR = "#388E3C"       # Green for success messages
WARNING_COLOR = "#F57C00"       # Orange for warnings
INFO_COLOR = "#0288D1"          # Blue for info messages

# Status colors
STATUS_COLORS = {
    'Pending': "#F57C00",       # Orange
    'In Progress': "#2196F3",   # Blue
    'Completed': "#4CAF50",     # Green
    'Closed': "#9E9E9E",        # Gray
    'Requires Additional Information': "#9C27B0"  # Purple
}

# Urgency colors
URGENCY_COLORS = {
    'Routine': "#4CAF50",       # Green
    'Urgent': "#FF9800",        # Orange
    'Emergency': "#F44336"      # Red
}

# CSS for custom styling
CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        color: """ + PRIMARY_COLOR + """;
        margin-bottom: 1rem;
        border-bottom: 2px solid """ + ACCENT_COLOR + """;
        padding-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.8rem;
        color: """ + SECONDARY_COLOR + """;
        margin-bottom: 0.8rem;
    }
    
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid """ + PRIMARY_COLOR + """;
    }
    
    .metric-card {
        background-color: """ + BACKGROUND_COLOR + """;
        border-left: 5px solid """ + PRIMARY_COLOR + """;
        padding: 1rem;
        border-radius: 5px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: """ + PRIMARY_COLOR + """;
    }
    
    .metric-label {
        color: """ + TEXT_COLOR + """;
        font-size: 1rem;
    }
    
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        color: white;
        display: inline-block;
    }
    
    .urgency-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        color: white;
        display: inline-block;
    }
    
    .referral-item {
        border-left: 4px solid """ + SECONDARY_COLOR + """;
        padding-left: 1rem;
        margin-bottom: 0.8rem;
    }
    
    .form-section {
        background-color: """ + BACKGROUND_COLOR + """;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    .btn-primary {
        background-color: """ + PRIMARY_COLOR + """;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 0.5rem 0;
        cursor: pointer;
    }
    
    .btn-secondary {
        background-color: """ + SECONDARY_COLOR + """;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 0.5rem 0;
        cursor: pointer;
    }
    
    .logo-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }
    
    .logo-area {
        display: flex;
        align-items: center;
    }
    
    .logo-area img {
        margin-right: 1rem;
    }
    
    .institution-name {
        font-size: 1.5rem;
        font-weight: bold;
        color: """ + PRIMARY_COLOR + """;
    }
    
    .institution-details {
        font-size: 0.9rem;
        color: """ + TEXT_COLOR + """;
    }
    
    .clinical-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .clinical-card-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: """ + PRIMARY_COLOR + """;
        border-bottom: 1px solid """ + ACCENT_COLOR + """;
        padding-bottom: 0.3rem;
    }
    
    .section-divider {
        border-top: 1px solid """ + ACCENT_COLOR + """;
        margin: 1.5rem 0;
    }
</style>
"""

def apply_page_styling():
    """Apply the default green-themed styling to the Streamlit app."""
    import streamlit as st
    
    # Set page config
    st.set_page_config(
        page_title="Doctor Referral System",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def format_status_badge(status):
    """Return HTML for a colored status badge."""
    color = STATUS_COLORS.get(status, "#9E9E9E")  # Default to gray if status not found
    return f'<span class="status-badge" style="background-color: {color};">{status}</span>'

def format_urgency_badge(urgency):
    """Return HTML for a colored urgency badge."""
    color = URGENCY_COLORS.get(urgency, "#9E9E9E")  # Default to gray if urgency not found
    return f'<span class="urgency-badge" style="background-color: {color};">{urgency}</span>'

def metric_card(title, value, description=""):
    """Create a styled metric card with title, value, and optional description."""
    html = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        <div style="font-size:0.8rem;">{description}</div>
    </div>
    """
    return html

def logo_header(institution_name="Medical Referral System", department="", logo_path=None):
    """Create a styled header with logo and institution name."""
    logo_html = f'<img src="{logo_path}" width="60" />' if logo_path else '🏥'
    
    html = f"""
    <div class="logo-header">
        <div class="logo-area">
            {logo_html}
            <div>
                <div class="institution-name">{institution_name}</div>
                <div class="institution-details">{department}</div>
            </div>
        </div>
    </div>
    """
    return html