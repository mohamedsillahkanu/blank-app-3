import streamlit as st
import os
import sys
import types
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="SNT Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color theme
COLORS = {
    "primary": "#1E88E5",
    "secondary": "#90CAF9",
    "background": "#E3F2FD",
    "text": "#0D47A1",
    "accent": "#64B5F6"
}

# Custom CSS styling
def get_css():
    return f"""
    <style>
        .stApp {{
            background-color: {COLORS["background"]};
        }}
        h1, h2, h3 {{
            color: {COLORS["text"]};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .dashboard-title {{
            background-color: {COLORS["primary"]};
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
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
        .footer {{
            background-color: {COLORS["primary"]};
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-top: 30px;
            box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.1);
        }}
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

# Greeting message based on time of day
def get_greeting():
    current_hour = datetime.now().hour
    if current_hour < 12:
        return "Good Morning"
    elif current_hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"

# Initialize session state
if 'current_module' not in st.session_state:
    st.session_state.current_module = None

# Safe import to avoid st.set_page_config issues
def import_module_safely(module_path, module_name):
    """
    Import a module from file path while removing st.set_page_config and non-ASCII characters.
    """
    try:
        with open(module_path, 'r', encoding='utf-8') as file:
            source_code = file.read()

        modified_code = []
        skip_line = False
        inside_config = False

        for line in source_code.split('\n'):
            if "st.set_page_config" in line:
                skip_line = True
                inside_config = True
                continue
            if inside_config and ")" in line:
                skip_line = False
                inside_config = False
                continue
            if not skip_line:
                clean_line = line.encode('ascii', 'ignore').decode()
                modified_code.append(clean_line)

        module = types.ModuleType(module_name)
        module.__file__ = module_path
        sys.modules[module_name] = module
        exec('\n'.join(modified_code), module.__dict__)
        return module

    except Exception as e:
        st.error(f"Error loading module: {str(e)}")
        return None

# Create card UI for module
def create_module_card(name, info, base_dir):
    module_name = name.replace('.py', '').replace('_', ' ').title()
    card_html = f"""
    <div class="module-card">
        <h3>{module_name}</h3>
        <p>{info['desc']}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    module_file_path = os.path.join(base_dir, name)
    file_exists = os.path.exists(module_file_path)

    if not file_exists:
        st.warning(f"Module file not found: {module_file_path}")

    if st.button(f"Open {module_name}", key=f"btn_{name}", disabled=not file_exists):
        st.session_state.current_module = name
        st.rerun()

# Main dashboard logic
def main():
    st.markdown(get_css(), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="dashboard-title">
        <h1>SNT Dashboard</h1>
        <p>{get_greeting()} | {datetime.now().strftime("%A, %B %d, %Y")}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.current_module:
        if st.button("← Back to Dashboard", key="back_btn"):
            st.session_state.current_module = None
            st.rerun()

        try:
            module_name = st.session_state.current_module.replace('.py', '')
            base_dir = os.path.abspath(os.path.dirname(__file__))
            module_path = os.path.join(base_dir, st.session_state.current_module)

            st.markdown(f"<h2>{module_name.replace('_', ' ').title()}</h2>", unsafe_allow_html=True)

            module = import_module_safely(module_path, module_name)

            if module:
                if hasattr(module, 'run'):
                    module.run()
                elif hasattr(module, 'main'):
                    module.main()
                else:
                    st.warning(f"Module {module_name} has no run() or main() function.")
            else:
                st.error(f"Failed to load module: {st.session_state.current_module}")
            return
        except Exception as e:
            st.error(f"Error running module: {str(e)}")
            st.write(f"Details: {type(e).__name__}: {str(e)}")

    # Show cards
    st.markdown("<h2>Select a Section</h2>", unsafe_allow_html=True)

    modules = {
        "Data_assembly_and_management.py": {
            "desc": "Assemble datasets and manage data preprocessing workflows"
        },
        "Epidemiological_stratification.py": {
            "desc": "Analyze epidemiological data and identify patterns"
        },
        "Review_of_past_interventions.py": {
            "desc": "Evaluate the effectiveness of previous health interventions"
        },
        "Intervention_targeting.py": {
            "desc": "Plan and optimize new health intervention strategies"
        }
    }

    base_dir = os.path.abspath(os.path.dirname(__file__))
    col1, col2 = st.columns(2)
    module_list = list(modules.items())

    with col1:
        for i in range(0, len(module_list), 2):
            name, info = module_list[i]
            create_module_card(name, info, base_dir)

    with col2:
        for i in range(1, len(module_list), 2):
            name, info = module_list[i]
            create_module_card(name, info, base_dir)

    st.markdown("""
    <div class="footer">
        <p>© 2025 SNT Health Analytics Dashboard | Version 1.0</p>
        <p>Last updated: May 21, 2025</p>
        <p>Developer: MS Kanu</p>
    </div>
    """, unsafe_allow_html=True)

# Run app
if __name__ == "__main__":
    main()
