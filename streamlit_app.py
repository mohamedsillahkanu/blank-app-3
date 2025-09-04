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

# CSS for styling the dashboard with improved responsiveness
def get_css():
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {COLORS["background"]};
            background: linear-gradient(135deg, {COLORS["background"]} 0%, {COLORS["primary"]} 100%);
            min-height: 100vh;
        }}
        
        /* Container for main content */
        .main-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 10px;
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {COLORS["text"]};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        /* Improved responsive dashboard title styling */
        .dashboard-title {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["accent"]} 100%);
            padding: 15px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}
        
        .header-content {{
            margin: 0 auto;
            max-width: 100%;
        }}
        
        .header-content h1 {{
            color: white;
            margin: 10px 0;
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: bold;
        }}
        
        .header-content p {{
            color: rgba(255, 255, 255, 0.9);
            margin: 5px 0;
            font-size: clamp(0.9rem, 2vw, 1.1rem);
        }}
        
        .header-images {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}
        
        .header-image {{
            max-height: 80px;
            max-width: 120px;
            height: auto;
            width: auto;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            background: white;
            padding: 5px;
        }}
        
        /* Mobile-first responsive design */
        @media (max-width: 768px) {{
            .dashboard-title {{
                padding: 10px;
                margin-bottom: 15px;
            }}
            
            .header-images {{
                gap: 10px;
                margin: 10px 0;
            }}
            
            .header-image {{
                max-height: 60px;
                max-width: 100px;
            }}
            
            .header-content h1 {{
                font-size: 1.5rem;
            }}
            
            .header-content p {{
                font-size: 0.9rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .header-image {{
                max-height: 50px;
                max-width: 80px;
            }}
            
            .header-content h1 {{
                font-size: 1.3rem;
            }}
            
            .header-content p {{
                font-size: 0.8rem;
            }}
        }}
        
        /* Responsive module cards */
        .module-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid {COLORS["accent"]};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .module-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }}
        
        .module-card h3 {{
            margin: 0 0 10px 0;
            color: {COLORS["text"]};
            font-size: clamp(1.1rem, 2.5vw, 1.3rem);
            line-height: 1.4;
        }}
        
        .module-card p {{
            margin: 0;
            color: #666;
            font-size: clamp(0.9rem, 2vw, 1rem);
            line-height: 1.5;
        }}
        
        /* Sub-module cards with improved responsiveness */
        .sub-module-card {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid {COLORS["accent"]};
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .sub-module-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        }}
        
        .sub-module-card h3 {{
            margin: 0 0 8px 0;
            color: {COLORS["text"]};
            font-size: clamp(1rem, 2.2vw, 1.2rem);
            line-height: 1.3;
        }}
        
        .sub-module-card p {{
            margin: 0;
            color: #666;
            font-size: clamp(0.85rem, 1.8vw, 0.95rem);
            line-height: 1.4;
        }}
        
        /* Responsive icons */
        .module-icon {{
            font-size: clamp(1.2rem, 3vw, 1.5rem);
            margin-right: 8px;
            display: inline-block;
        }}
        
        .sub-module-icon {{
            font-size: clamp(1rem, 2.5vw, 1.3rem);
            margin-right: 6px;
            display: inline-block;
        }}
        
        /* Responsive breadcrumb navigation */
        .breadcrumb {{
            background-color: {COLORS["secondary"]};
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: {COLORS["text"]};
            font-size: clamp(0.85rem, 2vw, 1rem);
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        /* Responsive footer */
        .footer {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["text"]} 100%);
            padding: 20px 15px;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-top: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .footer p {{
            margin: 5px 0;
            font-size: clamp(0.8rem, 1.8vw, 0.95rem);
        }}
        
        /* Responsive button styling */
        .stButton>button {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["accent"]} 100%);
            color: white;
            border-radius: 8px;
            border: none;
            padding: 12px 20px;
            width: 100%;
            font-weight: bold;
            font-size: clamp(0.9rem, 2vw, 1rem);
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .stButton>button:hover {{
            background: linear-gradient(135deg, {COLORS["text"]} 0%, {COLORS["primary"]} 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        
        /* Responsive memory management */
        .memory-management {{
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 15px;
            border-radius: 10px;
            margin: 15px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .memory-info {{
            color: {COLORS["text"]};
            font-weight: bold;
            font-size: clamp(0.8rem, 1.8vw, 0.9rem);
            flex: 1;
            min-width: 200px;
        }}
        
        .memory-controls {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .memory-button {{
            background: linear-gradient(135deg, {COLORS["accent"]} 0%, {COLORS["primary"]} 100%) !important;
            color: white !important;
            border: none !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            font-size: clamp(0.75rem, 1.5vw, 0.85rem) !important;
            cursor: pointer !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            min-width: 80px;
        }}
        
        .memory-button:hover {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["text"]} 100%) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Memory status colors */
        .memory-critical {{
            background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%) !important;
            animation: pulse 1.5s infinite !important;
        }}
        
        .memory-high {{
            background: linear-gradient(135deg, #ff8800 0%, #e65100 100%) !important;
        }}
        
        .memory-moderate {{
            background: linear-gradient(135deg, #4CAF50 0%, #2e7d32 100%) !important;
        }}
        
        .memory-normal {{
            background: linear-gradient(135deg, {COLORS["accent"]} 0%, {COLORS["primary"]} 100%) !important;
        }}
        
        /* Pulse animation for critical memory */
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
        
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {{
            .main-container {{
                padding: 5px;
            }}
            
            .memory-management {{
                flex-direction: column;
                text-align: center;
                padding: 10px;
            }}
            
            .memory-info {{
                text-align: center;
                min-width: auto;
            }}
            
            .memory-controls {{
                justify-content: center;
                width: 100%;
            }}
            
            .module-card, .sub-module-card {{
                margin-bottom: 12px;
                padding: 15px;
            }}
            
            .footer {{
                margin-top: 20px;
                padding: 15px 10px;
            }}
        }}
        
        @media (max-width: 480px) {{
            .memory-management {{
                padding: 8px;
                margin: 10px 0;
            }}
            
            .memory-button {{
                padding: 6px 10px !important;
                min-width: 70px;
            }}
            
            .module-card {{
                padding: 12px;
            }}
            
            .sub-module-card {{
                padding: 10px;
            }}
        }}
        
        /* Improved column responsiveness */
        @media (max-width: 768px) {{
            .stColumn {{
                padding: 0 5px;
            }}
        }}
        
        /* Custom scrollbar for better mobile experience */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {COLORS["background"]};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {COLORS["accent"]};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS["primary"]};
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

# Improved function to create header with better responsiveness
def create_header_with_images():
    """Create the dashboard header with responsive images and memory management"""
    # Get the base directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Image paths
    nmcp_path = os.path.join(base_dir, "NMCP.png")
    icf_path = os.path.join(base_dir, "ICF-SL.jpg")
    
    # Get base64 encoded images
    nmcp_base64 = get_image_base64(nmcp_path)
    icf_base64 = get_image_base64(icf_path)
    
    # Create responsive header HTML
    images_html = ""
    if nmcp_base64 or icf_base64:
        images_html = '<div class="header-images">'
        if nmcp_base64:
            images_html += f'<img src="data:image/png;base64,{nmcp_base64}" class="header-image" alt="NMCP Logo">'
        if icf_base64:
            images_html += f'<img src="data:image/jpeg;base64,{icf_base64}" class="header-image" alt="ICF Logo">'
        images_html += '</div>'
    
    header_html = f"""
    <div class="main-container">
        <div class="dashboard-title">
            <div class="header-content">
                <h1>📊 Data Management and Analysis Tool</h1>
                <p>{get_greeting()} | {datetime.now().strftime("%A, %B %d, %Y")}</p>
                {images_html}
            </div>
        </div>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Check memory and show warnings
    warning_level = check_memory_and_warn()
    
    # Add responsive memory management section
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
    
    # Create responsive memory management with Streamlit columns
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        memory_html = f"""
        <div class="memory-info {memory_class}">
            🧠 {memory_display} | {status_message}
        </div>
        """
        st.markdown(memory_html, unsafe_allow_html=True)
    
    with col2:
        # Change button color based on memory status
        button_help = "Clear memory immediately - protects all users from app crashes"
        if warning_level in ["critical", "high"]:
            button_help = "🚨 URGENT: Clear memory now to prevent app crash!"
            
        if st.button("🗑️ Clear", key="header_manual_cleanup", help=button_help):
            if clear_memory():
                st.success("✅ Memory cleared!")
                st.rerun()
            else:
                st.error("❌ Cleanup failed!")
    
    with col3:
        if st.button("🔄 Refresh", key="header_refresh", help="Refresh memory status"):
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

# Function to create a responsive card for each module
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

# Function to create responsive breadcrumb navigation
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

    # Wrap main content in container for better responsive behavior
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Show breadcrumb navigation
    create_breadcrumb()

    # Get the main directory path
    base_dir = os.path.abspath(os.path.dirname(__file__))

    # If a sub-module is selected, run it
    if st.session_state.current_sub_module and st.session_state.current_module:
        # Add responsive back buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if cleanup_button("← Module", key="back_to_module"):
                st.session_state.current_sub_module = None
                st.rerun()
        with col2:
            if cleanup_button("← Dashboard", key="back_to_dashboard"):
                st.session_state.current_module = None
                st.session_state.current_sub_module = None
                st.rerun()
        
        # Run the sub-module
        main_module_dir = st.session_state.current_module.replace('.py', '')
        sub_module_path = os.path.join(base_dir, main_module_dir, st.session_state.current_sub_module)
        sub_module_name = st.session_state.current_sub_module.replace('.py', '')
        
        st.markdown(f"<h2>{sub_module_name.replace('_', ' ').title()}</h2>", unsafe_allow_html=True)
        run_module(sub_module_path, sub_module_name)
        
        # Close container
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # If a main module is selected, show its sub-modules
    if st.session_state.current_module:
        # Add a responsive back button
        col1, col2 = st.columns([1, 5])
        with col1:
            if cleanup_button("← Dashboard", key="main_back_btn"):
                st.session_state.current_module = None
                st.rerun()

        # Check if this module has sub-modules
        sub_modules = get_sub_modules(st.session_state.current_module, base_dir)

        if sub_modules:
            # Show sub-modules with responsive layout
            st.markdown(f"<h2>Select a Sub-Module</h2>", unsafe_allow_html=True)

            # Define sub-module information (you can customize this)
            sub_module_info = {
                # You can define specific info for sub-modules here
                # For now, we'll use generic info
            }

            # Create responsive columns for sub-modules
            if len(sub_modules) == 1:
                # Single column for one sub-module
                col1 = st.columns(1)[0]
                with col1:
                    info = sub_module_info.get(sub_modules[0], {
                        "icon": "📄", 
                        "desc": f"Sub-module for {sub_modules[0].replace('.py', '').replace('_', ' ')}"
                    })
                    create_module_card(sub_modules[0], info, base_dir, is_sub_module=True)
            else:
                # Two columns for multiple sub-modules
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

        # Close container
        st.markdown('</div>', unsafe_allow_html=True)
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

    # Create responsive layout for modules
    module_list = list(modules.items())
    
    # Determine layout based on number of modules
    if len(module_list) <= 2:
        # Single column or two modules in one row
        if len(module_list) == 1:
            col1 = st.columns(1)[0]
            with col1:
                name, info = module_list[0]
                create_module_card(name, info, base_dir)
        else:
            col1, col2 = st.columns(2)
            with col1:
                name, info = module_list[0]
                create_module_card(name, info, base_dir)
            with col2:
                name, info = module_list[1]
                create_module_card(name, info, base_dir)
    else:
        # Multiple modules - use 2 columns
        col1, col2 = st.columns(2)

        # Arrange modules in 2 columns
        for i, (name, info) in enumerate(module_list):
            if i % 2 == 0:
                with col1:
                    create_module_card(name, info, base_dir)
            else:
                with col2:
                    create_module_card(name, info, base_dir)
    
    # Create responsive footer
    footer_html = """
    <div class="footer">
        <p>© 2025 Data Management and Analysis Tool | Version 1.0</p>
        <p>Last updated: May 21, 2025</p>
        <p>Developer: MS Kanu</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
    
    # Close main container
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
