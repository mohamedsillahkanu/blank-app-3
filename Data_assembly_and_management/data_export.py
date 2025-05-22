import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import Dict, List

# Set page config
st.set_page_config(
    page_title="Variable Rename Tool",
    page_icon="✏️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #9C27B0 0%, #673AB7 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .column-rename-card {
        background-color: white;
        color: black;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 60px;
        display: flex;
        align-items: center;
    }
    
    .column-rename-row {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        gap: 1rem;
    }
    
    .column-rename-left,
    .column-rename-right {
        flex: 1;
    }
    
    .stTextInput > div > div > input {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
        height: 60px !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        margin: 0.5rem 0 !important;
    }
    
    .stTextInput > div {
        margin-bottom: 0 !important;
    }
    
    .stTextInput {
        margin-bottom: 0 !important;
    }
    
    .column-type-badge {
        display: inline-block;
        background-color: #2196F3;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
    }
    
    .column-type-badge.numeric {
        background-color: #4CAF50;
    }
    
    .column-type-badge.text {
        background-color: #FF9800;
    }
    
    .column-type-badge.datetime {
        background-color: #E91E63;
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
        border: 2px dashed #9C27B0;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stats-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 3px solid #9C27B0;
    }
    
    .rename-summary {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>✏️ Variable Rename Tool</h1>
    <p>Rename column variables in your dataset with ease</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'renamed_df' not in st.session_state:
    st.session_state.renamed_df = None
if 'rename_mapping' not in st.session_state:
    st.session_state.rename_mapping = {}
if 'columns_renamed' not in st.session_state:
    st.session_state.columns_renamed = False

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

def get_column_type(dtype):
    """Get user-friendly column type and corresponding CSS class"""
    if pd.api.types.is_numeric_dtype(dtype):
        return "Numeric", "numeric"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "DateTime", "datetime"
    else:
        return "Text", "text"

def validate_new_names(new_names: Dict[str, str], original_columns: List[str]) -> tuple:
    """Validate new column names and return validation results"""
    errors = []
    warnings = []
    valid_mapping = {}
    
    # Get all new names (excluding empty ones)
    proposed_names = {old: new.strip() for old, new in new_names.items() if new.strip()}
    all_new_names = list(proposed_names.values())
    
    # Add unchanged column names to the mix for duplicate checking
    unchanged_names = [col for col in original_columns if col not in proposed_names]
    all_final_names = all_new_names + unchanged_names
    
    # Check for duplicates in new names
    seen_names = set()
    for old_name, new_name in proposed_names.items():
        if new_name in seen_names:
            errors.append(f"Duplicate new name '{new_name}' found")
        elif new_name in unchanged_names:
            errors.append(f"New name '{new_name}' conflicts with existing column")
        else:
            seen_names.add(new_name)
            valid_mapping[old_name] = new_name
    
    # Check for invalid characters (optional - you can customize this)
    invalid_chars = ['/', '\\', '?', '*', '[', ']', ':', '<', '>', '|']
    for old_name, new_name in valid_mapping.items():
        if any(char in new_name for char in invalid_chars):
            warnings.append(f"Column '{new_name}' contains special characters that may cause issues")
    
    return valid_mapping, errors, warnings

# File upload section
if st.session_state.df is None:
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your Data File</h3>
        <p>Upload a CSV or Excel file to rename its column variables</p>
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
            # Store in session state
            st.session_state.df = df
            st.session_state.original_df = df.copy()
            
            # Reset rename state when new file is uploaded
            st.session_state.renamed_df = None
            st.session_state.rename_mapping = {}
            st.session_state.columns_renamed = False
            
            st.success(f"✅ File uploaded successfully!")
            
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📊 **File:** {uploaded_file.name}")
            with col2:
                st.info(f"📏 **Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
            with col3:
                st.info(f"📋 **Columns:** {len(df.columns)} variables")
            
            st.rerun()

# Main content when file is uploaded
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Reset button
    if st.button("🔄 Upload New File", type="secondary"):
        # Reset everything
        st.session_state.df = None
        st.session_state.original_df = None
        st.session_state.renamed_df = None
        st.session_state.rename_mapping = {}
        st.session_state.columns_renamed = False
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
            <p>Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).shape[1]
        st.markdown(f"""
        <div class="stats-card">
            <h3>{numeric_cols}</h3>
            <p>Numeric</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        text_cols = df.select_dtypes(include=['object']).shape[1]
        st.markdown(f"""
        <div class="stats-card">
            <h3>{text_cols}</h3>
            <p>Text</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Column renaming section
    if not st.session_state.columns_renamed:
        st.subheader("✏️ Rename Column Variables")
        st.markdown("Enter new names for the columns you want to rename. Leave blank to keep the original name.")
        
        # Create rename interface
        new_names = {}
        
        # Display columns in pairs (old name | new name input)
        for i, column in enumerate(df.columns):
            col_type, css_class = get_column_type(df[column].dtype)
            
            # Create two columns for each variable
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.markdown(f"""
                <div class="column-rename-card">
                    <strong>{column}</strong>
                    <span class="column-type-badge {css_class}">{col_type}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_right:
                new_name = st.text_input(
                    "New name",
                    key=f"rename_{i}",
                    placeholder=f"Enter new name for '{column}'",
                    label_visibility="collapsed"
                )
                new_names[column] = new_name
        
        # Rename button and validation
        st.markdown("---")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("✏️ Rename Variables", type="primary"):
                # Validate new names
                valid_mapping, errors, warnings = validate_new_names(new_names, df.columns.tolist())
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    if not valid_mapping:
                        st.warning("⚠️ No column names to change. Please enter at least one new name.")
                    else:
                        # Show warnings if any
                        for warning in warnings:
                            st.warning(f"⚠️ {warning}")
                        
                        # Apply renaming
                        try:
                            renamed_df = df.rename(columns=valid_mapping)
                            
                            # Store results
                            st.session_state.renamed_df = renamed_df
                            st.session_state.rename_mapping = valid_mapping
                            st.session_state.columns_renamed = True
                            
                            st.success("✅ Variables renamed successfully!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error renaming variables: {str(e)}")
        
        with col2:
            # Show preview of changes
            if any(name.strip() for name in new_names.values()):
                valid_mapping, errors, warnings = validate_new_names(new_names, df.columns.tolist())
                if valid_mapping and not errors:
                    st.markdown("**Preview of changes:**")
                    for old_name, new_name in valid_mapping.items():
                        st.markdown(f"• `{old_name}` → `{new_name}`")

# Show results if variables have been renamed
if st.session_state.columns_renamed and st.session_state.renamed_df is not None:
    st.subheader("📊 Rename Results")
    
    # Show rename summary
    st.markdown("### 📋 Rename Summary")
    
    if st.session_state.rename_mapping:
        for old_name, new_name in st.session_state.rename_mapping.items():
            st.markdown(f"""
            <div class="rename-summary">
                <strong>Renamed:</strong> <code>{old_name}</code> → <code>{new_name}</code>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**Total columns renamed:** {len(st.session_state.rename_mapping)}")
        st.markdown(f"**Unchanged columns:** {len(st.session_state.df.columns) - len(st.session_state.rename_mapping)}")
    
    # Display renamed dataframe
    st.markdown("### 📈 Dataset with Renamed Variables")
    st.dataframe(st.session_state.renamed_df, use_container_width=True, height=400)
    
    # Show column comparison
    st.markdown("### 🔄 Before & After Column Names")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Columns:**")
        for col in st.session_state.df.columns:
            status = "→ Renamed" if col in st.session_state.rename_mapping else "✓ Unchanged"
            st.markdown(f"• `{col}` {status}")
    
    with col2:
        st.markdown("**New Columns:**")
        for col in st.session_state.renamed_df.columns:
            # Find if this was renamed
            original_name = None
            for old, new in st.session_state.rename_mapping.items():
                if new == col:
                    original_name = old
                    break
            
            if original_name:
                st.markdown(f"• `{col}` ← Renamed from `{original_name}`")
            else:
                st.markdown(f"• `{col}` ✓ Unchanged")
    
    # Summary statistics
    st.markdown("### 📊 Dataset Statistics")
    numeric_data = st.session_state.renamed_df.select_dtypes(include=['int64', 'float64'])
    if not numeric_data.empty:
        st.dataframe(numeric_data.describe(), use_container_width=True)
    else:
        st.info("No numeric columns found for statistical summary.")
    
    # Download section
    st.markdown("### 💾 Download Renamed Dataset")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv_buffer = io.StringIO()
        st.session_state.renamed_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"renamed_variables_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download dataset with renamed variables as CSV"
        )
    
    with col2:
        # Excel download with rename log
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Main data with renamed columns
            st.session_state.renamed_df.to_excel(writer, sheet_name='Renamed_Data', index=False)
            
            # Rename log sheet
            if st.session_state.rename_mapping:
                log_data = []
                for old_name, new_name in st.session_state.rename_mapping.items():
                    log_data.append({
                        'Original_Name': old_name,
                        'New_Name': new_name,
                        'Data_Type': str(st.session_state.df[old_name].dtype),
                        'Rename_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                log_df = pd.DataFrame(log_data)
                log_df.to_excel(writer, sheet_name='Rename_Log', index=False)
        
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"renamed_variables_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download dataset with rename log as Excel"
        )
    
    # Button to rename different variables
    if st.button("✏️ Rename Different Variables", type="secondary"):
        st.session_state.columns_renamed = False
        st.session_state.renamed_df = None
        st.session_state.rename_mapping = {}
        st.rerun()

# Show features when no file is uploaded
if st.session_state.df is None:
    
    # How it works section
    st.subheader("ℹ️ How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Renaming Process:**
        
        1. **Upload File**: CSV or Excel file with your data
        
        2. **View Columns**: See all column names with their data types
        
        3. **Enter New Names**: Type new names for columns you want to rename
        
        4. **Validate**: Automatic checking for duplicates and conflicts
        
        5. **Apply Changes**: Generate dataset with new column names
        """)
    
    with col2:
        st.markdown("""
        **Features:**
        - 📊 Visual column type indicators
        - ✅ Duplicate name validation
        - 🔄 Before/after comparison
        - 📋 Detailed rename log
        - 💾 Excel and CSV downloads
        
        **Supported Formats:**
        - 📄 CSV files
        - 📊 Excel files (.xlsx, .xls)
        """)
    
    st.subheader("✨ Tool Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 Smart Interface:**
        - Side-by-side old/new name display
        - Color-coded data type indicators
        - Real-time validation
        - Preview of changes before applying
        """)
    
    with col2:
        st.markdown("""
        **🔒 Data Safety:**
        - Original data preserved
        - Comprehensive validation
        - Detailed change tracking
        - Easy rollback option
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>✏️ Built with Streamlit | Variable Rename Tool v1.0</p>
</div>
""", unsafe_allow_html=True)
