import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Set page configuration
st.set_page_config(
    page_title="Data Assembly & Management",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color theme - light blue palette (same as main dashboard)
COLORS = {
    "primary": "#1E88E5",       # Primary blue
    "secondary": "#90CAF9",     # Light blue
    "background": "#E3F2FD",    # Very light blue background
    "text": "#0D47A1",          # Dark blue text
    "accent": "#64B5F6"         # Accent blue
}

# CSS for styling
def get_css():
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {COLORS["background"]};
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {COLORS["text"]};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        /* Page title styling */
        .page-title {{
            background-color: {COLORS["primary"]};
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        /* Section cards */
        .section-card {{
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid {COLORS["primary"]};
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        /* Button styling */
        .stButton>button {{
            background-color: {COLORS["primary"]};
            color: white;
            border-radius: 5px;
            border: none;
            padding: 8px 16px;
            font-weight: bold;
            transition: background-color 0.3s;
        }}
        
        .stButton>button:hover {{
            background-color: {COLORS["text"]};
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
            margin-bottom: 20px;
            text-decoration: none;
            display: inline-block;
        }}
        
        /* Footer */
        .footer {{
            background-color: {COLORS["primary"]};
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-top: 30px;
            box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.1);
        }}
    </style>
    """

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

def load_sample_data():
    """Generate sample health data for demonstration"""
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'patient_id': range(1, n_samples + 1),
        'age': np.random.randint(18, 80, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_samples),
        'intervention_type': np.random.choice(['Treatment A', 'Treatment B', 'Control'], n_samples),
        'baseline_score': np.random.normal(50, 15, n_samples),
        'follow_up_score': np.random.normal(55, 12, n_samples),
        'comorbidities': np.random.randint(0, 5, n_samples),
        'date_enrolled': pd.date_range('2023-01-01', periods=n_samples, freq='D')[:n_samples]
    }
    
    df = pd.DataFrame(data)
    df['improvement'] = df['follow_up_score'] - df['baseline_score']
    df['success'] = (df['improvement'] > 5).astype(int)
    
    return df

def preprocess_data(df):
    """Basic data preprocessing"""
    # Handle missing values
    df = df.dropna()
    
    # Create age groups
    df['age_group'] = pd.cut(df['age'], bins=[0, 30, 50, 70, 100], 
                            labels=['18-30', '31-50', '51-70', '71+'])
    
    # Create severity categories based on baseline score
    df['severity'] = pd.cut(df['baseline_score'], 
                           bins=[0, 35, 50, 65, 100],
                           labels=['Mild', 'Moderate', 'Severe', 'Critical'])
    
    return df

def main():
    # Apply custom CSS
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # Back button at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Back to Dashboard", key="back_btn"):
            st.markdown("""
            <script>
                window.history.back();
            </script>
            """, unsafe_allow_html=True)
            st.info("Click the back button in your browser or navigate back to the main dashboard")
    
    # Page title
    title_html = f"""
    <div class="page-title">
        <h1>📊 Data Assembly & Management</h1>
        <p>Load, process, and manage datasets for epidemiological analysis</p>
    </div>
    """
    st.markdown(title_html, unsafe_allow_html=True)
    
    # Sidebar for data operations
    st.sidebar.title("Data Operations")
    
    # Data loading section
    st.sidebar.subheader("1. Load Data")
    data_source = st.sidebar.selectbox(
        "Select Data Source:",
        ["Sample Data", "Upload CSV", "Database Connection"]
    )
    
    if data_source == "Sample Data":
        if st.sidebar.button("Load Sample Data"):
            with st.spinner("Loading sample data..."):
                st.session_state.processed_data = load_sample_data()
                st.session_state.data_loaded = True
            st.sidebar.success("Sample data loaded!")
    
    elif data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            try:
                st.session_state.processed_data = pd.read_csv(uploaded_file)
                st.session_state.data_loaded = True
                st.sidebar.success("File uploaded successfully!")
            except Exception as e:
                st.sidebar.error(f"Error loading file: {str(e)}")
    
    elif data_source == "Database Connection":
        st.sidebar.info("Database connection feature coming soon...")
    
    # Data preprocessing section
    if st.session_state.data_loaded:
        st.sidebar.subheader("2. Data Processing")
        if st.sidebar.button("Preprocess Data"):
            with st.spinner("Processing data..."):
                st.session_state.processed_data = preprocess_data(st.session_state.processed_data)
            st.sidebar.success("Data preprocessed!")
    
    # Main content area
    if st.session_state.data_loaded and st.session_state.processed_data is not None:
        # Data overview section
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📋 Dataset Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", len(st.session_state.processed_data))
        with col2:
            st.metric("Total Columns", len(st.session_state.processed_data.columns))
        with col3:
            missing_values = st.session_state.processed_data.isnull().sum().sum()
            st.metric("Missing Values", missing_values)
        with col4:
            memory_usage = st.session_state.processed_data.memory_usage(deep=True).sum() / 1024**2
            st.metric("Memory Usage (MB)", f"{memory_usage:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data preview section
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("👁️ Data Preview")
        
        # Show first few rows
        st.write("**First 10 rows:**")
        st.dataframe(st.session_state.processed_data.head(10))
        
        # Show data types
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Data Types:**")
            dtype_df = pd.DataFrame({
                'Column': st.session_state.processed_data.columns,
                'Type': st.session_state.processed_data.dtypes.astype(str)
            })
            st.dataframe(dtype_df)
        
        with col2:
            st.write("**Summary Statistics:**")
            numeric_cols = st.session_state.processed_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                st.dataframe(st.session_state.processed_data[numeric_cols].describe())
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data quality section
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🔍 Data Quality Assessment")
        
        # Missing values analysis
        missing_data = st.session_state.processed_data.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        
        if len(missing_data) > 0:
            st.write("**Missing Values by Column:**")
            missing_df = pd.DataFrame({
                'Column': missing_data.index,
                'Missing Count': missing_data.values,
                'Missing %': (missing_data.values / len(st.session_state.processed_data) * 100).round(2)
            })
            st.dataframe(missing_df)
        else:
            st.success("✅ No missing values detected!")
        
        # Duplicate records check
        duplicates = st.session_state.processed_data.duplicated().sum()
        if duplicates > 0:
            st.warning(f"⚠️ Found {duplicates} duplicate records")
        else:
            st.success("✅ No duplicate records found!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data filtering and export section
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🔧 Data Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Filter Data:**")
            # Simple filtering interface
            if 'age' in st.session_state.processed_data.columns:
                age_range = st.slider(
                    "Age Range:",
                    int(st.session_state.processed_data['age'].min()),
                    int(st.session_state.processed_data['age'].max()),
                    (int(st.session_state.processed_data['age'].min()), 
                     int(st.session_state.processed_data['age'].max()))
                )
                filtered_data = st.session_state.processed_data[
                    (st.session_state.processed_data['age'] >= age_range[0]) & 
                    (st.session_state.processed_data['age'] <= age_range[1])
                ]
                st.write(f"Filtered records: {len(filtered_data)}")
        
        with col2:
            st.write("**Export Data:**")
            if st.button("Download as CSV"):
                csv = st.session_state.processed_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Welcome screen when no data is loaded
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("👋 Welcome to Data Assembly & Management")
        st.write("""
        This module helps you:
        
        **📤 Load Data:**
        - Import sample health datasets
        - Upload your own CSV files
        - Connect to databases (coming soon)
        
        **🔧 Process Data:**
        - Clean and preprocess datasets
        - Handle missing values
        - Create derived variables
        
        **📊 Analyze Data:**
        - View data quality metrics
        - Generate summary statistics
        - Filter and export data
        
        **Get started by selecting a data source from the sidebar!**
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    footer_html = f"""
    <div class="footer">
        <p>📊 Data Assembly & Management Module | SNT Health Analytics</p>
        <p>Last updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
