import streamlit as st
import importlib
import os
import sys
import types
import importlib.util
from datetime import datetime

# Set page configuration for the main dashboard
st.set_page_config(
    page_title="SNT Dashboard",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color theme - light blue palette
COLORS = {
    "primary": "#1E88E5",       # Primary blue
    "secondary": "#90CAF9",     # Light blue
    "background": "#E3F2FD",    # Very light blue background
    "text": "#0D47A1",          # Dark blue text
    "accent": "#64B5F6"         # Accent blue
}

# CSS for styling the dashboard
def get_css():
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {COLORS["background"]};
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {COLORS["text"]};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        /* Dashboard title styling */
        .dashboard-title {{
            background-color: {COLORS["primary"]};
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        /* Module cards */
        .module-card {{
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid {COLORS["primary"]};
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .module-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }}
        
        /* Icons in module cards */
        .module-icon {{
            font-size: 24px;
            margin-right: 10px;
        }}
        
        /* Footer styling */
        .footer {{
            background-color: {COLORS["primary"]};
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-top: 30px;
            box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.1);
        }}
        
        /* Back button styling */
        .back-button {{
            background-color: {COLORS["accent"]};
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        
        /* Dividers */
        hr {{
            border-top: 2px solid {COLORS["secondary"]};
            margin: 20px 0;
        }}
        
        /* Button styling */
        .stButton>button {{
            background-color: {COLORS["primary"]};
            color: white;
            border-radius: 5px;
            border: none;
            padding: 8px 16px;
            width: 100%;
            font-weight: bold;
            transition: background-color 0.3s;
        }}
        
        .stButton>button:hover {{
            background-color: {COLORS["text"]};
        }}
    </style>
    """

# Generate a greeting based on time of day
def get_greeting():
    current_hour = datetime.now().hour
    if current_hour < 12:
        return "Good Morning"
    elif current_hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"

# Initialize session state for module navigation
if 'current_module' not in st.session_state:
    st.session_state.current_module = None

# Function to safely import and execute module
def import_and_run_module(module_path, module_name):
    try:
        # Check if file exists
        if not os.path.exists(module_path):
            st.error(f"Module file not found: {module_path}")
            return False
        
        # Read the module content
        with open(module_path, 'r', encoding='utf-8') as file:
            source_code = file.read()
        
        # Remove or comment out st.set_page_config calls
        lines = source_code.split('\n')
        modified_lines = []
        skip_config = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check for st.set_page_config
            if 'st.set_page_config' in line:
                # Comment out the line instead of removing it
                modified_lines.append(f"# {line}")
                # Check if it's a multi-line config
                if '(' in line and ')' not in line:
                    skip_config = True
                continue
            
            # Skip lines until we find the closing parenthesis
            if skip_config:
                modified_lines.append(f"# {line}")
                if ')' in line:
                    skip_config = False
                continue
            
            modified_lines.append(line)
        
        modified_code = '\n'.join(modified_lines)
        
        # Create a temporary module namespace
        module_globals = {
            '__name__': module_name,
            '__file__': module_path,
            'st': st,  # Make sure streamlit is available
        }
        
        # Add other common imports that might be needed
        import pandas as pd
        import numpy as np
        module_globals.update({
            'pd': pd,
            'np': np,
            'os': os,
            'sys': sys,
        })
        
        # Execute the module code
        exec(modified_code, module_globals)
        
        # Try to call main functions if they exist
        if 'main' in module_globals and callable(module_globals['main']):
            module_globals['main']()
        elif 'run' in module_globals and callable(module_globals['run']):
            module_globals['run']()
        
        return True
        
    except Exception as e:
        st.error(f"Error loading module '{module_name}': {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        
        # Show more detailed error information in an expander
        with st.expander("Show detailed error information"):
            import traceback
            st.code(traceback.format_exc())
        
        return False

# Function to create a card for each module
def create_module_card(name, info, base_dir):
    module_name = name.replace('.py', '').replace('_', ' ').title()
    
    card_html = f"""
    <div class="module-card">
        <h3><span class="module-icon">{info['icon']}</span>{module_name}</h3>
        <p>{info['desc']}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Check if the module file exists
    module_file_path = os.path.join(base_dir, name)
    file_exists = os.path.exists(module_file_path)
    
    if not file_exists:
        st.warning(f"Module file not found: {module_file_path}")
    
    if st.button(f"Open {module_name}", 
                 key=f"btn_{name}", 
                 disabled=not file_exists):
        st.session_state.current_module = name
        st.rerun()

# Main function to run the dashboard
def main():
    # Apply custom CSS
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # Create header
    header_html = f"""
    <div class="dashboard-title">
        <h1>🧊 SNT Dashboard</h1>
        <p>{get_greeting()} | {datetime.now().strftime("%A, %B %d, %Y")}</p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # If a module is selected, run it
    if st.session_state.current_module:
        # Add a back button
        if st.button("← Back to Dashboard", key="std_back_btn"):
            st.session_state.current_module = None
            st.rerun()
        
        # Display module title
        module_display_name = st.session_state.current_module.replace('.py', '').replace('_', ' ').title()
        st.markdown(f"<h2>{module_display_name}</h2>", unsafe_allow_html=True)
        
        # Get the module path from main directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        module_path = os.path.join(base_dir, st.session_state.current_module)
        
        # Import and run the module
        module_name = st.session_state.current_module.replace('.py', '')
        success = import_and_run_module(module_path, module_name)
        
        if not success:
            st.error("Failed to load the module. Please check the file and try again.")
            
        return
    
    # Otherwise, show the main dashboard with the modules in 2 columns
    st.markdown("<h2>Select a Section</h2>", unsafe_allow_html=True)
    
    # Define the modules with their descriptions and icons
    modules = {
        "combine_files.py": {"icon": "📊", "desc": "Assembly datasets and manage data preprocessing workflows"},
        "rename_columns.py": {"icon": "🔬", "desc": "Analyze epidemiological data and identify patterns"},
        "create_new_variables.py": {"icon": "📋", "desc": "Evaluate the effectiveness of previous health interventions"},
        "outlier_detection_and_correction.py": {"icon": "🎯", "desc": "Plan and optimize new health intervention strategies"}
    }
    
    # Get the main directory path (same directory as this file)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Display current directory for debugging
    with st.expander("Debug Information"):
        st.write(f"Current working directory: {os.getcwd()}")
        st.write(f"Base directory: {base_dir}")
        st.write("Files in base directory:")
        try:
            files = os.listdir(base_dir)
            for file in files:
                if file.endswith('.py'):
                    st.write(f"  - {file}")
        except Exception as e:
            st.write(f"Error listing files: {e}")
    
    # Create 2 columns
    col1, col2 = st.columns(2)
    
    # Arrange modules in 2 columns
    module_list = list(modules.items())
    
    # First column - modules 0, 2
    with col1:
        for i in range(0, len(module_list), 2):
            if i < len(module_list):
                name, info = module_list[i]
                create_module_card(name, info, base_dir)
    
    # Second column - modules 1, 3
    with col2:
        for i in range(1, len(module_list), 2):
            if i < len(module_list):
                name, info = module_list[i]
                create_module_card(name, info, base_dir)
    
    # Create footer
    footer_html = """
    <div class="footer">
        <p>© 2025 SNT Health Analytics Dashboard | Version 1.0</p>
        <p>Last updated: May 21, 2025</p>
        <p>Developer: MS Kanu</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
