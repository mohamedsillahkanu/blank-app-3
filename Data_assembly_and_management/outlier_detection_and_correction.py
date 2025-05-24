import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime
from typing import List, Dict, Tuple
from scipy import stats
import gc  # For garbage collection

# Set page config
st.set_page_config(
    page_title="Advanced Outlier Detection & Correction Tool",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #8E24AA 0%, #3F51B5 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .selection-card {
        background-color: white;
        color: black;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 400px;
    }
    
    .method-card {
        background-color: white;
        color: black;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .method-badge {
        display: inline-block;
        background-color: #8E24AA;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    
    .method-badge.mean {
        background-color: #4CAF50;
    }
    
    .method-badge.median {
        background-color: #FF9800;
    }
    
    .method-badge.moving-avg {
        background-color: #3F51B5;
    }
    
    .method-badge.winsorized {
        background-color: #E91E63;
    }
    
    .outlier-stats {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9800;
        margin: 1rem 0;
    }
    
    .group-summary {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 0.5rem 0;
    }
    
    .correction-summary {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
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
        border: 2px dashed #8E24AA;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stats-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 3px solid #8E24AA;
    }
    
    .section-header {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #8E24AA;
        margin: 1rem 0;
        font-weight: bold;
    }
    
    .memory-info {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        color: #1976d2;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 Advanced Outlier Detection & Correction Tool</h1>
    <p>Group-based outlier detection with Mean, Median, Moving Average, and Winsorization methods</p>
</div>
""", unsafe_allow_html=True)

# Memory optimization functions
@st.cache_data
def optimize_dataframe_memory(df):
    """Optimize dataframe memory usage by converting data types"""
    df_optimized = df.copy()
    
    for col in df_optimized.columns:
        if df_optimized[col].dtype == 'object':
            # Try to convert to category if unique values < 50% of total
            unique_ratio = df_optimized[col].nunique() / len(df_optimized)
            if unique_ratio < 0.5:
                df_optimized[col] = df_optimized[col].astype('category')
        elif df_optimized[col].dtype in ['int64', 'int32']:
            # Downcast integers
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
        elif df_optimized[col].dtype in ['float64', 'float32']:
            # Downcast floats
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
    
    return df_optimized

def get_memory_usage(df):
    """Get memory usage information for dataframe"""
    memory_usage = df.memory_usage(deep=True).sum()
    return f"{memory_usage / 1024**2:.2f} MB"

def display_dataframe_head(df, title="Data Preview", height=300):
    """Display only the first 5 rows of dataframe with memory info"""
    st.markdown(f"**{title}** (showing first 5 rows)")
    st.markdown(f'<div class="memory-info">📊 Total rows: {len(df):,} | Memory usage: {get_memory_usage(df)}</div>', unsafe_allow_html=True)
    
    # Display only first 5 rows
    display_df = df.head(5)
    st.dataframe(display_df, use_container_width=True, height=height)
    
    if len(df) > 5:
        st.info(f"💡 Showing 5 of {len(df):,} total rows to optimize performance")

# Store groupby columns in session state for outlier analysis
if 'groupby_columns' not in st.session_state:
    st.session_state.groupby_columns = []
# Initialize session state with memory optimization
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'corrected_df' not in st.session_state:
    st.session_state.corrected_df = None
if 'outlier_results' not in st.session_state:
    st.session_state.outlier_results = {}
if 'correction_applied' not in st.session_state:
    st.session_state.correction_applied = False
if 'memory_optimized' not in st.session_state:
    st.session_state.memory_optimized = False
    st.session_state.original_df = None
if 'corrected_df' not in st.session_state:
    st.session_state.corrected_df = None
if 'outlier_results' not in st.session_state:
    st.session_state.outlier_results = {}
if 'correction_applied' not in st.session_state:
    st.session_state.correction_applied = False
if 'memory_optimized' not in st.session_state:
    st.session_state.memory_optimized = False

@st.cache_data
def read_file(uploaded_file):
    """Read uploaded file and return DataFrame with memory optimization"""
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if file_extension == 'csv':
            # Read CSV with optimizations
            df = pd.read_csv(uploaded_file, low_memory=False)
        elif file_extension in ['xls', 'xlsx']:
            # Read Excel with optimizations
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Optimize memory usage
        df_optimized = optimize_dataframe_memory(df)
        
        return df_optimized
    except Exception as e:
        st.error(f"Error reading file {uploaded_file.name}: {str(e)}")
        return None

def get_numeric_columns(df):
    """Get only numeric columns from the dataframe"""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def get_categorical_columns(df):
    """Get categorical columns suitable for grouping"""
    # Include object types and low-cardinality numeric columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Add numeric columns with low unique values (potential categorical)
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].nunique() <= 20:  # Threshold for considering as categorical
            categorical_cols.append(col)
    
    return categorical_cols

def detect_outliers_iqr(data, multiplier=1.5):
    """Detect outliers using IQR method"""
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    outliers = (data < lower_bound) | (data > upper_bound)
    return outliers, lower_bound, upper_bound

def correct_outliers_mean(data, outliers, group_data=None):
    """Replace outliers with mean"""
    corrected = data.copy()
    if group_data is not None and len(group_data.dropna()) > 0:
        replacement_value = group_data.mean()
    else:
        replacement_value = data.mean()
    
    corrected[outliers] = replacement_value
    return corrected

def correct_outliers_median(data, outliers, group_data=None):
    """Replace outliers with median"""
    corrected = data.copy()
    if group_data is not None and len(group_data.dropna()) > 0:
        replacement_value = group_data.median()
    else:
        replacement_value = data.median()
    
    corrected[outliers] = replacement_value
    return corrected

def correct_outliers_moving_average(data, outliers, window=5):
    """Replace outliers with moving average"""
    corrected = data.copy()
    moving_avg = data.rolling(window=window, center=True, min_periods=1).mean()
    corrected[outliers] = moving_avg[outliers]
    return corrected

def winsorize_data(data, limits=(0.05, 0.05)):
    """Apply Winsorization to the data"""
    from scipy.stats import mstats
    corrected = data.copy()
    non_null_mask = ~data.isna()
    
    if non_null_mask.sum() > 0:
        winsorized_values = mstats.winsorize(data.dropna(), limits=limits)
        corrected.loc[non_null_mask] = winsorized_values
    
    return corrected

@st.cache_data
def create_outlier_analysis_df(original_df, corrected_df, outlier_results, groupby_cols):
    """Create comprehensive outlier analysis dataframe for export"""
    analysis_rows = []
    
    for column, results in outlier_results.items():
        if 'group_results' in results:
            # Group-based analysis
            for group_name, group_result in results['group_results'].items():
                # Get group data
                if len(groupby_cols) == 1:
                    group_mask = original_df[groupby_cols[0]] == group_name
                else:
                    # Handle multiple groupby columns
                    group_mask = True
                    for i, col in enumerate(groupby_cols):
                        if isinstance(group_name, tuple):
                            group_mask &= (original_df[col] == group_name[i])
                        else:
                            group_mask &= (original_df[col] == group_name)
                
                group_data = original_df[group_mask][column]
                
                # Calculate bounds for this group
                outliers, lower_bound, upper_bound = detect_outliers_iqr(group_data, 1.5)
                
                # Add row for each data point in this group
                for idx in group_data.index:
                    original_value = original_df.loc[idx, column]
                    corrected_value = corrected_df.loc[idx, column]
                    is_outlier = outliers.loc[idx] if idx in outliers.index else False
                    
                    # Create group identifier
                    if len(groupby_cols) == 1:
                        group_id = f"{groupby_cols[0]}={group_name}"
                    else:
                        group_parts = [f"{col}={val}" for col, val in zip(groupby_cols, group_name)]
                        group_id = "; ".join(group_parts)
                    
                    analysis_rows.append({
                        'Row_Index': idx,
                        'Column': column,
                        'Group': group_id,
                        'Original_Value': original_value,
                        'Corrected_Value': corrected_value,
                        'Lower_Bound': lower_bound,
                        'Upper_Bound': upper_bound,
                        'Outlier_Status': 'Outlier' if is_outlier else 'Normal',
                        f'Corrected_{results["method"]}': 'Yes' if is_outlier else 'No',
                        'Detection_Method': 'IQR',
                        'Correction_Method': results['method']
                    })
        else:
            # Overall analysis (no grouping)
            data = original_df[column]
            outliers, lower_bound, upper_bound = detect_outliers_iqr(data, 1.5)
            
            for idx in data.index:
                original_value = original_df.loc[idx, column]
                corrected_value = corrected_df.loc[idx, column]
                is_outlier = outliers.loc[idx] if idx in outliers.index else False
                
                analysis_rows.append({
                    'Row_Index': idx,
                    'Column': column,
                    'Group': 'All_Data',
                    'Original_Value': original_value,
                    'Corrected_Value': corrected_value,
                    'Lower_Bound': lower_bound,
                    'Upper_Bound': upper_bound,
                    'Outlier_Status': 'Outlier' if is_outlier else 'Normal',
                    f'Corrected_{results["method"]}': 'Yes' if is_outlier else 'No',
                    'Detection_Method': 'IQR',
                    'Correction_Method': results['method']
                })
    
    return pd.DataFrame(analysis_rows)
    """Apply outlier correction within groups with memory optimization"""
    corrected_df = df.copy()
    results = {}
    
    if groupby_cols:
        # Group-based correction
        for numeric_col in numeric_cols:
            column_results = {}
            total_outliers = 0
            
            # Process groups in batches to save memory
            for group_name, group_data in df.groupby(groupby_cols):
                group_series = group_data[numeric_col]
                
                if len(group_series.dropna()) < 3:  # Skip groups with too few observations
                    continue
                
                # Detect outliers within group using IQR method
                outliers, _, _ = detect_outliers_iqr(group_series, kwargs.get('iqr_multiplier', 1.5))
                
                # Apply correction
                if correction_method == "Mean":
                    corrected_series = correct_outliers_mean(group_series, outliers, group_series)
                elif correction_method == "Median":
                    corrected_series = correct_outliers_median(group_series, outliers, group_series)
                elif correction_method == "Moving Average":
                    corrected_series = correct_outliers_moving_average(group_series, outliers, kwargs.get('window', 5))
                elif correction_method == "Winsorization":
                    corrected_series = winsorize_data(group_series, kwargs.get('limits', (0.05, 0.05)))
                
                # Update the corrected dataframe
                corrected_df.loc[group_data.index, numeric_col] = corrected_series
                
                # Store group results (only essential info to save memory)
                column_results[str(group_name)] = {
                    'outlier_count': int(outliers.sum()),
                    'group_size': len(group_series),
                    'outlier_percentage': float((outliers.sum() / len(group_series)) * 100) if len(group_series) > 0 else 0.0
                }
                total_outliers += outliers.sum()
            
            results[numeric_col] = {
                'group_results': column_results,
                'total_outliers': int(total_outliers),
                'method': correction_method,
                'detection_method': 'IQR'
            }
    else:
        # No grouping - apply to entire dataset
        for numeric_col in numeric_cols:
            data = df[numeric_col]
            
            # Detect outliers using IQR method
            outliers, _, _ = detect_outliers_iqr(data, kwargs.get('iqr_multiplier', 1.5))
            
            # Apply correction
            if correction_method == "Mean":
                corrected_data = correct_outliers_mean(data, outliers)
            elif correction_method == "Median":
                corrected_data = correct_outliers_median(data, outliers)
            elif correction_method == "Moving Average":
                corrected_data = correct_outliers_moving_average(data, outliers, kwargs.get('window', 5))
            elif correction_method == "Winsorization":
                corrected_data = winsorize_data(data, kwargs.get('limits', (0.05, 0.05)))
            
            corrected_df[numeric_col] = corrected_data
            
            results[numeric_col] = {
                'total_outliers': int(outliers.sum()),
                'outlier_percentage': float((outliers.sum() / len(data)) * 100),
                'method': correction_method,
                'detection_method': 'IQR'
            }
    
    # Force garbage collection
    gc.collect()
    
    return corrected_df, results

# File upload section
if st.session_state.df is None:
    st.markdown("""
    <div class="upload-section">
        <h3>📁 Upload Your Data File</h3>
        <p>Upload a CSV or Excel file to detect and correct outliers with group-based analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files"
    )
    
    if uploaded_file is not None:
        with st.spinner("Loading and optimizing file..."):
            df = read_file(uploaded_file)
            
        if df is not None:
            # Check if there are numeric columns
            numeric_cols = get_numeric_columns(df)
            if len(numeric_cols) == 0:
                st.error("❌ Dataset must have at least 1 numeric column to detect outliers.")
            else:
                # Store in session state
                st.session_state.df = df
                st.session_state.original_df = df.copy()
                st.session_state.memory_optimized = True
                
                # Reset state when new file is uploaded
                st.session_state.corrected_df = None
                st.session_state.outlier_results = {}
                st.session_state.correction_applied = False
                
                st.success(f"✅ File uploaded and optimized successfully!")
                
                # Show file info with memory usage
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.info(f"📊 **File:** {uploaded_file.name}")
                with col2:
                    st.info(f"📏 **Shape:** {df.shape[0]:,} rows × {df.shape[1]} columns")
                with col3:
                    st.info(f"🔢 **Numeric columns:** {len(numeric_cols)}")
                with col4:
                    st.info(f"💾 **Memory:** {get_memory_usage(df)}")
                
                st.rerun()

# Main content when file is uploaded
if st.session_state.df is not None:
    df = st.session_state.df
    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)
    
    # Reset button with memory cleanup
    if st.button("🔄 Upload New File", type="secondary"):
        # Reset everything and clean memory
        st.session_state.df = None
        st.session_state.original_df = None
        st.session_state.corrected_df = None
        st.session_state.outlier_results = {}
        st.session_state.correction_applied = False
        st.session_state.memory_optimized = False
        gc.collect()  # Force garbage collection
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
            <h3>{len(numeric_cols)}</h3>
            <p>Numeric Columns</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{len(categorical_cols)}</h3>
            <p>Grouping Options</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        missing_values = df.isnull().sum().sum()
        st.markdown(f"""
        <div class="stats-card">
            <h3>{missing_values:,}</h3>
            <p>Missing Values</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Memory usage indicator
    if st.session_state.memory_optimized:
        st.success(f"✅ Memory optimized: {get_memory_usage(df)} (showing first 5 rows for performance)")
    
    # Outlier detection and correction section
    if not st.session_state.correction_applied:
        st.subheader("🎯 Configure Outlier Detection & Correction")
        
        # Two-column layout for selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="section-header">
                📊 Step 1: Select Grouping Variables (Optional)
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="selection-card">
            """, unsafe_allow_html=True)
            
            st.markdown("**Group by columns (optional):**")
            st.markdown("Select categorical columns to group data before outlier detection")
            
            groupby_columns = st.multiselect(
                "Choose grouping columns",
                categorical_cols,
                help="Select columns to group by. Outliers will be detected within each group."
            )
            
            if groupby_columns:
                st.success(f"✅ Will analyze outliers within groups of: {', '.join(groupby_columns)}")
                
                # Show group information (first grouping variable only, 5 values)
                if len(groupby_columns) >= 1:
                    first_group_col = groupby_columns[0]
                    group_counts = df[first_group_col].value_counts()
                    st.markdown(f"**{first_group_col} - Top 5 groups:**")
                    top_5_groups = group_counts.head(5)
                    for group, count in top_5_groups.items():
                        st.write(f"• {group}: {count:,} records")
                    
                    if len(group_counts) > 5:
                        st.info(f"💡 Showing 5 of {len(group_counts):,} total groups")
                else:
                    group_counts = df.groupby(groupby_columns).size()
                    st.markdown(f"**Total groups:** {len(group_counts):,}")
                    st.markdown(f"**Average group size:** {group_counts.mean():.1f}")
            else:
                st.info("💡 No grouping selected. Outliers will be detected across the entire dataset.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="section-header">
                🔢 Step 2: Select Numeric Columns to Analyze
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="selection-card">
            """, unsafe_allow_html=True)
            
            st.markdown("**Numeric columns for outlier detection:**")
            st.markdown("Select which numeric columns to analyze and correct")
            
            selected_numeric_cols = st.multiselect(
                "Choose numeric columns",
                numeric_cols,
                default=numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols,
                help="Select the numeric columns you want to analyze for outliers"
            )
            
            if selected_numeric_cols:
                st.success(f"✅ Will analyze {len(selected_numeric_cols)} columns")
            else:
                st.warning("⚠️ Please select at least one numeric column")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Method selection
        if selected_numeric_cols:
            st.markdown("""
            <div class="section-header">
                🛠️ Step 3: Choose Detection and Correction Methods
            </div>
            """, unsafe_allow_html=True)
            
            # Detection method
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Outlier Detection Method")
                st.markdown("**IQR (Interquartile Range)**")
                st.info("Uses Q1 and Q3 quartiles to identify outliers")
                
                iqr_multiplier = st.slider(
                    "IQR multiplier",
                    min_value=1.0,
                    max_value=3.0,
                    value=1.5,
                    step=0.1,
                    help="Higher values = fewer outliers detected"
                )
                
                st.markdown(f"**Detection rule:** Values outside Q1 - {iqr_multiplier}×IQR to Q3 + {iqr_multiplier}×IQR")
            
            with col2:
                st.markdown("### Correction Method")
                correction_method = st.selectbox(
                    "Choose correction method:",
                    ["Mean", "Median", "Moving Average", "Winsorization"],
                    help="Method to replace outliers"
                )
                
                # Method-specific parameters
                if correction_method == "Moving Average":
                    window_size = st.number_input(
                        "Window size",
                        min_value=3,
                        max_value=21,
                        value=5,
                        step=2,
                        help="Number of neighboring values for averaging"
                    )
                
                elif correction_method == "Winsorization":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        lower_percentile = st.slider(
                            "Lower limit (%)",
                            min_value=1.0,
                            max_value=25.0,
                            value=5.0,
                            step=0.5,
                            help="Values below this percentile will be capped"
                        )
                    with col_b:
                        upper_percentile = st.slider(
                            "Upper limit (%)",
                            min_value=75.0,
                            max_value=99.0,
                            value=95.0,
                            step=0.5,
                            help="Values above this percentile will be capped"
                        )
            
            # Show method descriptions
            st.markdown("### 📋 Method Descriptions")
            
            method_descriptions = {
                "Mean": "Replace outliers with the mean value of the group/dataset",
                "Median": "Replace outliers with the median value of the group/dataset", 
                "Moving Average": "Replace outliers with the moving average of surrounding values",
                "Winsorization": "Cap extreme values at specified percentiles"
            }
            
            badges = {
                "Mean": "mean",
                "Median": "median", 
                "Moving Average": "moving-avg",
                "Winsorization": "winsorized"
            }
            
            st.markdown(f"""
            <div class="method-card">
                <span class="method-badge {badges[correction_method]}">🎯 {correction_method}</span>
                <p>{method_descriptions[correction_method]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Apply correction
            if st.button("🎯 Detect and Correct Outliers", type="primary"):
                with st.spinner("Detecting and correcting outliers..."):
                    try:
                        # Prepare parameters
                        kwargs = {'iqr_multiplier': iqr_multiplier}
                        
                        if correction_method == "Moving Average":
                            kwargs['window'] = window_size
                        elif correction_method == "Winsorization":
                            kwargs['limits'] = (lower_percentile/100, (100-upper_percentile)/100)
                        
                        # Store groupby columns for outlier analysis
                        st.session_state.groupby_columns = groupby_columns
                        
                        # Apply correction with memory optimization
                        corrected_df, results = apply_group_based_correction(
                            df, groupby_columns, selected_numeric_cols, 
                            correction_method, **kwargs
                        )
                        
                        # Optimize memory of corrected dataframe
                        corrected_df = optimize_dataframe_memory(corrected_df)
                        
                        # Store results
                        st.session_state.corrected_df = corrected_df
                        st.session_state.outlier_results = results
                        st.session_state.correction_applied = True
                        
                        st.success("✅ Outliers detected and corrected successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error detecting/correcting outliers: {str(e)}")

# Show results if correction has been applied
if st.session_state.correction_applied and st.session_state.corrected_df is not None:
    st.subheader("📊 Outlier Detection & Correction Results")
    
    # Summary statistics
    total_outliers = sum(
        result.get('total_outliers', 0) for result in st.session_state.outlier_results.values()
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Columns Analyzed", len(st.session_state.outlier_results))
    with col2:
        st.metric("Total Outliers Found", total_outliers)
    with col3:
        correction_method = list(st.session_state.outlier_results.values())[0]['method']
        st.metric("Correction Method", correction_method)
    
    # Detailed results summary only
    for column, results in st.session_state.outlier_results.items():
        st.markdown(f"#### Results for {column}")
        
        if 'group_results' in results:
            # Group-based results summary
            st.markdown(f"""
            <div class="group-summary">
                <strong>Group-based Analysis</strong><br>
                🎯 Method: {results['method']}<br>
                📊 Detection: IQR Method<br>
                🔢 Total outliers: {results['total_outliers']:,}<br>
                📊 Groups analyzed: {len(results['group_results']):,}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Overall results summary
            st.markdown(f"""
            <div class="correction-summary">
                <strong>Overall Analysis</strong><br>
                🎯 Method: {results['method']}<br>
                📊 Detection: IQR Method<br>
                🔢 Outliers found: {results['total_outliers']:,}<br>
                📈 Outlier rate: {results['outlier_percentage']:.2f}%
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Display corrected dataframe summary only
    st.markdown("### 📈 Dataset with Corrected Values")
    st.markdown(f"📊 **Dataset shape:** {st.session_state.corrected_df.shape[0]:,} rows × {st.session_state.corrected_df.shape[1]} columns")
    st.markdown(f"💾 **Memory usage:** {get_memory_usage(st.session_state.corrected_df)}")
    
    # Show only first 5 rows
    display_dataframe_head(st.session_state.corrected_df, "Corrected Dataset Preview", height=300)
    
    # Download section
    st.markdown("### 💾 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Corrected Dataset")
        # Direct CSV download of corrected data
        csv_buffer = io.StringIO()
        st.session_state.corrected_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Corrected Data (CSV)",
            data=csv_data,
            file_name=f"corrected_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Download complete corrected dataset as CSV"
        )
        
    with col2:
        st.markdown("#### 🎯 Outlier Analysis")
        # Create and download outlier analysis
        if st.button("📥 Prepare Outlier Analysis", type="secondary"):
            with st.spinner("Creating detailed outlier analysis..."):
                # Get groupby columns used in correction
                groupby_cols = []
                # We need to reconstruct the groupby columns from the session or make them available
                # For now, we'll create the analysis based on available results
                
                analysis_df = create_outlier_analysis_df(
                    st.session_state.original_df, 
                    st.session_state.corrected_df, 
                    st.session_state.outlier_results,
                    st.session_state.groupby_columns
                )
                
                # Convert to CSV
                analysis_csv_buffer = io.StringIO()
                analysis_df.to_csv(analysis_csv_buffer, index=False)
                analysis_csv_data = analysis_csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Outlier Analysis (CSV)",
                    data=analysis_csv_data,
                    file_name=f"outlier_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    help="Download detailed outlier analysis with bounds and correction status"
                )
                
                st.success("✅ Outlier analysis ready for download!")
                
                # Show preview of analysis structure
                st.markdown("**Analysis includes:**")
                st.write("• Row indices and original values")
                st.write("• Outlier detection bounds (lower/upper)")
                st.write("• Outlier status (Outlier/Normal)")
                st.write("• Correction status and method")
                st.write("• Group information (if applicable)")
    
    st.info("💡 **Download Info:** Corrected dataset contains cleaned data. Outlier analysis contains detailed detection and correction information.")
    
    # Button to try different correction
    if st.button("🎯 Try Different Correction", type="secondary"):
        st.session_state.correction_applied = False
        st.session_state.corrected_df = None
        st.session_state.outlier_results = {}
        gc.collect()  # Clean memory
        st.rerun()

# Show features when no file is uploaded
if st.session_state.df is None:
    
    # How it works section
    st.subheader("ℹ️ How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Advanced Outlier Detection Process:**
        
        1. **Upload Data**: CSV or Excel with numeric columns
        
        2. **Memory Optimization**: Automatic data type optimization for better performance
        
        3. **Select Groups**: Choose categorical columns for grouping (optional)
        
        4. **Choose Columns**: Select numeric columns to analyze
        
        5. **Configure Methods**: Set detection and correction parameters
        
        6. **Apply Correction**: Generate cleaned dataset with group-based analysis
        """)
    
    with col2:
        st.markdown("""
        **Memory-Efficient Features:**
        
        **🚀 Performance Optimizations:**
        - Automatic data type optimization
        - Display first 5 rows only
        - Cached processing functions
        - Memory usage monitoring
        - Garbage collection
        
        **📊 Smart Display:**
        - Progressive data loading
        - Limited Excel exports for large files
        - Real-time memory usage tracking
        """)
    
    st.subheader("✨ Correction Methods")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Statistical Methods:**
        
        <span class="method-badge mean">📊 Mean</span> Replace outliers with group/overall mean<br><br>
        
        <span class="method-badge median">📊 Median</span> Replace outliers with group/overall median<br><br>
        
        **Best for:** Simple statistical replacement within groups
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        **🔧 Advanced Methods:**
        
        <span class="method-badge moving-avg">📈 Moving Average</span> Replace with local trend patterns<br><br>
        
        <span class="method-badge winsorized">🎯 Winsorization</span> Cap values at percentile boundaries<br><br>
        
        **Best for:** Preserving data patterns and distributions
        """, unsafe_allow_html=True)
    
    st.subheader("🎯 Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏗️ Flexible Grouping:**
        - Group by any categorical column(s)
        - Automatic group size analysis
        - Group-specific outlier detection
        - Maintains group characteristics
        """)
        
        st.markdown("""
        **⚡ Performance Features:**
        - Memory usage optimization
        - Progressive data loading
        - First 5 rows display
        - Automatic data type conversion
        """)
    
    with col2:
        st.markdown("""
        **📊 Comprehensive Analysis:**
        - Before/after statistical comparison
        - Group-by-group outlier summary
        - Visual detection feedback
        - Detailed correction logging
        """)
        
        st.markdown("""
        **💾 Smart Export:**
        - Direct CSV downloads only
        - Corrected dataset export
        - Comprehensive outlier analysis
        - Outlier bounds and correction status
        """)

# Footer with memory info
st.markdown("---")
current_memory = "N/A"
if st.session_state.df is not None:
    current_memory = get_memory_usage(st.session_state.df)

st.markdown(f"""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎯 Built with Streamlit | Advanced Outlier Detection & Correction Tool v2.1 | Current Memory Usage: {current_memory}</p>
</div>
""", unsafe_allow_html=True)
