import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Compute New Variables Tool",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .computation-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .variable-tag {
        display: inline-block;
        background-color: #e7f3ff;
        color: #1976d2;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 15px;
        font-size: 0.8rem;
        border: 1px solid #bbdefb;
    }
    
    .operation-badge {
        display: inline-block;
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    
    .operation-badge.subtract {
        background-color: #ff9800;
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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🧮 Compute New Variables Tool</h1>
    <p>Create new calculated variables from existing columns</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'num_computations' not in st.session_state:
    st.session_state.num_computations = 0
if 'computations' not in st.session_state:
    st.session_state.computations = []
if 'used_variables' not in st.session_state:
    st.session_state.used_variables = set()
if 'computed_df' not in st.session_state:
    st.session_state.computed_df = None
if 'computations_applied' not in st.session_state:
    st.session_state.computations_applied = False

# Helper functions
def get_available_columns(exclude_used=True):
    """Get columns that haven't been used in computations"""
    if st.session_state.df is None:
        return []
    
    # Get numeric columns only
    numeric_cols = st.session_state.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Remove already used variables if requested
    if exclude_used:
        available_cols = [col for col in numeric_cols if col not in st.session_state.used_variables]
        return available_cols
    else:
        return numeric_cols

def compute_variable(df, selected_vars, operation):
    """Compute new variable based on operation"""
    if operation == "Addition":
        return df[selected_vars].sum(axis=1)
    elif operation == "Subtraction":
        if len(selected_vars) != 2:
            return None
        result = df[selected_vars[0]] - df[selected_vars[1]]
        # Replace negative values with 0
        return result.clip(lower=0)
    return None

def apply_all_computations():
    """Apply all computations to create computed dataframe"""
    if st.session_state.df is None:
        return None
    
    computed_df = st.session_state.df.copy()
    
    for computation in st.session_state.computations:
        new_var = computation['new_variable']
        selected_vars = computation['variables']
        operation = computation['operation']
        
        # Compute the new variable
        computed_df[new_var] = compute_variable(computed_df, selected_vars, operation)
    
    return computed_df

# Sidebar for file upload
with st.sidebar:
    st.header("📁 File Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files"
    )
    
    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Store in session state
            st.session_state.df = df
            st.session_state.original_df = df.copy()
            
            # Reset computations when new file is uploaded
            st.session_state.computations = []
            st.session_state.used_variables = set()
            st.session_state.computed_df = None
            st.session_state.computations_applied = False
            
            st.success(f"✅ File uploaded successfully!")
            st.info(f"📊 **File:** {uploaded_file.name}")
            st.info(f"📏 **Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Show numeric columns info
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            st.info(f"🔢 **Numeric columns:** {len(numeric_cols)}")
            
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    # Option to use sample data if no file is uploaded
    if st.session_state.df is None and st.button("📊 Use Sample Data"):
        # Create sample data
        sample_data = {
            'Variable A': [10, 15, 8, 12, 20],
            'Variable B': [5, 8, 3, 9, 15],
            'Variable C': [7, 12, 9, 14, 6],
            'Variable D': [3, 6, 9, 12, 15],
            'Variable E': [20, 15, 10, 5, 0]
        }
        df = pd.DataFrame(sample_data)
        
        # Store in session state
        st.session_state.df = df
        st.session_state.original_df = df.copy()
        
        # Reset computations
        st.session_state.computations = []
        st.session_state.used_variables = set()
        st.session_state.computed_df = None
        st.session_state.computations_applied = False
        
        st.success(f"✅ Sample data loaded successfully!")
        st.rerun()

# Main content
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Step 1: Ask for number of variables to compute
    if not st.session_state.computations:
        st.subheader("Step 1: How many new variables do you want to compute?")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            num_computations = st.number_input(
                "Number of variables",
                min_value=1,
                max_value=20,
                value=st.session_state.num_computations if st.session_state.num_computations > 0 else 3,
                step=1,
                help="Enter the number of new variables you want to compute"
            )
        
        with col2:
            if st.button("Set Up Computations", type="primary"):
                st.session_state.num_computations = num_computations
                st.rerun()
    
    # Step 2: Configure computations
    if st.session_state.num_computations > 0:
        st.subheader(f"Step 2: Configure {st.session_state.num_computations} New Variables")
        
        # Get available columns
        available_cols = get_available_columns(exclude_used=False)
        
        # Create forms for each computation
        computations = []
        
        for i in range(st.session_state.num_computations):
            st.markdown(f"#### New Variable {i+1}")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                var_name = st.text_input(
                    "New Variable Name",
                    key=f"var_name_{i}",
                    value=f"NewVar_{i+1}" if f"var_name_{i}" not in st.session_state else st.session_state[f"var_name_{i}"],
                    help="Enter name for the new variable"
                )
            
            with col2:
                operation = st.selectbox(
                    "Operation",
                    ["Addition", "Subtraction"],
                    key=f"operation_{i}",
                    help="Choose mathematical operation"
                )
            
            with col3:
                # Filter out variables that are already used in other computations
                current_used = set()
                for comp in computations:
                    current_used.update(comp["variables"])
                
                filtered_cols = [col for col in available_cols if col not in current_used or col in st.session_state.get(f"selected_vars_{i}", [])]
                
                if operation == "Subtraction":
                    if f"selected_vars_{i}" in st.session_state and len(st.session_state[f"selected_vars_{i}"]) > 2:
                        # Reset selection if switching from addition to subtraction with more than 2 variables
                        st.session_state[f"selected_vars_{i}"] = st.session_state[f"selected_vars_{i}"][:2] if len(st.session_state[f"selected_vars_{i}"]) > 0 else []
                    
                    selected_vars = st.multiselect(
                        "Select Variables (exactly 2)",
                        filtered_cols,
                        key=f"selected_vars_{i}",
                        default=st.session_state.get(f"selected_vars_{i}", []),
                        max_selections=2,
                        help="Select exactly 2 variables for subtraction. The second will be subtracted from the first."
                    )
                    
                    if len(selected_vars) == 2:
                        st.caption(f"Formula: {selected_vars[0]} - {selected_vars[1]} (negative results → 0)")
                else:
                    selected_vars = st.multiselect(
                        "Select Variables to Add",
                        filtered_cols,
                        key=f"selected_vars_{i}",
                        default=st.session_state.get(f"selected_vars_{i}", []),
                        help="Select variables to add together"
                    )
                    
                    if selected_vars:
                        st.caption(f"Formula: {' + '.join(selected_vars)}")
            
            # Add to computations list
            if var_name and selected_vars:
                if operation != "Subtraction" or len(selected_vars) == 2:
                    computations.append({
                        "new_variable": var_name,
                        "operation": operation,
                        "variables": selected_vars
                    })
            
            st.markdown("---")
        
        # Save computations to session state
        if st.button("Compute Variables", type="primary"):
            # Validate computations
            valid = True
            used_variables = set()
            new_var_names = set()
            
            for i, comp in enumerate(computations):
                # Check if variable name is empty
                if not comp["new_variable"].strip():
                    st.error(f"❌ Variable name cannot be empty for New Variable {i+1}")
                    valid = False
                
                # Check if variable name is unique
                if comp["new_variable"] in new_var_names:
                    st.error(f"❌ Variable name '{comp['new_variable']}' is used more than once")
                    valid = False
                else:
                    new_var_names.add(comp["new_variable"])
                
                # Check if variable name already exists in the dataframe
                if comp["new_variable"] in df.columns:
                    st.error(f"❌ Variable name '{comp['new_variable']}' already exists in the data")
                    valid = False
                
                # Check if enough variables are selected
                if not comp["variables"]:
                    st.error(f"❌ No variables selected for '{comp['new_variable']}'")
                    valid = False
                
                # Check if subtraction has exactly 2 variables
                if comp["operation"] == "Subtraction" and len(comp["variables"]) != 2:
                    st.error(f"❌ Subtraction requires exactly 2 variables for '{comp['new_variable']}'")
                    valid = False
                
                # Check for variable reuse
                for var in comp["variables"]:
                    if var in used_variables:
                        st.error(f"❌ Variable '{var}' is used in multiple computations")
                        valid = False
                    else:
                        used_variables.add(var)
            
            if valid:
                st.session_state.computations = computations
                st.session_state.used_variables = used_variables
                
                # Apply computations
                try:
                    st.session_state.computed_df = apply_all_computations()
                    st.session_state.computations_applied = True
                    st.success("✅ Variables computed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error computing variables: {str(e)}")
    
    # Step 3: Show results
    if st.session_state.computations_applied and st.session_state.computed_df is not None:
        st.subheader("Step 3: Results")
        
        # Show summary of computations
        st.markdown("### Computation Summary")
        
        for i, comp in enumerate(st.session_state.computations):
            operation_class = "subtract" if comp['operation'] == "Subtraction" else ""
            vars_html = "".join([f'<span class="variable-tag">{var}</span>' for var in comp['variables']])
            
            st.markdown(f"""
            <div class="computation-card">
                <strong>{comp['new_variable']}</strong> = 
                <span class="operation-badge {operation_class}">{comp['operation']}</span>
                <div>{vars_html}</div>
                {f"<small>Formula: {comp['variables'][0]} - {comp['variables'][1]} (negatives → 0)</small>" if comp['operation'] == "Subtraction" else f"<small>Formula: {' + '.join(comp['variables'])}</small>"}
            </div>
            """, unsafe_allow_html=True)
        
        # Display computed dataframe
        st.markdown("### Data with Computed Variables")
        st.dataframe(st.session_state.computed_df, use_container_width=True)
        
        # Summary statistics for new variables
        st.markdown("### Statistics for New Variables")
        new_vars = [comp['new_variable'] for comp in st.session_state.computations]
        stats_df = st.session_state.computed_df[new_vars].describe().T
        st.dataframe(stats_df, use_container_width=True)
        
        # Download section
        st.markdown("### Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download
            csv_buffer = io.StringIO()
            st.session_state.computed_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f"computed_variables_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Download data with computed variables as CSV"
            )
        
        with col2:
            # Excel download
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                st.session_state.computed_df.to_excel(writer, sheet_name='Computed Data', index=False)
                
                # Add computation log in a separate sheet
                log_data = []
                for comp in st.session_state.computations:
                    if comp['operation'] == 'Addition':
                        formula = ' + '.join(comp['variables'])
                    else:
                        formula = f"{comp['variables'][0]} - {comp['variables'][1]} (negatives → 0)"
                    
                    log_data.append({
                        'New_Variable': comp['new_variable'],
                        'Operation': comp['operation'],
                        'Source_Variables': ', '.join(comp['variables']),
                        'Formula': formula
                    })
                
                log_df = pd.DataFrame(log_data)
                log_df.to_excel(writer, sheet_name='Computation Log', index=False)
            
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📥 Download as Excel",
                data=excel_data,
                file_name=f"computed_variables_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download data with computation log as Excel"
            )
        
        # Button to reset and create new computations
        if st.button("🔄 Create New Computations", type="secondary"):
            st.session_state.num_computations = 0 
            st.session_state.computations = []
            st.session_state.used_variables = set()
            st.session_state.computed_df = None
            st.session_state.computations_applied = False
            st.rerun()

else:
    # Show instructions when no file is uploaded
    st.markdown("""
    <div style="border: 2px dashed #ccc; border-radius: 10px; padding: 2rem; text-align: center; background-color: #f8f9fa; margin: 1rem 0;">
        <h3>📁 No file uploaded yet</h3>
        <p>Please upload a CSV or Excel file using the sidebar to get started.</p>
        <p>Alternatively, you can use the sample data option in the sidebar.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show features
    st.subheader("✨ Tool Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Computation Options:**
        - **Addition:** Sum multiple variables together
        - **Subtraction:** Subtract one variable from another
        - **Smart handling:** Negative results become zero
        - **Batch creation:** Set up multiple variables at once
        """)
    
    with col2:
        st.markdown("""
        **🔒 Smart Constraints:**
        - Variables are used only once across all computations
        - Subtraction requires exactly 2 variables
        - Addition allows multiple variables
        - Automatic validation and error checking
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🧮 Built with Streamlit | Compute New Variables Tool v1.0</p>
</div>
""", unsafe_allow_html=True)
