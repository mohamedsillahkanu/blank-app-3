import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
import gc  # For garbage collection

# Set page config
st.set_page_config(
    page_title="File Combiner Tool",
    page_icon="🔗",
    layout="wide"
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
    
    .column-list {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
    }
    
    .clear-memory-section {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔗 Enhanced File Combiner Tool</h1>
    <p>Combine multiple XLS, XLSX, and CSV files with ALL columns (common + uncommon)</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = []
if 'combined_df' not in st.session_state:
    st.session_state.combined_df = None
if 'combination_log' not in st.session_state:
    st.session_state.combination_log = []

def clear_memory_and_cache():
    """Clear all session state data and force garbage collection"""
    # Clear session state
    st.session_state.uploaded_files_data = []
    st.session_state.combined_df = None
    st.session_state.combination_log = []
    
    # Force garbage collection to free memory
    gc.collect()
    
    # Clear Streamlit cache
    st.cache_data.clear()
    st.cache_resource.clear()

def clean_dataframe(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """Clean dataframe by removing empty rows and unnamed columns"""
    original_shape = df.shape
    
    # Remove rows where first column is empty/null
    if len(df.columns) > 0:
        first_col = df.columns[0]
        df = df.dropna(subset=[first_col])
        df = df[df[first_col].astype(str).str.strip() != '']
    
    # Remove columns that are unnamed or have variations of 'Unnamed'
    columns_to_keep = []
    for col in df.columns:
        col_str = str(col).lower().strip()
        if not (col_str.startswith('unnamed') or col_str == 'nan' or col_str == ''):
            columns_to_keep.append(col)
    
    df = df[columns_to_keep]
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Reset index
    df = df.reset_index(drop=True)
    
    cleaned_shape = df.shape
    
    if original_shape != cleaned_shape:
        st.info(f"📋 Cleaned {filename}: {original_shape[0]} → {cleaned_shape[0]} rows, {original_shape[1]} → {cleaned_shape[1]} columns")
    
    return df

@st.cache_data
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
        
        # Clean the dataframe
        df = clean_dataframe(df, uploaded_file.name)
        
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

def get_all_columns(dataframes: List[pd.DataFrame]) -> List[str]:
    """Get all unique columns across all dataframes"""
    all_cols = set()
    for df in dataframes:
        all_cols.update(df.columns)
    return sorted(list(all_cols))

def reorder_columns_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns to put categorical/text columns first, then numeric columns"""
    # Separate columns by data type
    categorical_cols = []
    numeric_cols = []
    
    for col in df.columns:
        if col == 'source_file':
            continue  # Handle source_file separately at the end
        
        if df[col].dtype in ['object', 'string', 'category']:
            categorical_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        else:
            # For datetime or other types, treat as categorical
            categorical_cols.append(col)
    
    # Reorder: categorical first, then numeric, then source_file
    new_column_order = categorical_cols + numeric_cols
    if 'source_file' in df.columns:
        new_column_order.append('source_file')
    
    return df[new_column_order]

def combine_files_by_type(files_data: List[Dict]) -> Dict[str, pd.DataFrame]:
    """Combine files by their type (CSV, Excel) including ALL columns"""
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
            combined_df = files[0]['dataframe'].copy()
            combined_df['source_file'] = files[0]['name']
            combined_dfs[file_type] = reorder_columns_by_type(combined_df)
        else:
            # Multiple files of the same type - combine ALL columns
            dataframes = [file_data['dataframe'] for file_data in files]
            all_columns = get_all_columns(dataframes)
            
            # Combine using ALL columns (common + uncommon)
            combined_list = []
            for i, file_data in enumerate(files):
                df_copy = file_data['dataframe'].copy()
                
                # Add missing columns with NaN values
                for col in all_columns:
                    if col not in df_copy.columns:
                        df_copy[col] = np.nan
                
                # Reorder columns to match all_columns order
                df_copy = df_copy[all_columns]
                
                # Add source file column
                df_copy['source_file'] = file_data['name']
                combined_list.append(df_copy)
            
            combined_df = pd.concat(combined_list, ignore_index=True)
            combined_dfs[file_type] = reorder_columns_by_type(combined_df)
    
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
            all_cols = get_all_columns(dataframes)
            
            log_entry = {
                'file_type': file_type,
                'files_combined': len(files),
                'file_names': [f['name'] for f in files],
                'common_columns': common_cols,
                'all_columns': all_cols,
                'unique_columns': len(all_cols),
                'total_rows_before': sum(df.shape[0] for df in dataframes),
                'total_rows_after': combined_dfs[file_type].shape[0],
                'columns_after': list(combined_dfs[file_type].columns)
            }
            log.append(log_entry)
        else:
            # Single file
            log_entry = {
                'file_type': file_type,
                'files_combined': 1,
                'file_names': [files[0]['name']],
                'common_columns': list(files[0]['dataframe'].columns),
                'all_columns': list(files[0]['dataframe'].columns),
                'unique_columns': len(files[0]['dataframe'].columns),
                'total_rows_before': files[0]['dataframe'].shape[0],
                'total_rows_after': combined_dfs[file_type].shape[0],
                'columns_after': list(combined_dfs[file_type].columns)
            }
            log.append(log_entry)
    
    return log

# File upload section
st.markdown("""
<div class="upload-section">
    <h3>📁 Upload Multiple Files</h3>
    <p>Upload multiple XLS, XLSX, and CSV files to combine them with ALL columns preserved</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Choose files",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True,
    help="Upload multiple CSV, XLS, or XLSX files. Files will be cleaned and combined with ALL columns preserved."
)

if uploaded_files:
    # Process uploaded files
    files_data = []
    
    with st.spinner("Processing and cleaning uploaded files..."):
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
            
            with st.expander(f"{file_data['type']}: {file_data['name']} ({file_data['shape'][0]} rows × {file_data['shape'][1]} columns)"):
                st.markdown(f"""
                <div class="file-card">
                    <div>
                        <span class="file-type-badge {badge_class}">{file_data['type']}</span>
                        <strong>{file_data['name']}</strong>
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <small>📏 Shape: {file_data['shape'][0]} rows × {file_data['shape'][1]} columns</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display all columns in a scrollable box
                st.markdown("**All Columns:**")
                columns_text = ", ".join(file_data['columns'])
                st.markdown(f"""
                <div class="column-list">
                    {columns_text}
                </div>
                """, unsafe_allow_html=True)
        
        # Show column analysis by file type
        st.markdown("### 🔍 Column Analysis by File Type")
        
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
                all_cols = get_all_columns(dataframes)
                unique_cols = set()
                for f in files:
                    unique_cols.update(f['columns'])
                
                st.markdown(f"""
                <div class="column-info">
                    <strong>{file_type} Files ({len(files)} files)</strong><br>
                    <strong>Total unique columns:</strong> {len(all_cols)}<br>
                    <strong>Common columns ({len(common_cols)}):</strong> {', '.join(common_cols) if common_cols else 'None'}<br>
                    <strong>All columns will be preserved in final output</strong><br>
                    <small>Files: {', '.join([f['name'] for f in files])}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Show all columns in expandable section
                with st.expander(f"View all {len(all_cols)} columns for {file_type} files"):
                    columns_text = ", ".join(all_cols)
                    st.markdown(f"""
                    <div class="column-list">
                        {columns_text}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="column-info">
                    <strong>{file_type} Files (1 file)</strong><br>
                    <strong>All {len(files[0]['columns'])} columns will be preserved</strong><br>
                    <small>File: {files[0]['name']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Combine files button
        if st.button("🔗 Combine Files (ALL Columns)", type="primary"):
            with st.spinner("Combining files with ALL columns..."):
                try:
                    # Combine files by type
                    combined_dfs = combine_files_by_type(files_data)
                    
                    # Create combination log
                    combination_log = create_combination_log(files_data, combined_dfs)
                    
                    # Store results in session state
                    st.session_state.combined_df = combined_dfs
                    st.session_state.combination_log = combination_log
                    
                    st.success("✅ Files combined successfully with ALL columns preserved!")
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
                <strong>Common Columns:</strong> {len(log_entry['common_columns'])}<br>
                <strong>Total Unique Columns:</strong> {log_entry['unique_columns']}<br>
                <strong>Rows:</strong> {log_entry['total_rows_before']} → {log_entry['total_rows_after']}<br>
                <strong>Final Columns (including source_file):</strong> {len(log_entry['columns_after'])}
            </div>
            """, unsafe_allow_html=True)
            
            # Show all columns in the combined data
            with st.expander(f"View all {len(log_entry['columns_after'])} columns in combined {log_entry['file_type']} data"):
                columns_text = ", ".join(log_entry['columns_after'])
                st.markdown(f"""
                <div class="column-list">
                    {columns_text}
                </div>
                """, unsafe_allow_html=True)
    
    # Display summary stats for each combined dataframe (NO DATAFRAME DISPLAY)
    for file_type, combined_df in st.session_state.combined_df.items():
        st.markdown(f"### 📈 Combined {file_type} Data Summary")
        
        # Show basic stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows", combined_df.shape[0])
        with col2:
            st.metric("Total Columns", combined_df.shape[1])
        with col3:
            numeric_cols = combined_df.select_dtypes(include=[np.number]).shape[1]
            st.metric("Numeric Columns", numeric_cols)
        with col4:
            # Count unique source files
            unique_sources = combined_df['source_file'].nunique() if 'source_file' in combined_df.columns else 1
            st.metric("Source Files", unique_sources)
        
        # Show data types summary with categorical/text first
        with st.expander(f"📊 Column Data Types for {file_type}"):
            # Separate and count by data type categories
            categorical_cols = []
            numeric_cols = []
            other_cols = []
            
            for col in combined_df.columns:
                if col == 'source_file':
                    continue
                    
                dtype = combined_df[col].dtype
                if dtype in ['object', 'string', 'category']:
                    categorical_cols.append(col)
                elif pd.api.types.is_numeric_dtype(dtype):
                    numeric_cols.append(col)
                else:
                    other_cols.append(col)
            
            st.write(f"**📝 Categorical/Text Columns**: {len(categorical_cols)}")
            if categorical_cols:
                st.write(f"   {', '.join(categorical_cols[:10])}{'...' if len(categorical_cols) > 10 else ''}")
            
            st.write(f"**🔢 Numeric Columns**: {len(numeric_cols)}")
            if numeric_cols:
                st.write(f"   {', '.join(numeric_cols[:10])}{'...' if len(numeric_cols) > 10 else ''}")
            
            if other_cols:
                st.write(f"**📅 Other Types**: {len(other_cols)}")
                st.write(f"   {', '.join(other_cols)}")
            
            st.write(f"**📁 Source Tracking**: source_file column")
        
        # Show sample of source file distribution
        if 'source_file' in combined_df.columns:
            with st.expander(f"📁 Source File Distribution for {file_type}"):
                source_counts = combined_df['source_file'].value_counts()
                st.dataframe(source_counts.to_frame('Row Count'), use_container_width=True)
        
        # Add a prominent reset button at the top of download section
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Reset & Clear All Memory", type="secondary", use_container_width=True):
            clear_memory_and_cache()
            st.success("✅ All data cleared! Ready for new files.")
            st.rerun()
    
    st.markdown("---")
    
    # Download options
    st.subheader("💾 Download Combined Data")
    
    # Prepare download data
    if len(st.session_state.combined_df) == 1:
        # Single file type - download directly
        file_type, df_to_download = list(st.session_state.combined_df.items())[0]
        default_filename = f"combined_{file_type.lower()}_data"
    else:
        # Multiple file types - combine all into one
        all_dfs = []
        for file_type, df in st.session_state.combined_df.items():
            df_copy = df.copy()
            df_copy['data_type'] = file_type
            all_dfs.append(df_copy)
        
        df_to_download = pd.concat(all_dfs, ignore_index=True, sort=False)
        default_filename = "combined_all_data"
    
    # File naming section
    st.markdown("### 📝 Customize Download Filename")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        custom_filename = st.text_input(
            "Enter filename (without extension):",
            value=default_filename,
            help="Enter your preferred filename. The appropriate extension (.csv or .xlsx) will be added automatically.",
            placeholder="e.g., my_combined_data"
        )
    
    with col2:
        # Show preview of final filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        st.markdown("**Preview:**")
        if custom_filename.strip():
            clean_filename = custom_filename.strip().replace(" ", "_")
            preview_csv = f"{clean_filename}_{timestamp}.csv"
            preview_excel = f"{clean_filename}_{timestamp}.xlsx"
        else:
            clean_filename = default_filename
            preview_csv = f"{clean_filename}_{timestamp}.csv"
            preview_excel = f"{clean_filename}_{timestamp}.xlsx"
        
        st.markdown(f"📄 CSV: `{preview_csv}`")
        st.markdown(f"📊 Excel: `{preview_excel}`")
    
    # Validate filename
    if not custom_filename.strip():
        st.warning("⚠️ Please enter a filename")
        download_enabled = False
    else:
        # Clean filename (remove special characters, replace spaces with underscores)
        clean_filename = custom_filename.strip().replace(" ", "_")
        # Remove potentially problematic characters
        import re
        clean_filename = re.sub(r'[<>:"/\\|?*]', '', clean_filename)
        if not clean_filename:
            st.warning("⚠️ Please enter a valid filename")
            download_enabled = False
        else:
            download_enabled = True
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv_buffer = io.StringIO()
        df_to_download.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        csv_download = st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"{clean_filename}_{timestamp}.csv",
            mime="text/csv",
            help="Download combined data as CSV file with ALL columns (Memory will be cleared after download)",
            key="csv_download",
            disabled=not download_enabled
        )
        
        if csv_download:
            # Automatically clear memory immediately after download
            clear_memory_and_cache()
            st.success("✅ CSV downloaded and memory cleared successfully!")
    
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
                        'Common_Columns': len(log_entry['common_columns']),
                        'Total_Unique_Columns': log_entry['unique_columns'],
                        'Rows_Before': log_entry['total_rows_before'],
                        'Rows_After': log_entry['total_rows_after'],
                        'Final_Columns_Count': len(log_entry['columns_after'])
                    })
                
                log_df = pd.DataFrame(log_data)
                log_df.to_excel(writer, sheet_name='Combination_Log', index=False)
        
        excel_data = excel_buffer.getvalue()
        
        excel_download = st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"{clean_filename}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download combined data as Excel file with multiple sheets and ALL columns (Memory will be cleared after download)",
            key="excel_download",
            disabled=not download_enabled
        )
        
        if excel_download:
            # Automatically clear memory immediately after download
            clear_memory_and_cache()
            st.success("✅ Excel downloaded and memory cleared successfully!")

