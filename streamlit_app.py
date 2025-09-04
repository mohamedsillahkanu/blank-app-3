import streamlit as st
import importlib
import os
import sys
import types
import importlib.util
import pandas as pd
from datetime import datetime
import json
import base64
import gc

# Try to import psutil for memory monitoring (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Set page configuration for the main dashboard
st.set_page_config(
    page_title="SNT Automation",
    page_icon="📊",
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

# Memory cleanup function
def clear_memory():
    """Clear memory by removing cached data and running garbage collection"""
    try:
        # Clear Streamlit cache
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Clear pandas cache if any
        if hasattr(pd, '_cache'):
            pd._cache.clear()
        
        # Remove large variables from session state
        keys_to_remove = []
        for key in st.session_state:
            if key.startswith('data_') or key.startswith('df_') or key.startswith('result_'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Force garbage collection
        gc.collect()
        
        # Clear any matplotlib figures if imported
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except ImportError:
            pass
        
        return True
    except Exception as e:
        st.error(f"Memory cleanup error: {str(e)}")
        return False

# Memory warning and auto-cleanup function
def check_memory_and_warn():
    """Check memory usage and warn/cleanup if necessary"""
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            
            # Determine warning level and actions
            if memory_percent >= 90:
                st.error("🚨 CRITICAL: Memory usage at {:.1f}%! Auto-cleaning to prevent app crash...".format(memory_percent))
                clear_memory()
                st.success("✅ Emergency cleanup completed. Please save your work!")
                return "critical"
            elif memory_percent >= 75:
                st.warning("⚠️ HIGH: Memory usage at {:.1f}%! Consider clearing memory soon.".format(memory_percent))
                return "high"
            elif memory_percent >= 60:
                st.info("💡 MODERATE: Memory usage at {:.1f}%. Monitor usage closely.".format(memory_percent))
                return "moderate"
            else:
                return "normal"
                
        except Exception as e:
            st.error(f"Memory monitoring error: {str(e)}")
            return "error"
    else:
        # Fallback: Check session state size
        try:
            total_size = sum(sys.getsizeof(v) for v in st.session_state.values())
            size_mb = total_size / (1024 * 1024)
            
            if size_mb > 100:  # 100MB threshold for session state
                st.warning(f"⚠️ Large session data: {size_mb:.1f}MB. Consider clearing memory.")
                return "high"
            elif size_mb > 50:
                st.info(f"💡 Session data: {size_mb:.1f}MB. Monitor usage.")
                return "moderate"
            else:
                return "normal"
        except:
            return "normal"

# Enhanced button with auto cleanup
def cleanup_button(label, key=None, **kwargs):
    """Custom button that automatically cleans memory when clicked"""
    button_clicked = st.button(label, key=key, **kwargs)
    if button_clicked:
        clear_memory()
    return button_clicked

# Function to encode image to base64
def get_image_base64(image_path):
    """Convert image to base64 string for embedding in HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path}")
        return None
    except Exception as e:
        st.error(f"Error loading image {image_path}: {str(e)}")
        return None

# CSS for styling the dashboard
def get_css():
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {COLORS["background"]};
            background: linear-gradient(135deg, {COLORS["background"]} 0%, {COLORS["primary"]} 100%);
            min-height: 100vh;
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {COLORS["text"]};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        /* Dashboard title styling with images */
        .dashboard-title {{
            background-color: {COLORS["primary"]};
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .header-content {{
            flex: 1;
            text-align: center;
        }}
        
        .header-image {{
            max-height: 180px;
            max-width: 180px;
            object-fit: contain;
            margin: 0 20px;
        }}
        
        .header-image-left {{
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
        }}
        
        .header-image-right {{
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
        }}
        
        /* Responsive header for smaller screens */
        @media (max-width: 768px) {{
            .dashboard-title {{
                flex-direction: column;
                position: static;
            }}
            
            .header-image-left,
            .header-image-right {{
                position: static;
                transform: none;
                margin: 10px 0;
            }}
            
            .header-content {{
                order: 2;
            }}
            
            .header-image-left {{
                order: 1;
            }}
            
            .header-image-right {{
                order: 3;
            }}
        }}
        
        /* Module cards */
        .module-card {{
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid {COLORS["accent"]};
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .module-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }}
        
        /* Sub-module cards with different styling */
        .sub-module-card {{
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid {COLORS["accent"]};
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .sub-module-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        
        /* Icons in module cards */
        .module-icon {{
            font-size: 24px;
            margin-right: 10px;
        }}
        
        .sub-module-icon {{
            font-size: 20px;
            margin-right: 8px;
        }}
        
        /* Breadcrumb navigation */
        .breadcrumb {{
            background-color: {COLORS["secondary"]};
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: {COLORS["text"]};
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
        
        /* Sub-module button styling */
        .sub-module-button {{
            background-color: {COLORS["accent"]} !important;
        }}
        
        .sub-module-button:hover {{
            background-color: {COLORS["secondary"]} !important;
        }}
        
        /* Memory management in header */
        .memory-management {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .memory-info {{
            color: {COLORS["text"]};
            font-weight: bold;
            font-size: 14px;
        }}
        
        .memory-button {{
            background-color: {COLORS["accent"]} !important;
            color: white !important;
            border: none !important;
            padding: 5px 12px !important;
            border-radius: 5px !important;
            font-size: 12px !important;
            cursor: pointer !important;
            width: auto !important;
        }}
        
        .memory-button:hover {{
            background-color: {COLORS["secondary"]} !important;
        }}
        
        /* Memory warning styles */
        .memory-critical {{
            background-color: #ff4444 !important;
            color: white !important;
            font-weight: bold !important;
            animation: pulse 1s infinite !important;
        }}
        
        .memory-high {{
            background-color: #ff8800 !important;
            color: white !important;
            font-weight: bold !important;
        }}
        
        .memory-moderate {{
            background-color: #4CAF50 !important;
            color: white !important;
        }}
        
        .memory-normal {{
            background-color: {COLORS["accent"]} !important;
            color: white !important;
        }}
        
        /* Responsive memory management */
        @media (max-width: 768px) {{
            .memory-management {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
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

# Function to get memory usage
def get_memory_usage():
    """Get current memory usage percentage"""
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            return memory_percent, f"RAM: {memory_percent:.1f}%"
        except:
            return 0, "RAM: N/A"
    else:
        # Alternative method using sys.getsizeof for session state
        try:
            total_size = sum(sys.getsizeof(v) for v in st.session_state.values())
            size_mb = total_size / (1024 * 1024)
            return size_mb, f"Session: {size_mb:.1f}MB"
        except:
            return 0, "Memory: OK"

# Function to get memory status class for styling
def get_memory_status_class():
    """Get CSS class based on memory usage level"""
    if PSUTIL_AVAILABLE:
        try:
            memory_percent = psutil.Process().memory_percent()
            if memory_percent >= 90:
                return "memory-critical"
            elif memory_percent >= 75:
                return "memory-high"
            elif memory_percent >= 60:
                return "memory-moderate"
            else:
                return "memory-normal"
        except:
            return "memory-normal"
    else:
        try:
            total_size = sum(sys.getsizeof(v) for v in st.session_state.values())
            size_mb = total_size / (1024 * 1024)
            if size_mb > 100:
                return "memory-high"
            elif size_mb > 50:
                return "memory-moderate"
            else:
                return "memory-normal"
        except:
            return "memory-normal"

# Function to create header with images and memory management
def create_header_with_images():
    """Create the dashboard header with left and right images and memory management"""
    # Get the base directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Image paths
    nmcp_path = os.path.join(base_dir, "NMCP.png")
    icf_path = os.path.join(base_dir, "ICF-SL.jpg")
    
    # Get base64 encoded images
    nmcp_base64 = get_image_base64(nmcp_path)
    icf_base64 = get_image_base64(icf_path)
    
    # Create header HTML with images
    nmcp_img = f'<img src="data:image/png;base64,{nmcp_base64}" class="header-image header-image-left" alt="NMCP Logo">' if nmcp_base64 else ''
    icf_img = f'<img src="data:image/png;base64,{icf_base64}" class="header-image header-image-right" alt="ICF Logo">' if icf_base64 else ''
    
    header_html = f"""
    <div class="dashboard-title">
        {nmcp_img}
        <div class="header-content">
            <h1>📊 Data Management and Analysis Tool</h1>
            <p>{get_greeting()} | {datetime.now().strftime("%A, %B %d, %Y")}</p>
        </div>
        {icf_img}
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Check memory and show warnings
    warning_level = check_memory_and_warn()
    
    # Add memory management section below header
    memory_percent, memory_display = get_memory_usage()
    memory_class = get_memory_status_class()
    
    # Determine status message based on warning level
    status_messages = {
        "critical": "🚨 CRITICAL - Auto-cleaning active",
        "high": "⚠️ HIGH - Clean memory soon", 
        "moderate": "💡 MODERATE - Monitor closely",
        "normal": "✅ NORMAL - Auto-cleanup active",
        "error": "❌ ERROR - Monitor manually"
    }
    
    status_message = status_messages.get(warning_level, "✅ Auto-cleanup active")
    
    memory_html = f"""
    <div class="memory-management {memory_class}">
        <div class="memory-info">
            🧠 Memory Usage: {memory_display} | {status_message}
        </div>
    </div>
    """
    
    st.markdown(memory_html, unsafe_allow_html=True)
    
    # Add memory management controls
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col2:
        # Change button color based on memory status
        button_help = "Clear memory immediately - protects all users from app crashes"
        if warning_level in ["critical", "high"]:
            button_help = "🚨 URGENT: Clear memory now to prevent app crash!"
            
        if st.button("🗑️ Clear Now", key="header_manual_cleanup", help=button_help):
            if clear_memory():
                st.success("✅ Memory cleared! All users protected.")
                st.rerun()
            else:
                st.error("❌ Cleanup failed! Try again.")
    
    with col3:
        if st.button("🔄 Refresh", key="header_refresh", help="Refresh memory status and warnings"):
            st.rerun()

# Initialize session state for module navigation
if 'current_module' not in st.session_state:
    st.session_state.current_module = None
if 'current_sub_module' not in st.session_state:
    st.session_state.current_sub_module = None
if 'navigation_stack' not in st.session_state:
    st.session_state.navigation_stack = []

# Function to safely import module without set_page_config issues
def import_module_safely(module_path, module_name):
    """Import a module from file path while handling set_page_config"""
    try:
        # Clear memory before importing new module
        clear_memory()
        
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

# Function to get sub-modules for a main module
def get_sub_modules(main_module_name, base_dir):
    """Get list of sub-modules for a main module"""
    # Remove .py extension from main module name
    main_name = main_module_name.replace('.py', '')

    # Look for a folder with the same name as the main module
    sub_module_dir = os.path.join(base_dir, main_name)

    if not os.path.exists(sub_module_dir):
        return []

    # Get all .py files in the sub-module directory
    sub_modules = []
    for file in os.listdir(sub_module_dir):
        if file.endswith('.py') and file != '__init__.py':
            sub_modules.append(file)

    return sub_modules

# Function to create a card for each module
def create_module_card(name, info, base_dir, is_sub_module=False):
    module_name = name.replace('.py', '').replace('_', ' ').title()

    card_class = "sub-module-card" if is_sub_module else "module-card"
    icon_class = "sub-module-icon" if is_sub_module else "module-icon"

    card_html = f"""
    <div class="{card_class}">
        <h3><span class="{icon_class}">{info['icon']}</span>{module_name}</h3>
        <p>{info['desc']}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

    # Check if the module file exists
    if is_sub_module:
        # For sub-modules, look in the main module's subdirectory
        main_module_dir = st.session_state.current_module.replace('.py', '')
        module_file_path = os.path.join(base_dir, main_module_dir, name)
    else:
        module_file_path = os.path.join(base_dir, name)

    file_exists = os.path.exists(module_file_path)

    if not file_exists:
        st.warning(f"Module file not found: {module_file_path}")

    button_key = f"btn_sub_{name}" if is_sub_module else f"btn_{name}"
    button_class = "sub-module-button" if is_sub_module else ""

    # Use cleanup_button instead of regular st.button
    if cleanup_button(f"Open {module_name}", 
                     key=button_key, 
                     disabled=not file_exists):
        if is_sub_module:
            st.session_state.current_sub_module = name
        else:
            st.session_state.current_module = name
            st.session_state.current_sub_module = None
        st.rerun()

# Function to create breadcrumb navigation
def create_breadcrumb():
    breadcrumb_parts = ["🏠 Dashboard"]

    if st.session_state.current_module:
        module_name = st.session_state.current_module.replace('.py', '').replace('_', ' ').title()
        breadcrumb_parts.append(f"📁 {module_name}")

    if st.session_state.current_sub_module:
        sub_module_name = st.session_state.current_sub_module.replace('.py', '').replace('_', ' ').title()
        breadcrumb_parts.append(f"📄 {sub_module_name}")

    breadcrumb_html = f"""
    <div class="breadcrumb">
        {' > '.join(breadcrumb_parts)}
    </div>
    """
    st.markdown(breadcrumb_html, unsafe_allow_html=True)

# Function to run a specific module
def run_module(module_path, module_name):
    """Run a specific module"""
    try:
        # Import the module safely
        module = import_module_safely(module_path, module_name)
        
        if module:
            # Try to run the module
            if hasattr(module, 'run'):
                module.run()
            elif hasattr(module, 'main'):
                module.main()
            else:
                st.info(f"Module {module_name} has been loaded successfully.")
                
            # Clear memory after module execution
            clear_memory()
        else:
            st.error(f"Failed to load module: {module_name}")
    except Exception as e:
        st.error(f"Error running module: {str(e)}")
        st.write(f"Details: {type(e).__name__}: {str(e)}")
        # Clear memory even on error
        clear_memory()

# Main function to run the dashboard
def main():
    # Apply custom CSS
    st.markdown(get_css(), unsafe_allow_html=True)

    # Create header with images and memory management
    create_header_with_images()

    # Show breadcrumb navigation
    create_breadcrumb()

    # Get the main directory path
    base_dir = os.path.abspath(os.path.dirname(__file__))

    # If a sub-module is selected, run it
    if st.session_state.current_sub_module and st.session_state.current_module:
        # Add back buttons with cleanup
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if cleanup_button("← Back to Module", key="back_to_module"):
                st.session_state.current_sub_module = None
                st.rerun()
        with col2:
            if cleanup_button("← Back to Dashboard", key="back_to_dashboard"):
                st.session_state.current_module = None
                st.session_state.current_sub_module = None
                st.rerun()
        
        # Run the sub-module
        main_module_dir = st.session_state.current_module.replace('.py', '')
        sub_module_path = os.path.join(base_dir, main_module_dir, st.session_state.current_sub_module)
        sub_module_name = st.session_state.current_sub_module.replace('.py', '')
        
        st.markdown(f"<h2>{sub_module_name.replace('_', ' ').title()}</h2>", unsafe_allow_html=True)
        run_module(sub_module_path, sub_module_name)
        return

    # If a main module is selected, show its sub-modules
    if st.session_state.current_module:
        # Add a back button with cleanup
        if cleanup_button("← Back to Dashboard", key="main_back_btn"):
            st.session_state.current_module = None
            st.rerun()

        # Check if this module has sub-modules
        sub_modules = get_sub_modules(st.session_state.current_module, base_dir)

        if sub_modules:
            # Show sub-modules in the same layout style
            st.markdown(f"<h2>Select a Sub-Module</h2>", unsafe_allow_html=True)

            # Define sub-module information (you can customize this)
            sub_module_info = {
                # You can define specific info for sub-modules here
                # For now, we'll use generic info
            }

            # Create 2 columns for sub-modules
            col1, col2 = st.columns(2)

            # Arrange sub-modules in 2 columns
            for i, sub_module in enumerate(sub_modules):
                # Generic info for sub-modules (you can customize this)
                info = sub_module_info.get(sub_module, {
                    "icon": "📄", 
                    "desc": f"Sub-module for {sub_module.replace('.py', '').replace('_', ' ')}"
                })
                
                if i % 2 == 0:
                    with col1:
                        create_module_card(sub_module, info, base_dir, is_sub_module=True)
                else:
                    with col2:
                        create_module_card(sub_module, info, base_dir, is_sub_module=True)
        else:
            # No sub-modules, run the main module directly
            module_path = os.path.join(base_dir, st.session_state.current_module)
            module_name = st.session_state.current_module.replace('.py', '')

            st.markdown(f"<h2>{module_name.replace('_', ' ').title()}</h2>", unsafe_allow_html=True)
            run_module(module_path, module_name)

        return
    
    # Show the main dashboard with the modules
    st.markdown("<h2>Select a Data Analysis Module</h2>", unsafe_allow_html=True)

    # Define the main modules with their descriptions and icons
    modules = {
        "Data_assembly_and_management.py": {
            "icon": "🗂️", 
            "desc": "Assemble datasets and manage data preprocessing workflows"
        },
        "Epidemiological_stratification.py": {
            "icon": "📊", 
            "desc": "Analyze epidemiological data and identify patterns"
        },
        "Review_of_past_interventions.py": {
            "icon": "📈", 
            "desc": "Evaluate the effectiveness of previous health interventions"
        },
        "Intervention_targeting.py": {
            "icon": "🎯", 
            "desc": "Plan and optimize new health intervention strategies"
        }
    }

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
        <p>© 2025 Data Management and Analysis Tool | Version 1.0</p>
        <p>Last updated: May 21, 2025</p>
        <p>Developer: MS Kanu</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
