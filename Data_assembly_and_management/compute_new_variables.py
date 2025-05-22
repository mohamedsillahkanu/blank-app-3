import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
from typing import List, Dict, Tuple

# Set page config
st.set_page_config(
    page_title="Create New Variables Tool",
    page_icon="🧮",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .operation-card {
        background-color: white;
        color: black;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .operation-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #FF6B35;
    }
    
    .operation-badge {
        display: inline-block;
        background-color: #FF6B35;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin-right: 1rem;
    }
    
    .operation-badge.subtraction {
        background-color: #E74C3C;
    }
    
    .variable-input-row {
        display: flex;
        align-items: center;
        margin: 1rem 0;
        gap: 1rem;
    }
    
    .variable-input-left,
    .variable-input-right {
        flex: 1;
    }
    
    .input-label {
        background-color: #f8f9fa;
        color: black;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border: 1px solid #ddd;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    
    .upload-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #FF6B35;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stats-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 3px solid #FF6B35;
    }
    
    .result-summary {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
    
    .formula-display {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        font-family: monospace;
        margin: 0.5rem 0;
    }
    
    .stSelectbox > div > div > div {
        background-color: white !important;
        color: black !important;
    }
    
    .stTextInput > div > div > input {
        background-color: white !important;
        color: black !important;
    }
    
    .stMultiSelect > div > div > div {
        background-color: white !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🧮 Create New Variables Tool</h1>
    <p>Create new calculated variables using addition and subtraction operations</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'computed_df' not in st.session_state:
    st.session_state.computed_df = None
if 'operations' not in st.session_state:
    st.session_state.operations = []
if 'variables_created' not in st.session_state:
    st.session_state.variables_created = False

def read_file(uploaded_file):
    """Read uploaded file and return DataFrame"""
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return df
    except Exception as e:
        st.error(f"Error reading file {uploaded_file.name}: {str(e)}")
        return None

def get_numeric_columns(df):
    """Get only numeric columns from the dataframe"""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def validate_operations(operations: List[Dict], df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Validate all operations and return errors and warnings"""
    errors = []
    warnings = []
    
    if not operations:
        errors.append("No operations defined. Please add at least one operation.")
        return errors, warnings
    
    # Check for duplicate new variable names
    new_names = [op['new_name'] for op in operations if op.get('new_name')]
    if len(new_names) != len(set(new_names)):
        errors.append("Duplicate new variable names found. Each new variable must have a unique name.")
    
    # Check for conflicts with existing columns
    existing_cols = df.columns.tolist()
    for new_name in new_names:
        if new_name in existing_cols:
            errors.append(f"Variable name '{new_name}' already exists in the dataset.")
    
    # Validate individual operations
    for i, op in enumerate(operations):
        op_num = i + 1
        
        if not op.get('new_name', '').strip():
            errors.append(f"Operation {op_num}: New variable name is required.")
        
        if op['operation'] == 'Addition':
            if not op.get('variables') or len(op['variables']) < 2:
                errors.append(f"Operation {op_num}: Addition requires at least 2 variables.")
        
        elif op['operation'] == 'Subtraction':
            if not op.get('variables') or len(op['variables']) != 2:
                errors.append(f"Operation {op_num}: Subtraction requires exactly 2 variables.")
    
    return errors, warnings

def apply_operations(df: pd.DataFrame, operations: List[Dict]) -> pd.DataFrame:
    """Apply all operations to create new variables"""
    result_df = df.copy()
    
    for op in operations:
        if op['operation'] == 'Addition':
            result_df[op['new_name']] = result_df[op['variables']].sum(axis=1)
        
        elif op['operation'] == 'Subtraction':
            # First variable minus second variable, negative results become 0
            result_df[op['new_name']] = (
                result_df[op['variables'][0]] - result_df[op['variables'][1]]
            ).clip(lower=0)
    
    return result_df

# File upload section
if st.session_state.df is None:
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your Data File</h3>
        <p>Upload a CSV or Excel file to create new calculated variables</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files"
    )
    
    if uploaded_file is not None:
        df = read_file(uploaded_file)
        if df is not None:
            # Check if there are numeric columns
            numeric_cols = get_numeric_columns(df)
            if len(numeric_cols) < 2:
                st.error("❌ Dataset must have at least 2 numeric columns to create new variables.")
            else:
                # Store in session state
                st.session_state.df = df
                st.session_state.original_df = df.copy()
                
                # Reset state when new file is uploaded
                st.session_state.computed_df = None
                st.session_state.operations = []
                st.session_state.variables_created = False
                
                st.success(f"✅ File uploaded successfully!")
                
                # Show file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"📊 **File:** {uploaded_file.name}")
                with col2:
                    st.info(f"📏 **Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
                with col3:
                    st.info(f"🔢 **Numeric columns:** {len(numeric_cols)}")
                
                st.rerun()

# Main content when file is uploaded
if st.session_state.df is not None:
    df = st.session_state.df
    numeric_cols = get_numeric_columns(df)
    
    # Reset button
    if st.button("🔄 Upload New File", type="secondary"):
        # Reset everything
        st.session_state.df = None
        st.session_state.original_df = None
        st.session_state.computed_df = None
        st.session_state.operations = []
        st.session_state.variables_created = False
        st.rerun()
    
    # Show current file stats
    st.subheader("📊 Current Dataset Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{df.shape[0]:,}</h3>
            <p>Rows</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{df.shape[1]}</h3>
            <p>Total Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{len(numeric_cols)}</h3>
            <p>Numeric Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        text_cols = df.select_dtypes(include=['object']).shape[1]
        st.markdown(f"""
        <div class="stats-card">
            <h3>{text_cols}</h3>
            <p>Text Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show available numeric columns
    st.subheader("🔢 Available Numeric Columns")
    st.markdown(f"**Columns available for calculations:** {', '.join(numeric_cols)}")
    
    # Operations definition section
    if not st.session_state.variables_created:
        st.subheader("🧮 Define New Variables")
        
        # Number of operations
        st.markdown("### How many new variables do you want to create?")
        num_operations = st.number_input(
            "Number of new variables",
            min_value=1,
            max_value=10,
            value=1,
            help="Enter the number of new variables you want to create"
        )
        
        operations = []
        
        # Create operation forms
        for i in range(num_operations):
            st.markdown(f"""
            <div class="operation-card">
                <div class="operation-header">
                    <h4>New Variable {i+1}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # Operation type and new variable name
            col1, col2 = st.columns(2)
            
            with col1:
                operation_type = st.selectbox(
                    "Operation Type",
                    ["Addition", "Subtraction"],
                    key=f"op_type_{i}",
                    help="Choose the mathematical operation"
                )
            
            with col2:
                new_var_name = st.text_input(
                    "New Variable Name",
                    key=f"new_name_{i}",
                    placeholder=f"Enter name for new variable {i+1}",
                    help="Enter a unique name for the new variable"
                )
            
            # Variable selection based on operation type
            if operation_type == "Addition":
                st.markdown(f"""
                <div class="operation-badge">➕ Addition</div>
                <p><strong>Select 2 or more variables to add together</strong></p>
                """, unsafe_allow_html=True)
                
                selected_vars = st.multiselect(
                    "Select variables to add",
                    numeric_cols,
                    key=f"vars_{i}",
                    help="Select at least 2 numeric variables to add together"
                )
                
                if selected_vars and len(selected_vars) >= 2:
                    formula = " + ".join(selected_vars)
                    st.markdown(f"""
                    <div class="formula-display">
                        <strong>Formula:</strong> {new_var_name or f'NewVar_{i+1}'} = {formula}
                    </div>
                    """, unsafe_allow_html=True)
            
            elif operation_type == "Subtraction":
                st.markdown(f"""
                <div class="operation-badge subtraction">➖ Subtraction</div>
                <p><strong>Select exactly 2 variables (first - second, negatives become 0)</strong></p>
                """, unsafe_allow_html=True)
                
                selected_vars = st.multiselect(
                    "Select variables for subtraction",
                    numeric_cols,
                    key=f"vars_{i}",
                    max_selections=2,
                    help="Select exactly 2 variables. The second will be subtracted from the first."
                )
                
                if len(selected_vars) == 2:
                    formula = f"{selected_vars[0]} - {selected_vars[1]}"
                    st.markdown(f"""
                    <div class="formula-display">
                        <strong>Formula:</strong> {new_var_name or f'NewVar_{i+1}'} = {formula} (negatives → 0)
                    </div>
                    """, unsafe_allow_html=True)
                elif len(selected_vars) == 1:
                    st.info("Select one more variable for subtraction.")
            
            # Add operation to list if valid
            if new_var_name and selected_vars:
                if operation_type == "Addition" and len(selected_vars) >= 2:
                    operations.append({
                        'operation': operation_type,
                        'new_name': new_var_name,
                        'variables': selected_vars
                    })
                elif operation_type == "Subtraction" and len(selected_vars) == 2:
                    operations.append({
                        'operation': operation_type,
                        'new_name': new_var_name,
                        'variables': selected_vars
                    })
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
        
        # Create variables button
        if st.button("🧮 Create New Variables", type="primary"):
            # Validate operations
            errors, warnings = validate_operations(operations, df)
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Show warnings if any
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
                
                # Apply operations
                try:
                    computed_df = apply_operations(df, operations)
                    
                    # Store results
                    st.session_state.computed_df = computed_df
                    st.session_state.operations = operations
                    st.session_state.variables_created = True
                    
                    st.success("✅ New variables created successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating variables: {str(e)}")

# Show results if variables have been created
if st.session_state.variables_created and st.session_state.computed_df is not None:
    st.subheader("📊 Results")
    
    # Show operation summary
    st.markdown("### 📋 Operations Summary")
    
    for i, op in enumerate(st.session_state.operations):
        if op['operation'] == 'Addition':
            formula = " + ".join(op['variables'])
            badge_class = ""
        else:
            formula = f"{op['variables'][0]} - {op['variables'][1]} (negatives → 0)"
            badge_class = "subtraction"
        
        st.markdown(f"""
        <div class="result-summary">
            <span class="operation-badge {badge_class}">{op['operation']}</span>
            <strong>{op['new_name']}</strong> = {formula}
        </div>
        """, unsafe_allow_html=True)
    
    # Display computed dataframe
    st.markdown("### 📈 Dataset with New Variables")
    
    # Show only new columns first, then option to see all
    new_cols = [op['new_name'] for op in st.session_state.operations]
    
    show_all = st.checkbox("Show all columns", value=False)
    
    if show_all:
        display_df = st.session_state.computed_df
        st.markdown(f"**Showing all {len(display_df.columns)} columns**")
    else:
        display_df = st.session_state.computed_df[new_cols]
        st.markdown(f"**Showing {len(new_cols)} new variables** (check box above to see all columns)")
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Summary statistics for new variables
    st.markdown("### 📊 Statistics for New Variables")
    new_vars_stats = st.session_state.computed_df[new_cols].describe()
    st.dataframe(new_vars_stats, use_container_width=True)
    
    # Download section
    st.markdown("### 💾 Download Dataset with New Variables")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv_buffer = io.StringIO()
        st.session_state.computed_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"dataset_with_new_variables_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download complete dataset with new variables as CSV"
        )
    
    with col2:
        # Excel download with operation log
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Main data
            st.session_state.computed_df.to_excel(writer, sheet_name='Data_with_New_Variables', index=False)
            
            # Operations log
            log_data = []
            for op in st.session_state.operations:
                if op['operation'] == 'Addition':
                    formula = " + ".join(op['variables'])
                else:
                    formula = f"{op['variables'][0]} - {op['variables'][1]} (negatives → 0)"
                
                log_data.append({
                    'New_Variable': op['new_name'],
                    'Operation': op['operation'],
                    'Source_Variables': ", ".join(op['variables']),
                    'Formula': formula,
                    'Created_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            log_df = pd.DataFrame(log_data)
            log_df.to_excel(writer, sheet_name='Operations_Log', index=False)
        
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"dataset_with_new_variables_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download dataset with operations log as Excel"
        )
    
    # Button to create different variables
    if st.button("🧮 Create Different Variables", type="secondary"):
        st.session_state.variables_created = False
        st.session_state.computed_df = None
        st.session_state.operations = []
        st.rerun()

# Show features when no file is uploaded
if st.session_state.df is None:
    
    # How it works section
    st.subheader("ℹ️ How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Variable Creation Process:**
        
        1. **Upload File**: CSV or Excel with numeric data
        
        2. **Choose Operations**: Addition or Subtraction
        
        3. **Select Variables**: Pick columns for calculations
        
        4. **Name Variables**: Give meaningful names to new variables
        
        5. **Create & Download**: Generate dataset with new variables
        """)
    
    with col2:
        st.markdown("""
        **Operation Types:**
        
        **➕ Addition:**
        - Select 2+ numeric variables
        - Creates sum of all selected variables
        - Example: Total_Score = Math + Science + English
        
        **➖ Subtraction:**
        - Select exactly 2 numeric variables
        - First variable minus second variable
        - Negative results automatically become 0
        """)
    
    st.subheader("✨ Tool Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🧮 Smart Calculations:**
        - Multiple operations in one session
        - Real-time formula preview
        - Automatic negative value handling
        - Comprehensive validation
        """)
    
    with col2:
        st.markdown("""
        **📊 Data Management:**
        - Original data preservation
        - Detailed operation logging
        - Statistics for new variables
        - Excel and CSV export options
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🧮 Built with Streamlit | Create New Variables Tool v1.0</p>
</div>
""", unsafe_allow_html=True)
