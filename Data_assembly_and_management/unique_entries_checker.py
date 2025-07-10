import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

# Set page config
st.set_page_config(
    page_title="Data Editor & Cleaner",
    page_icon="🛠️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FF6B6B 0%, #4ECDC4 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .section-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #FF6B6B;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .categorical-card {
        border-left-color: #4ECDC4;
    }
    
    .numeric-card {
        border-left-color: #45B7D1;
    }
    
    .stats-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 3px solid #FF6B6B;
    }
    
    .value-box {
        background-color: #e3f2fd;
        padding: 0.5rem;
        margin: 0.25rem;
        border-radius: 5px;
        border: 1px solid #90caf9;
        display: inline-block;
    }
    
    .problematic-value {
        background-color: #ffebee;
        border-color: #ef5350;
    }
    
    .upload-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #FF6B6B;
        text-align: center;
        margin: 1rem 0;
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
    
    .error-summary {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🛠️ Data Editor & Cleaner Tool</h1>
    <p>Clean, edit, and standardize your data - Handle categorical and numeric data issues</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = None
if 'edit_history' not in st.session_state:
    st.session_state.edit_history = []
if 'categorical_changes' not in st.session_state:
    st.session_state.categorical_changes = {}
if 'numeric_changes' not in st.session_state:
    st.session_state.numeric_changes = {}

# FUNCTION DEFINITIONS - ALL AT THE TOP
def read_file(uploaded_file) -> pd.DataFrame:
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

def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Get all non-numeric columns"""
    return [col for col in df.columns if df[col].dtype in ['object', 'string', 'category']]

def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Get all numeric columns"""
    return [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

def detect_similar_entries(values: List[str], similarity_threshold: float = 0.9) -> Dict[str, List[str]]:
    """Detect similar entries that might be data entry errors"""
    try:
        from difflib import SequenceMatcher
        
        similar_groups = {}
        processed = set()
        
        for i, val1 in enumerate(values):
            if val1 in processed:
                continue
                
            similar_list = [val1]
            processed.add(val1)
            
            for j, val2 in enumerate(values[i+1:], i+1):
                if val2 in processed:
                    continue
                    
                # Clean values for comparison (remove extra spaces, punctuation)
                clean_val1 = re.sub(r'\s+', ' ', str(val1).strip().lower())
                clean_val2 = re.sub(r'\s+', ' ', str(val2).strip().lower())
                
                # Calculate similarity
                similarity = SequenceMatcher(None, clean_val1, clean_val2).ratio()
                
                if similarity >= similarity_threshold and clean_val1 != clean_val2:
                    similar_list.append(val2)
                    processed.add(val2)
            
            # Only keep groups with more than one similar entry
            if len(similar_list) > 1:
                # Use the most common or shortest as the key
                key = min(similar_list, key=len)
                similar_groups[key] = similar_list
        
        return similar_groups
    except Exception as e:
        return {}

def detect_potential_errors(df: pd.DataFrame, categorical_cols: List[str]) -> Dict[str, Dict]:
    """Detect various types of potential data entry errors"""
    try:
        errors = {}
        
        for col in categorical_cols:
            col_errors = {}
            values = df[col].dropna().astype(str).unique().tolist()
            
            if len(values) == 0:
                continue
                
            # Similar entries detection
            similar_groups = detect_similar_entries(values)
            if similar_groups:
                col_errors['similar_entries'] = similar_groups
            
            # Common patterns that might indicate errors
            patterns = {
                'extra_spaces': [],
                'mixed_case': [],
                'special_chars': [],
                'numbers_vs_text': []
            }
            
            for val in values:
                val_str = str(val)
                
                # Extra spaces
                if val_str != val_str.strip() or '  ' in val_str:
                    patterns['extra_spaces'].append(val)
                
                # Mixed case issues (if there are both "apple" and "Apple")
                lower_versions = [v.lower() for v in values if v != val]
                if val_str.lower() in lower_versions and val_str.lower() != val_str:
                    patterns['mixed_case'].append(val)
                
                # Special characters that might be typos
                if re.search(r'[^\w\s\-\.\,]', val_str):
                    patterns['special_chars'].append(val)
                
                # Numbers vs text (like "1st" vs "first")
                if re.search(r'\d', val_str) and any(not re.search(r'\d', v) for v in values):
                    patterns['numbers_vs_text'].append(val)
            
            # Only add patterns that have entries
            for pattern_type, pattern_values in patterns.items():
                if pattern_values:
                    if 'patterns' not in col_errors:
                        col_errors['patterns'] = {}
                    col_errors['patterns'][pattern_type] = pattern_values
            
            if col_errors:
                errors[col] = col_errors
        
        return errors
    except Exception as e:
        return {}

def find_non_numeric_in_numeric_cols(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, List[Any]]:
    """Find non-numeric values in supposedly numeric columns"""
    problematic_values = {}
    
    for col in numeric_cols:
        non_numeric = []
        for idx, value in enumerate(df[col]):
            if pd.isna(value):
                continue  # Skip NA values as requested
            
            # Try to convert to numeric
            try:
                float(value)
            except (ValueError, TypeError):
                if value not in non_numeric:
                    non_numeric.append(value)
        
        if non_numeric:
            problematic_values[col] = non_numeric
    
    return problematic_values

def apply_categorical_changes(df: pd.DataFrame, changes: Dict[str, Dict]) -> pd.DataFrame:
    """Apply categorical value changes to dataframe"""
    df_copy = df.copy()
    
    for col, col_changes in changes.items():
        for action_type, values in col_changes.items():
            if action_type == 'delete':
                for value in values:
                    df_copy = df_copy[df_copy[col] != value]
            elif action_type == 'replace':
                for old_val, new_val in values.items():
                    df_copy[col] = df_copy[col].replace(old_val, new_val)
    
    return df_copy.reset_index(drop=True)

def apply_numeric_changes(df: pd.DataFrame, changes: Dict[str, Dict]) -> pd.DataFrame:
    """Apply numeric value changes to dataframe"""
    df_copy = df.copy()
    
    for col, col_changes in changes.items():
        for action_type, values in col_changes.items():
            if action_type == 'delete':
                for value in values:
                    df_copy = df_copy[df_copy[col] != value]
            elif action_type == 'replace':
                for old_val, new_val in values.items():
                    df_copy[col] = df_copy[col].replace(old_val, new_val)
                    
                # Try to convert column to numeric after replacements
                try:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                except:
                    pass
    
    return df_copy.reset_index(drop=True)

# File upload section
st.markdown("""
<div class="upload-section">
    <h3>📁 Upload Data File for Editing</h3>
    <p>Upload CSV, XLS, or XLSX file to clean and edit data</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose a file",
    type=['csv', 'xlsx', 'xls'],
    help="Upload a data file to start cleaning and editing"
)

if uploaded_file:
    with st.spinner("Loading file..."):
        df = read_file(uploaded_file)
        if df is not None:
            st.session_state.original_df = df
            st.session_state.edited_df = df.copy()
            st.session_state.edit_history = []
            st.session_state.categorical_changes = {}
            st.session_state.numeric_changes = {}
            st.success(f"✅ File loaded successfully! Shape: {df.shape[0]} rows × {df.shape[1]} columns")

if st.session_state.original_df is not None:
    df = st.session_state.original_df
    current_df = st.session_state.edited_df
    
    # Error Summary Section (Above main content)
    st.markdown("---")
    st.subheader("🚨 Data Entry Errors Summary")
    
    categorical_cols = get_categorical_columns(current_df)
    
    if categorical_cols:
        try:
            potential_errors = detect_potential_errors(current_df, categorical_cols)
            
            if potential_errors:
                # Create expandable sections for each column with issues
                cols_per_row = 2
                error_cols = list(potential_errors.keys())
                
                for i in range(0, len(error_cols), cols_per_row):
                    error_row_cols = error_cols[i:i+cols_per_row]
                    display_cols = st.columns(len(error_row_cols))
                    
                    for j, col in enumerate(error_row_cols):
                        with display_cols[j]:
                            col_errors = potential_errors[col]
                            
                            with st.expander(f"⚠️ {col} Issues", expanded=False):
                                # Similar entries
                                if 'similar_entries' in col_errors:
                                    st.markdown("**🔍 Similar Entries:**")
                                    for key, similar_list in col_errors['similar_entries'].items():
                                        st.markdown(f"**Group:** `{key}`")
                                        for item in similar_list:
                                            count = current_df[current_df[col] == item].shape[0]
                                            if item == key:
                                                st.markdown(f"  • ✅ `{item}` ({count})")
                                            else:
                                                st.markdown(f"  • ❌ `{item}` ({count})")
                                        st.markdown("---")
                                
                                # Pattern issues
                                if 'patterns' in col_errors:
                                    for pattern_type, pattern_values in col_errors['patterns'].items():
                                        if pattern_type == 'extra_spaces':
                                            st.markdown("**🔤 Extra Spaces:**")
                                        elif pattern_type == 'mixed_case':
                                            st.markdown("**🔠 Mixed Case:**")
                                        elif pattern_type == 'special_chars':
                                            st.markdown("**🔣 Special Characters:**")
                                        elif pattern_type == 'numbers_vs_text':
                                            st.markdown("**🔢 Number/Text Mix:**")
                                        
                                        for val in pattern_values[:3]:  # Show first 3
                                            count = current_df[current_df[col] == val].shape[0]
                                            st.markdown(f"  • `{repr(val)}` ({count})")
                                        
                                        if len(pattern_values) > 3:
                                            st.markdown(f"  • ... and {len(pattern_values) - 3} more")
                                        st.markdown("---")
            else:
                st.markdown("""
                <div class="success-message">
                    <strong>✅ No obvious data entry errors detected!</strong>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Error detection unavailable: {str(e)}")
    else:
        st.info("No categorical columns to check for errors.")
    
    # Show current data status
    if len(st.session_state.edit_history) > 0:
        st.markdown("---")
        st.subheader("📊 Current Data Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Rows", current_df.shape[0], 
                     delta=current_df.shape[0] - df.shape[0])
        with col2:
            st.metric("Current Columns", current_df.shape[1])
        with col3:
            changes_made = len(st.session_state.edit_history)
            st.metric("Changes Applied", changes_made)
        
        # Show a preview of current data
        with st.expander("📋 Preview Current Data (First 10 rows)", expanded=False):
            st.dataframe(current_df.head(10), use_container_width=True)
    
    # Overview section - update to show current state
    st.markdown("---")
    st.subheader("📊 Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{current_df.shape[0]}</h3>
            <p>Current Rows</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{current_df.shape[1]}</h3>
            <p>Total Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    categorical_cols = get_categorical_columns(current_df)
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{len(categorical_cols)}</h3>
            <p>Categorical Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    numeric_cols = get_numeric_columns(current_df)
    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{len(numeric_cols)}</h3>
            <p>Numeric Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Categorical Data Section
    if categorical_cols:
        st.markdown("---")
        st.subheader("📝 Categorical Data Cleaning")
        
        selected_cat_col = st.selectbox(
            "Select categorical column to edit:",
            categorical_cols,
            key="cat_col_selector"
        )
        
        if selected_cat_col:
            st.markdown(f"""
            <div class="section-card categorical-card">
                <h4>Editing Column: {selected_cat_col}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Get unique values from current edited dataframe
            unique_values = current_df[selected_cat_col].dropna().unique()
            unique_values = sorted([str(val) for val in unique_values])
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Unique Values ({len(unique_values)}):**")
                
                # Get error information for this column
                try:
                    column_errors = detect_potential_errors(current_df, [selected_cat_col])
                    has_errors = selected_cat_col in column_errors
                    similar_groups = {}
                    problematic_values = set()
                    
                    if has_errors:
                        if 'similar_entries' in column_errors[selected_cat_col]:
                            similar_groups = column_errors[selected_cat_col]['similar_entries']
                            for group_values in similar_groups.values():
                                problematic_values.update(group_values)
                        
                        if 'patterns' in column_errors[selected_cat_col]:
                            for pattern_values in column_errors[selected_cat_col]['patterns'].values():
                                problematic_values.update(pattern_values)
                
                except:
                    has_errors = False
                    problematic_values = set()
                    similar_groups = {}
                
                # Display values with error highlighting
                values_per_row = 3
                for i in range(0, len(unique_values), values_per_row):
                    row_values = unique_values[i:i+values_per_row]
                    value_cols = st.columns(len(row_values))
                    for j, val in enumerate(row_values):
                        with value_cols[j]:
                            count = current_df[current_df[selected_cat_col] == val].shape[0]
                            
                            # Check if this value has issues
                            is_problematic = val in problematic_values
                            is_similar_key = val in similar_groups.keys()
                            
                            # Determine the style and icon
                            if is_similar_key:
                                # This is the "good" version in a similar group
                                box_class = "value-box"
                                icon = "✅"
                                status = "Recommended"
                            elif is_problematic:
                                # This value has issues
                                box_class = "value-box problematic-value"
                                icon = "⚠️"
                                # Find which group this belongs to
                                group_key = None
                                for key, group_values in similar_groups.items():
                                    if val in group_values and val != key:
                                        group_key = key
                                        break
                                if group_key:
                                    status = f"Similar to '{group_key}'"
                                else:
                                    status = "Needs review"
                            else:
                                # Normal value
                                box_class = "value-box"
                                icon = ""
                                status = ""
                            
                            # Create the display
                            value_display = f"<strong>{icon} {val}</strong>" if icon else f"<strong>{val}</strong>"
                            status_display = f"<br><small style='color: #666;'>{status}</small>" if status else ""
                            
                            st.markdown(f"""
                            <div class="{box_class}">
                                {value_display}<br>
                                <small>({count} records)</small>
                                {status_display}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show similar groups summary if any
                if similar_groups:
                    st.markdown("---")
                    st.markdown("**🔍 Similar Entry Groups:**")
                    for key, group_values in similar_groups.items():
                        other_values = [v for v in group_values if v != key]
                        if other_values:
                            st.markdown(f"**{key}** (recommended) ← {', '.join(other_values)}")
                
                # Quick action buttons for common fixes
                if has_errors:
                    st.markdown("---")
                    st.markdown("**🚀 Quick Fixes:**")
                    
                    if similar_groups:
                        if st.button("🔧 Auto-fix Similar Entries", key=f"auto_fix_{selected_cat_col}"):
                            # Auto-apply fixes for similar entries
                            if selected_cat_col not in st.session_state.categorical_changes:
                                st.session_state.categorical_changes[selected_cat_col] = {'delete': [], 'replace': {}}
                            
                            fix_count = 0
                            for key, group_values in similar_groups.items():
                                for val in group_values:
                                    if val != key:  # Don't replace the key with itself
                                        st.session_state.categorical_changes[selected_cat_col]['replace'][val] = key
                                        fix_count += 1
                            
                            if fix_count > 0:
                                st.success(f"✅ Added {fix_count} automatic replacements")
                                st.rerun()
                    
                    # Show count of issues
                    total_issues = len(problematic_values)
                    if total_issues > 0:
                        st.info(f"📊 Found {total_issues} values that may need attention")
            
            with col2:
                st.markdown("**Actions:**")
                
                # Delete values
                values_to_delete = st.multiselect(
                    "Select values to DELETE:",
                    unique_values,
                    key=f"delete_{selected_cat_col}"
                )
                
                # Replace values
                st.markdown("**Replace Values:**")
                old_value = st.selectbox(
                    "Select value to replace:",
                    [""] + unique_values,
                    key=f"old_val_{selected_cat_col}"
                )
                
                if old_value:
                    new_value = st.text_input(
                        "Replace with:",
                        key=f"new_val_{selected_cat_col}"
                    )
                    
                    if st.button(f"Add Replacement", key=f"add_replace_{selected_cat_col}"):
                        if new_value:
                            if selected_cat_col not in st.session_state.categorical_changes:
                                st.session_state.categorical_changes[selected_cat_col] = {'delete': [], 'replace': {}}
                            
                            st.session_state.categorical_changes[selected_cat_col]['replace'][old_value] = new_value
                            st.success(f"✅ Added replacement: '{old_value}' → '{new_value}'")
                            st.rerun()
                
                # Apply changes for this column
                if st.button(f"Apply Changes to {selected_cat_col}", key=f"apply_cat_{selected_cat_col}"):
                    if selected_cat_col not in st.session_state.categorical_changes:
                        st.session_state.categorical_changes[selected_cat_col] = {'delete': [], 'replace': {}}
                    
                    st.session_state.categorical_changes[selected_cat_col]['delete'] = values_to_delete
                    
                    # Apply changes
                    st.session_state.edited_df = apply_categorical_changes(
                        st.session_state.edited_df, 
                        {selected_cat_col: st.session_state.categorical_changes[selected_cat_col]}
                    )
                    
                    # Add to history
                    action_details = []
                    if values_to_delete:
                        action_details.append(f"Deleted {len(values_to_delete)} values")
                    if st.session_state.categorical_changes[selected_cat_col]['replace']:
                        action_details.append(f"Applied {len(st.session_state.categorical_changes[selected_cat_col]['replace'])} replacements")
                    
                    st.session_state.edit_history.append({
                        'column': selected_cat_col,
                        'type': 'categorical',
                        'action': ', '.join(action_details) if action_details else "No changes",
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Clear the changes for this column after applying
                    st.session_state.categorical_changes[selected_cat_col] = {'delete': [], 'replace': {}}
                    
                    st.success(f"✅ Applied changes to {selected_cat_col}")
                    st.rerun()
            
            # Show current changes for this column
            if selected_cat_col in st.session_state.categorical_changes:
                changes = st.session_state.categorical_changes[selected_cat_col]
                if changes['delete'] or changes['replace']:
                    st.markdown("**Pending Changes:**")
                    if changes['delete']:
                        st.write(f"🗑️ Delete: {', '.join(map(str, changes['delete']))}")
                    if changes['replace']:
                        for old, new in changes['replace'].items():
                            st.write(f"🔄 Replace: '{old}' → '{new}'")
    
    # Numeric Data Section
    if numeric_cols:
        st.markdown("---")
        st.subheader("🔢 Numeric Data Cleaning")
        
        # Find problematic values in numeric columns using current edited dataframe
        problematic_values = find_non_numeric_in_numeric_cols(current_df, numeric_cols)
        
        if problematic_values:
            st.markdown(f"""
            <div class="warning-message">
                <strong>⚠️ Found non-numeric values in {len(problematic_values)} numeric columns</strong>
            </div>
            """, unsafe_allow_html=True)
            
            selected_num_col = st.selectbox(
                "Select numeric column with issues to fix:",
                list(problematic_values.keys()),
                key="num_col_selector"
            )
            
            if selected_num_col:
                st.markdown(f"""
                <div class="section-card numeric-card">
                    <h4>Fixing Column: {selected_num_col}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                problematic_vals = problematic_values[selected_num_col]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Problematic Values ({len(problematic_vals)}):**")
                    
                    for val in problematic_vals:
                        count = current_df[current_df[selected_num_col] == val].shape[0]
                        st.markdown(f"""
                        <div class="value-box problematic-value">
                            <strong>{val}</strong> (Type: {type(val).__name__})<br>
                            <small>({count} records)</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**Actions:**")
                    
                    # Delete problematic values
                    values_to_delete = st.multiselect(
                        "Select values to DELETE:",
                        problematic_vals,
                        key=f"delete_num_{selected_num_col}"
                    )
                    
                    # Replace problematic values
                    st.markdown("**Replace Values:**")
                    old_value = st.selectbox(
                        "Select value to replace:",
                        [""] + problematic_vals,
                        key=f"old_num_val_{selected_num_col}"
                    )
                    
                    if old_value:
                        new_value = st.text_input(
                            "Replace with (numeric value):",
                            key=f"new_num_val_{selected_num_col}",
                            help="Enter a numeric value or leave empty for NaN"
                        )
                        
                        if st.button(f"Add Numeric Replacement", key=f"add_num_replace_{selected_num_col}"):
                            if selected_num_col not in st.session_state.numeric_changes:
                                st.session_state.numeric_changes[selected_num_col] = {'delete': [], 'replace': {}}
                            
                            # Validate numeric input
                            if new_value == "":
                                replacement_val = np.nan
                            else:
                                try:
                                    replacement_val = float(new_value)
                                except ValueError:
                                    st.error("❌ Please enter a valid numeric value")
                                    replacement_val = None
                            
                            if replacement_val is not None or new_value == "":
                                st.session_state.numeric_changes[selected_num_col]['replace'][old_value] = replacement_val
                                st.success(f"✅ Added replacement: '{old_value}' → {replacement_val}")
                                st.rerun()
                    
                    # Apply changes for this column
                    if st.button(f"Apply Changes to {selected_num_col}", key=f"apply_num_{selected_num_col}"):
                        if selected_num_col not in st.session_state.numeric_changes:
                            st.session_state.numeric_changes[selected_num_col] = {'delete': [], 'replace': {}}
                        
                        st.session_state.numeric_changes[selected_num_col]['delete'] = values_to_delete
                        
                        # Apply changes
                        st.session_state.edited_df = apply_numeric_changes(
                            st.session_state.edited_df, 
                            {selected_num_col: st.session_state.numeric_changes[selected_num_col]}
                        )
                        
                        # Add to history
                        action_details = []
                        if values_to_delete:
                            action_details.append(f"Deleted {len(values_to_delete)} problematic values")
                        if st.session_state.numeric_changes[selected_num_col]['replace']:
                            action_details.append(f"Applied {len(st.session_state.numeric_changes[selected_num_col]['replace'])} replacements")
                        
                        st.session_state.edit_history.append({
                            'column': selected_num_col,
                            'type': 'numeric',
                            'action': ', '.join(action_details) if action_details else "No changes",
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        
                        # Clear the changes for this column after applying
                        st.session_state.numeric_changes[selected_num_col] = {'delete': [], 'replace': {}}
                        
                        st.success(f"✅ Applied changes to {selected_num_col}")
                        st.rerun()
                
                # Show current changes for this column
                if selected_num_col in st.session_state.numeric_changes:
                    changes = st.session_state.numeric_changes[selected_num_col]
                    if changes['delete'] or changes['replace']:
                        st.markdown("**Pending Changes:**")
                        if changes['delete']:
                            st.write(f"🗑️ Delete: {', '.join(map(str, changes['delete']))}")
                        if changes['replace']:
                            for old, new in changes['replace'].items():
                                st.write(f"🔄 Replace: '{old}' → {new}")
        else:
            st.markdown(f"""
            <div class="success-message">
                <strong>✅ All numeric columns look clean! No non-numeric values found.</strong>
            </div>
            """, unsafe_allow_html=True)
    
    # Edit History and Summary
    if st.session_state.edit_history:
        st.markdown("---")
        st.subheader("📋 Edit History")
        
        for i, edit in enumerate(reversed(st.session_state.edit_history)):
            st.markdown(f"""
            <div class="section-card">
                <strong>{edit['timestamp']}</strong> - {edit['column']} ({edit['type']})<br>
                <small>{edit['action']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Final Results and Download
    if st.session_state.edited_df is not None and len(st.session_state.edit_history) > 0:
        st.markdown("---")
        st.subheader("💾 Save Cleaned Data")
        
        # Show before/after comparison
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Rows", st.session_state.original_df.shape[0])
        with col2:
            st.metric("Cleaned Rows", st.session_state.edited_df.shape[0])
        with col3:
            rows_removed = st.session_state.original_df.shape[0] - st.session_state.edited_df.shape[0]
            st.metric("Rows Removed", rows_removed)
        
        # Preview cleaned data
        with st.expander("Preview Cleaned Data (First 10 rows)"):
            st.dataframe(st.session_state.edited_df.head(10), use_container_width=True)
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download
            csv_buffer = io.StringIO()
            st.session_state.edited_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Cleaned CSV",
                data=csv_data,
                file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Download cleaned data as CSV file"
            )
        
        with col2:
            # Excel download
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                st.session_state.edited_df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
                
                # Add edit history sheet
                if st.session_state.edit_history:
                    history_df = pd.DataFrame(st.session_state.edit_history)
                    history_df.to_excel(writer, sheet_name='Edit_History', index=False)
            
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Cleaned Excel",
                data=excel_data,
                file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download cleaned data as Excel file with edit history"
            )
        
        # Reset button
        if st.button("🔄 Start Over", type="secondary"):
            st.session_state.edited_df = st.session_state.original_df.copy()
            st.session_state.edit_history = []
            st.session_state.categorical_changes = {}
            st.session_state.numeric_changes = {}
            st.success("✅ Reset to original data")
            st.rerun()

# Show features when no file is uploaded
if st.session_state.original_df is None:
    st.subheader("✨ Tool Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📝 Categorical Data Cleaning:**
        - View all unique values with counts
        - Delete unwanted values/categories
        - Replace/standardize values
        - Real-time preview of changes
        """)
    
    with col2:
        st.markdown("""
        **🔢 Numeric Data Cleaning:**
        - Detect non-numeric values in numeric columns
        - Delete problematic entries
        - Replace with proper numeric values
        - Automatic type conversion after cleaning
        """)
    
    st.markdown("""
    **🛠️ Additional Features:**
    - **🚨 Data Entry Error Detection**: Automatically finds similar entries like "February 2026" vs "February 2026."
    - Edit history tracking
    - Before/after comparison
    - Preview cleaned data
    - Download cleaned files (CSV/Excel)
    - Reset functionality
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🛠️ Data Editor & Cleaner Tool v1.0 | Clean Your Data with Precision</p>
</div>
""", unsafe_allow_html=True)
