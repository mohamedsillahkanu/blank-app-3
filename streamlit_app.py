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

# Function to safely import module without set_page_config issues
def import_module_safely(module_path, module_name):
    """Import a module from file path while handling set_page_config"""
    try:
        # Read the module content
        with open(module_path, 'r') as file:
            source_code = file.read()
        
        # Modify the source code to remove st.set_page_config call
        modified_code = []
        skip_line = False
        inside_config = False
        
        for line in source_code.split('\n'):
            if "st.set_page_config" in line:
                skip_line = True
                inside_config = True
                continue
            
            if inside_config:
                if ")" in line:
                    inside_config = False
                    skip_line = False
                    continue
            
            if not skip_line:
                modified_code.append(line)
        
        # Create a new module
        module = types.ModuleType(module_name)
        
        # Set the module's __file__ attribute
        module.__file__ = module_path
        
        # Add the module to sys.modules
        sys.modules[module_name] = module
        
        # Execute the modified code in the module's namespace
        exec('\n'.join(modified_code), module.__dict__)
        
        return module
    
    except Exception as e:
        st.error(f"Error loading module: {str(e)}")
        return None

# Function to create a card for each module
def create_module_card(name, info, pages_dir):
    module_name = name.replace('.py', '').replace('_', ' ').title()
    
    card_html = f"""
    <div class="module-card">
        <h3><span class="module-icon">{info['icon']}</span>{module_name}</h3>
        <p>{info['desc']}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Check if the module file exists
    module_file_path = os.path.join(pages_dir, name)
    file_exists = os.path.exists(module_file_path)
    
    if not file_exists:
        st.warning(f"Module file not found: {module_file_path}")
    
    if st.button(f"Open {module_name}", 
                 key=f"btn_{name}", 
                 disabled=not file_exists):
        st.session_state.current_module = name
        st.experimental_rerun()

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
        # Add a back button with custom styling
        back_button_html = """
        <button class="back-button" id="back-btn">← Back to Dashboard</button>
        <script>
            document.getElementById("back-btn").addEventListener("click", function() {
                window.location.href = window.location.pathname;
            });
        </script>
        """
        st.markdown(back_button_html, unsafe_allow_html=True)
        
        if st.button("← Back", key="std_back_btn"):
            st.session_state.current_module = None
            st.experimental_rerun()
        
        try:
            # Extract module name without .py extension
            module_name = st.session_state.current_module.replace('.py', '')
            
            # Get the module path
            base_dir = os.path.abspath(os.path.dirname(__file__))
            pages_dir = os.path.join(base_dir, "pages")
            module_path = os.path.join(pages_dir, st.session_state.current_module)
            
            # Display module title
            st.markdown(f"<h2>{module_name.replace('_', ' ').title()}</h2>", unsafe_allow_html=True)
            
            # Import the module safely (without set_page_config issues)
            module = import_module_safely(module_path, module_name)
            
            if module:
                # Try to run the module
                # First, try to call the run() function if it exists
                if hasattr(module, 'run'):
                    module.run()
                # If not, try to find a main() function
                elif hasattr(module, 'main'):
                    module.main()
                # If none of those work, we'll assume the module has already executed its code
                else:
                    st.warning(f"Module {module_name} doesn't have a run() or main() function, but its code has been executed.")
            else:
                st.error(f"Failed to load module: {st.session_state.current_module}")
            
            return
        except Exception as e:
            st.error(f"Error running module: {str(e)}")
            st.write(f"Details: {type(e).__name__}: {str(e)}")
    
    # Otherwise, show the main dashboard with the modules in 2 columns and 3 rows
    st.markdown("<h2>Select a Section</h2>", unsafe_allow_html=True)
    
    # Define the modules with their descriptions and icons
    modules = {
        "Data_assembly_and_management.py": {"icon": "", "desc": "Assemble datasets and manage data preprocessing workflows"},
        "Epidemiological_stratification.py": {"icon": "", "desc": "Analyze epidemiological data and identify patterns"},
        "Review_of_past_interventions.py": {"icon": "", "desc": "Evaluate the effectiveness of previous health interventions"},
        "Intervention_targeting.py": {"icon": "", "desc": "Plan and optimize new health intervention strategies"},
    }
    
    # Get the correct pages directory path
    base_dir = os.path.abspath(os.path.dirname(__file__))

    
    # Create 2 columns
    col1, col2 = st.columns(2)
    
    # Arrange modules in 2 columns and 3 rows
    module_list = list(modules.items())
    
    # First column - 3 modules
    with col1:
        for i in range(0, len(module_list), 2):
            if i < len(module_list):
                name, info = module_list[i]
                create_module_card(name, info, base_dir)
    
    # Second column - 3 modules
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
