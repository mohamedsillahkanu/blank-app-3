import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np

# Set page config
st.set_page_config(
    page_title="File Combiner Tool",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .file-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .file-type-badge {
        display: inline-block;
        background-color: #2196F3;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    
    .file-type-badge.csv {
        background-color: #FF9800;
    }
    
    .file-type-badge.excel {
        background-color: #4CAF50;
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
        border: 2px dashed #4CAF50;
        text-align: center;
        margin: 1rem 0;
    }
    
    .column-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #2196F3;
    }
    
    .stats-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 3px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔗 File Combiner Tool</h1>
    <p>Combine multiple XLS, XLSX, and CSV files with common columns</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = []
if 'combined_df' not in st.session_state:
    st.session_state.combined_df = None
if 'combination_log' not in st.session_state:
    st.session_state.combination_log = []

def read_file(uploaded_file) -> Tuple[pd.DataFrame, str]:
    """Read uploaded file and return DataFrame and file type"""
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            file_type = 'CSV'
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(uploaded_file)
            file_type = 'Excel'
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return df, file_type
    except Exception as e:
        st.error(f"Error reading file {uploaded_file.name}: {str(e)}")
        return None, None

def find_common_columns(dataframes: List[pd.DataFrame]) -> List[str]:
    """Find columns that are common across all dataframes"""
    if not dataframes:
        return []
    
    common_cols = set(dataframes[0].columns)
    for df in dataframes[1:]:
        common_cols = common_cols.intersection(set(df.columns))
    
    return sorted(list(common_cols))

def combine_files_by_type(files_data: List[Dict]) -> Dict[str, pd.DataFrame]:
    """Combine files by their type (CSV, Excel) based on common columns"""
    combined_dfs = {}
    
    # Group files by type
    files_by_type = {}
    for file_data in files_data:
        file_type = file_data['type']
        if file_type not in files_by_type:
            files_by_type[file_type] = []
        files_by_type[file_type].append(file_data)
    
    # Combine files within each type
    for file_type, files in files_by_type.items():
        if len(files) == 1:
            # Only one file of this type
            combined_dfs[file_type] = files[0]['dataframe'].copy()
            combined_dfs[file_type]['source_file'] = files[0]['name']
        else:
            # Multiple files of the same type - find common columns and combine
            dataframes = [file_data['dataframe'] for file_data in files]
            common_cols = find_common_columns(dataframes)
            
            if common_cols:
                # Combine using common columns
                combined_list = []
                for i, file_data in enumerate(files):
                    df_subset = file_data['dataframe'][common_cols].copy()
                    df_subset['source_file'] = file_data['name']
                    combined_list.append(df_subset)
                
                combined_dfs[file_type] = pd.concat(combined_list, ignore_index=True)
            else:
                # No common columns - keep files separate with file identifier
                combined_list = []
                for file_data in files:
                    df_copy = file_data['dataframe'].copy()
                    df_copy['source_file'] = file_data['name']
                    combined_list.append(df_copy)
                
                combined_dfs[file_type] = pd.concat(combined_list, ignore_index=True, sort=False)
    
    return combined_dfs

def create_combination_log(files_data: List[Dict], combined_dfs: Dict[str, pd.DataFrame]) -> List[Dict]:
    """Create a log of the combination process"""
    log = []
    
    # Group files by type for logging
    files_by_type = {}
    for file_data in files_data:
        file_type = file_data['type']
        if file_type not in files_by_type:
            files_by_type[file_type] = []
        files_by_type[file_type].append(file_data)
    
    for file_type, files in files_by_type.items():
        if len(files) > 1:
            dataframes = [file_data['dataframe'] for file_data in files]
            common_cols = find_common_columns(dataframes)
            
            log_entry = {
                'file_type': file_type,
                'files_combined': len(files),
                'file_names': [f['name'] for f in files],
                'common_columns': common_cols,
                'total_rows_before': sum(df.shape[0] for df in dataframes),
                'total_rows_after': combined_dfs[file_type].shape[0],
                'columns_after': list(combined_dfs[file_type].columns)
            }
            log.append(log_entry)
    
    return log

# File upload section
st.markdown("""
<div class="upload-section">
    <h3>📁 Upload Multiple Files</h3>
    <p>Upload multiple XLS, XLSX, and CSV files to combine them by file type</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Choose files",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True,
    help="Upload multiple CSV, XLS, or XLSX files. Files of the same type will be combined based on common columns."
)

if uploaded_files:
    # Process uploaded files
    files_data = []
    
    with st.spinner("Processing uploaded files..."):
        for uploaded_file in uploaded_files:
            df, file_type = read_file(uploaded_file)
            if df is not None:
                files_data.append({
                    'name': uploaded_file.name,
                    'type': file_type,
                    'dataframe': df,
                    'shape': df.shape,
                    'columns': list(df.columns)
                })
    
    if files_data:
        # Store in session state
        st.session_state.uploaded_files_data = files_data
        
        # Display uploaded files summary
        st.subheader("📋 Uploaded Files Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(files_data)}</h3>
                <p>Total Files</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            csv_count = sum(1 for f in files_data if f['type'] == 'CSV')
            st.markdown(f"""
            <div class="stats-card">
                <h3>{csv_count}</h3>
                <p>CSV Files</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            excel_count = sum(1 for f in files_data if f['type'] == 'Excel')
            st.markdown(f"""
            <div class="stats-card">
                <h3>{excel_count}</h3>
                <p>Excel Files</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display individual file information
        st.markdown("### 📄 Individual File Details")
        
        for i, file_data in enumerate(files_data):
            badge_class = "csv" if file_data['type'] == 'CSV' else "excel"
            
            st.markdown(f"""
            <div class="file-card">
                <div>
                    <span class="file-type-badge {badge_class}">{file_data['type']}</span>
                    <strong>{file_data['name']}</strong>
                </div>
                <div style="margin-top: 0.5rem;">
                    <small>📏 Shape: {file_data['shape'][0]} rows × {file_data['shape'][1]} columns</small><br>
                    <small>📊 Columns: {', '.join(file_data['columns'][:5])}{'...' if len(file_data['columns']) > 5 else ''}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show common columns analysis by file type
        st.markdown("### 🔍 Common Columns Analysis")
        
        files_by_type = {}
        for file_data in files_data:
            file_type = file_data['type']
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file_data)
        
        for file_type, files in files_by_type.items():
            if len(files) > 1:
                dataframes = [f['dataframe'] for f in files]
                common_cols = find_common_columns(dataframes)
                
                st.markdown(f"""
                <div class="column-info">
                    <strong>{file_type} Files ({len(files)} files)</strong><br>
                    <strong>Common columns ({len(common_cols)}):</strong> {', '.join(common_cols) if common_cols else 'No common columns found'}<br>
                    <small>Files: {', '.join([f['name'] for f in files])}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="column-info">
                    <strong>{file_type} Files (1 file)</strong><br>
                    <strong>All columns will be preserved:</strong> {', '.join(files[0]['columns'][:10])}{'...' if len(files[0]['columns']) > 10 else ''}<br>
                    <small>File: {files[0]['name']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Combine files button
        if st.button("🔗 Combine Files", type="primary"):
            with st.spinner("Combining files..."):
                try:
                    # Combine files by type
                    combined_dfs = combine_files_by_type(files_data)
                    
                    # Create combination log
                    combination_log = create_combination_log(files_data, combined_dfs)
                    
                    # Store results in session state
                    st.session_state.combined_df = combined_dfs
                    st.session_state.combination_log = combination_log
                    
                    st.success("✅ Files combined successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error combining files: {str(e)}")

# Display results if files have been combined
if st.session_state.combined_df:
    st.subheader("📊 Combined Results")
    
    # Show combination summary
    if st.session_state.combination_log:
        st.markdown("### 📋 Combination Summary")
        
        for log_entry in st.session_state.combination_log:
            st.markdown(f"""
            <div class="success-message">
                <strong>{log_entry['file_type']} Files Combined</strong><br>
                <strong>Files:</strong> {log_entry['files_combined']} files combined<br>
                <strong>Names:</strong> {', '.join(log_entry['file_names'])}<br>
                <strong>Common Columns:</strong> {len(log_entry['common_columns'])} ({', '.join(log_entry['common_columns']) if log_entry['common_columns'] else 'None'})<br>
                <strong>Rows:</strong> {log_entry['total_rows_before']} → {log_entry['total_rows_after']}<br>
                <strong>Final Columns:</strong> {len(log_entry['columns_after'])}
            </div>
            """, unsafe_allow_html=True)
    
    # Display each combined dataframe
    for file_type, combined_df in st.session_state.combined_df.items():
        st.markdown(f"### 📈 Combined {file_type} Data")
        
        # Show basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", combined_df.shape[0])
        with col2:
            st.metric("Columns", combined_df.shape[1])
        with col3:
            numeric_cols = combined_df.select_dtypes(include=[np.number]).shape[1]
            st.metric("Numeric Columns", numeric_cols)
        
        # Display the dataframe
        st.dataframe(combined_df, use_container_width=True, height=400)
        
        # Show basic statistics for numeric columns
        numeric_data = combined_df.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            with st.expander(f"📊 Statistics for {file_type} Data"):
                st.dataframe(numeric_data.describe(), use_container_width=True)
        
        st.markdown("---")
    
    # Download options
    st.subheader("💾 Download Combined Data")
    
    # Prepare download data
    if len(st.session_state.combined_df) == 1:
        # Single file type - download directly
        file_type, df_to_download = list(st.session_state.combined_df.items())[0]
        download_filename = f"combined_{file_type.lower()}_data"
    else:
        # Multiple file types - combine all into one
        all_dfs = []
        for file_type, df in st.session_state.combined_df.items():
            df_copy = df.copy()
            df_copy['data_type'] = file_type
            all_dfs.append(df_copy)
        
        df_to_download = pd.concat(all_dfs, ignore_index=True, sort=False)
        download_filename = "combined_all_data"
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv_buffer = io.StringIO()
        df_to_download.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"{download_filename}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download combined data as CSV file"
        )
    
    with col2:
        # Excel download with multiple sheets
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # If multiple file types, create separate sheets
            if len(st.session_state.combined_df) > 1:
                for file_type, df in st.session_state.combined_df.items():
                    sheet_name = f"Combined_{file_type}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Also create a combined sheet
                df_to_download.to_excel(writer, sheet_name='All_Combined', index=False)
            else:
                # Single file type
                df_to_download.to_excel(writer, sheet_name='Combined_Data', index=False)
            
            # Add combination log sheet
            if st.session_state.combination_log:
                log_data = []
                for log_entry in st.session_state.combination_log:
                    log_data.append({
                        'File_Type': log_entry['file_type'],
                        'Files_Combined': log_entry['files_combined'],
                        'File_Names': '; '.join(log_entry['file_names']),
                        'Common_Columns': '; '.join(log_entry['common_columns']),
                        'Rows_Before': log_entry['total_rows_before'],
                        'Rows_After': log_entry['total_rows_after'],
                        'Final_Columns': '; '.join(log_entry['columns_after'])
                    })
                
                log_df = pd.DataFrame(log_data)
                log_df.to_excel(writer, sheet_name='Combination_Log', index=False)
        
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"{download_filename}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download combined data as Excel file with multiple sheets"
        )

# Sidebar information
with st.sidebar:
    st.header("ℹ️ How It Works")
    
    st.markdown("""
    **File Combination Logic:**
    
    1. **By File Type**: Files are grouped by type (CSV, Excel)
    
    2. **Common Columns**: Within each type, files are combined based on common columns
    
    3. **Source Tracking**: A 'source_file' column is added to track original files
    
    4. **No Common Columns**: If no common columns exist, all columns are preserved
    """)
    
    st.markdown("---")
    
    st.markdown("""
    **Supported Formats:**
    - 📄 CSV files
    - 📊 Excel files (.xlsx, .xls)
    """)
    
    st.markdown("---")
    
    if st.session_state.uploaded_files_data:
        if st.button("🔄 Upload New Files"):
            # Clear all session state
            st.session_state.uploaded_files_data = []
            st.session_state.combined_df = None
            st.session_state.combination_log = []
            st.rerun()

# Show features when no files are uploaded
if not uploaded_files and not st.session_state.uploaded_files_data:
    st.subheader("✨ Tool Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 File Processing:**
        - Upload multiple files at once
        - Support for CSV, XLS, and XLSX
        - Automatic file type detection
        - Smart column matching
        """)
    
    with col2:
        st.markdown("""
        **🔗 Combination Logic:**
        - Group files by type (CSV/Excel)
        - Find common columns automatically
        - Preserve source file information
        - Handle files with different schemas
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔗 Built with Streamlit | File Combiner Tool v1.0</p>
</div>
""", unsafe_allow_html=True)