# Reset button in main area when files are uploaded (keeping the existing one too)
if st.session_state.uploaded_files_data:
    st.markdown("---")
    st.markdown("### 🔄 Start Over")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Upload New Files", type="secondary", use_container_width=True):
            clear_memory_and_cache()
            st.success("✅ Ready for new files!")
            st.rerun()

# Show features and how it works when no files are uploaded
if not uploaded_files and not st.session_state.uploaded_files_data:
    
    # How it works section
    st.subheader("ℹ️ How It Works - Enhanced Version")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Enhanced Combination Logic:**
        
        1. **Data Cleaning**: Removes empty rows and unnamed columns before merging
        
        2. **All Columns Preserved**: Combines ALL columns (common + uncommon)
        
        3. **By File Type**: Files are grouped by type (CSV, Excel)
        
        4. **Source Tracking**: A 'source_file' column tracks original files
        
        5. **Missing Data Handling**: Missing columns filled with NaN values
        
        6. **Memory Management**: Auto-clear memory on download
        """)
    
    with col2:
        st.markdown("""
        **Data Cleaning Features:**
        - Removes rows where first column is empty
        - Removes "Unnamed" columns
        - Removes completely empty rows
        - Preserves all meaningful data
        
        **Enhanced Download & Reset Features:**
        - Custom filename support
        - Manual reset functionality
        - Clean download experience (no auto-restart) with live preview
        - Automatic memory clearing on download
        - Manual reset button for fresh start
        - No auto-restart after download
        - Clean, efficient memory management
        """)
    
    st.subheader("✨ Enhanced Tool Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 Enhanced Processing:**
        - Automatic data cleaning
        - Preserve ALL columns (common + unique)
        - Remove empty/unnamed data
        - Smart column alignment
        - Detailed progress reporting
        - Memory-efficient processing
        - Custom filename support
        """)
    
    with col2:
        st.markdown("""
        **🔗 Improved Combination:**
        - No data loss (all columns preserved)
        - Clean, organized output
        - Comprehensive column analysis
        - Statistics without data display
        - Custom filename support
        - Enhanced download options
        - Automatic memory clearing on download
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔗 Enhanced File Combiner Tool v2.3 | Custom Filenames | Manual Reset | Clean Download Experience</p>
</div>
""", unsafe_allow_html=True)
