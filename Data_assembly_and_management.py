import streamlit as st
import importlib
import os
import sys
import types
import importlib.util
from datetime import datetime

# Set page configuration for the main dashboard
st.set_page_config(
    page_title="Data Assembly and Management",
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
        
        /* Error message styling */
        .error-box {{
            background-color: #ffebee;
            border: 1px solid #f44336;
            border-radius: 5px;
            padding: 10px;
            color: #c62828;
            margin: 10px 0;
        }}
        
        /* Warning message styling */
        .warning-box {{
            background-color: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 5px;
            padding: 10px;
            color: #ef6c00;
            margin: 10px 0;
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

# Function to handle rerun across different Streamlit versions
def safe_rerun():
    """Safely handle rerun for different Streamlit versions"""
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            # For very old versions, use session state manipulation
            st.session_state._rerun_trigger = not st.session_state.get('_rerun_trigger', False)

# Function to safely import module without set_page_config issues
def import_module_safely(module_path, module_name):
    """Import a module from file path while handling set_page_config"""
    try:
        # Check if file exists
        if not os.path.exists(module_path):
            st.error(f"Module file not found: {module_path}")
            return None
        
        # Read the module content
        with open(module_path, 'r', encoding='utf-8') as file:
            source_code = file.read()
        
        # Modify the source code to remove st.set_page_config call
        modified_code = []
        skip_line = False
        inside_config = False
        parentheses_count = 0
        
        for line in source_code.split('\n'):
            # Check for set_page_config
            if "st.set_page_config" in line:
                skip_line = True
                inside_config = True
                # Count parentheses to handle multi-line configs
                parentheses_count = line.count('(') - line.count(')')
                if parentheses_count <= 0:
                    inside_config = False
                    skip_line = False
                continue
            
            if inside_config:
                parentheses_count += line.count('(') - line.count(')')
                if parentheses_count <= 0:
                    inside_config = False
                    skip_line = False
                continue
            
            if not skip_line:
                modified_code.append(line)
        
        # Create a new module
        module = types.ModuleType(module_name)
        
        # Set the module's __file__ attribute
        module.__file__ = module_path
        
        # Add common imports to the module namespace
        module.__dict__.update({
            'st': st,
            'pd': None,  # Will be imported if needed
            'np': None,  # Will be imported if needed
            '__name__': module_name
        })
        
        # Try to import pandas and numpy if they're used in the module
        try:
            import pandas as pd
            module.__dict__['pd'] = pd
        except ImportError:
            pass
        
        try:
            import numpy as np
            module.__dict__['np'] = np
        except ImportError:
            pass
        
        # Execute the modified code in the module's namespace
        exec('\n'.join(modified_code), module.__dict__)
        
        return module
    
    except Exception as e:
        st.error(f"Error loading module '{module_name}': {str(e)}")
        with st.expander("Show detailed error"):
            st.code(f"Error Type: {type(e).__name__}\nError Message: {str(e)}")
        return None

# Function to create a card for each module
def create_module_card(name, info, base_dir):
    """Create a module card with error handling"""
    try:
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
            st.markdown(f"""
            <div class="warning-box">
                ⚠️ Module file not found: {name}
            </div>
            """, unsafe_allow_html=True)
        
        # Create button with unique key
        button_key = f"btn_{name}_{id(info)}"
        
        if st.button(f"Open {module_name}", 
                     key=button_key, 
                     disabled=not file_exists,
                     help=f"Launch {module_name} module" if file_exists else "Module file not available"):
            st.session_state.current_module = name
            safe_rerun()
    
    except Exception as e:
        st.markdown(f"""
        <div class="error-box">
            ❌ Error creating card for {name}: {str(e)}
        </div>
        """, unsafe_allow_html=True)

# Function to run a module safely
def run_module_safely(module_path, module_name):
    """Run a module with comprehensive error handling"""
    try:
        # Import the module safely
        module = import_module_safely(module_path, module_name)
        
        if not module:
            return False
        
        # Try different ways to execute the module
        execution_methods = [
            ('run', 'run()'),
            ('main', 'main()'),
            ('app', 'app()'),
            ('execute', 'execute()'),
        ]
        
        for method_name, method_desc in execution_methods:
            if hasattr(module, method_name):
                st.info(f"Executing {module_name} using {method_desc}")
                try:
                    getattr(module, method_name)()
                    return True
                except Exception as e:
                    st.error(f"Error executing {method_desc}: {str(e)}")
                    continue
        
        # If no execution method found, inform the user
        st.warning(f"Module '{module_name}' loaded but no standard execution method found.")
        st.info("The module code has been executed during import.")
        return True
        
    except Exception as e:
        st.error(f"Failed to run module '{module_name}': {str(e)}")
        with st.expander("Show technical details"):
            st.code(f"""
Error Type: {type(e).__name__}
Error Message: {str(e)}
Module Path: {module_path}
            """)
        return False

# Main function to run the dashboard
def main():
    try:
        # Apply custom CSS
        st.markdown(get_css(), unsafe_allow_html=True)
        
        # Create header
        header_html = f"""
        <div class="dashboard-title">
            <h1>🧊 Data Management and Assembly</h1>
            <p>{get_greeting()} | {datetime.now().strftime("%A, %B %d, %Y")}</p>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
        
        # If a module is selected, run it
        if st.session_state.current_module:
            # Add a back button
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.button("← Back to Dashboard", key="back_btn", type="secondary"):
                    st.session_state.current_module = None
                    safe_rerun()
            
            with col2:
                st.markdown(f"### {st.session_state.current_module.replace('.py', '').replace('_', ' ').title()}")
            
            st.markdown("---")
            
            try:
                # Get the correct file path
                base_dir = os.path.abspath(os.path.dirname(__file__))
                module_path = os.path.join(base_dir, st.session_state.current_module)
                module_name = st.session_state.current_module.replace('.py', '')
                
                # Run the module
                success = run_module_safely(module_path, module_name)
                
                if not success:
                    st.error("Failed to execute the module. Please check the module file and try again.")
                    if st.button("Return to Dashboard", key="error_return"):
                        st.session_state.current_module = None
                        safe_rerun()
                
            except Exception as e:
                st.error(f"Unexpected error running module: {str(e)}")
                st.markdown(f"""
                <div class="error-box">
                    <strong>Technical Details:</strong><br>
                    Error Type: {type(e).__name__}<br>
                    Error Message: {str(e)}
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Return to Dashboard", key="exception_return"):
                    st.session_state.current_module = None
                    safe_rerun()
            
            return
        
        # Show the main dashboard
        st.markdown("<h2>📋 Available Modules</h2>", unsafe_allow_html=True)
        
        # Define the modules with their descriptions and icons
        modules = {
            "Combine_files.py": {
                "icon": "🔗", 
                "desc": "Merge multiple datasets into unified data structure"
            },
            "Rename_columns.py": {
                "icon": "🏷️", 
                "desc": "Standardize and rename data columns for consistency"
            },
            "Create_new_variables.py": {
                "icon": "⚡", 
                "desc": "Generate derived variables and calculated fields"
            },
            "Outlier_detection_and_correction.py": {
                "icon": "🎯", 
                "desc": "Identify and handle data anomalies and outliers"
            }
        }
        
        # Get the correct base directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
        # Show module availability status
        st.markdown("#### Module Status")
        
        available_modules = 0
        for module_file in modules.keys():
            module_path = os.path.join(base_dir, module_file)
            if os.path.exists(module_path):
                available_modules += 1
        
        st.info(f"📊 {available_modules} out of {len(modules)} modules available")
        
        # Create 2 columns for module cards
        col1, col2 = st.columns(2)
        
        # Arrange modules in 2 columns
        module_list = list(modules.items())
        
        # First column
        with col1:
            for i in range(0, len(module_list), 2):
                if i < len(module_list):
                    name, info = module_list[i]
                    create_module_card(name, info, base_dir)
        
        # Second column
        with col2:
            for i in range(1, len(module_list), 2):
                if i < len(module_list):
                    name, info = module_list[i]
                    create_module_card(name, info, base_dir)
        
        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Show help section
        with st.expander("ℹ️ Help & Information"):
            st.markdown("""
            **How to use this dashboard:**
            
            1. **Select a Module**: Click on any module card to launch that tool
            2. **Navigate**: Use the back button to return to the main dashboard
            3. **Module Requirements**: Each module may require specific file formats
            4. **Error Handling**: If a module fails to load, check the error details
            
            **Module Descriptions:**
            - **Combine Files**: Merge multiple CSV/Excel files into one dataset
            - **Rename Columns**: Standardize column names across datasets
            - **Create New Variables**: Add calculated fields and derived variables
            - **Outlier Detection**: Find and handle anomalous data points
            
            **Technical Requirements:**
            - Python modules must be in the same directory as this dashboard
            - Supported file formats: CSV, XLSX, XLS
            - Internet connection required for some advanced features
            """)
        
        # Create footer
        footer_html = f"""
        <div class="footer">
            <p>© 2025 SNT Health Analytics Dashboard | Version 1.1</p>
            <p>Last updated: {datetime.now().strftime("%B %d, %Y")}</p>
            <p>Developer: MS Kanu</p>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)
    
    except Exception as e:
        st.error("Critical error in main dashboard")
        st.markdown(f"""
        <div class="error-box">
            <strong>Critical Error Details:</strong><br>
            Error Type: {type(e).__name__}<br>
            Error Message: {str(e)}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
