import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page config
st.set_page_config(
    page_title="Reporting Rate Analysis Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
    }
    
    .method-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-top: 3px solid #4CAF50;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #bbdefb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Health Facility Reporting Rate Analysis</h1>
    <p>Advanced reporting rate calculation using WHO, Ousmane, and Mohamed methods</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = {}

def validate_data(df):
    """Validate that the dataframe has required columns"""
    required_cols = ['hf_id', 'date', 'allout', 'susp', 'test', 'conf', 'treat']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return False
    
    # Convert date column to datetime
    try:
        df['date'] = pd.to_datetime(df['date'])
    except:
        st.error("Could not convert 'date' column to datetime format")
        return False
    
    # Ensure numeric columns are numeric
    numeric_cols = ['allout', 'susp', 'test', 'conf', 'treat']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return True

def calculate_total_cases(df):
    """Calculate total cases and determine if reporting"""
    df['total_cases'] = df['allout'] + df['susp'] + df['test'] + df['conf'] + df['treat']
    df['is_reporting'] = df['total_cases'] > 0
    return df

def method_who(df):
    """
    WHO Method: HF becomes active from first date when total > 0,
    and remains in denominator for all subsequent months
    """
    results = []
    
    # Get unique health facilities
    hf_list = df['hf_uid'].unique()
    
    # Get all unique months in the dataset
    df['year_month'] = df['date'].dt.to_period('M')
    all_months = sorted(df['year_month'].unique())
    
    for hf in hf_list:
        hf_data = df[df['hf_uid'] == hf].copy()
        hf_data = hf_data.sort_values('date')
        
        # Find first active date (when total > 0)
        active_records = hf_data[hf_data['total_cases'] > 0]
        
        if len(active_records) > 0:
            first_active_date = active_records.iloc[0]['date']
            first_active_month = active_records.iloc[0]['year_month']
            
            # For each month from first active onwards
            for month in all_months:
                if month >= first_active_month:
                    # Check if HF reported in this month
                    month_data = hf_data[hf_data['year_month'] == month]
                    
                    if len(month_data) > 0:
                        reported = month_data['is_reporting'].any()
                    else:
                        reported = False
                    
                    results.append({
                        'hf_uid': hf,
                        'year_month': month,
                        'method': 'WHO',
                        'included_in_denominator': True,
                        'reported': reported,
                        'first_active_date': first_active_date
                    })
    
    return pd.DataFrame(results)

def method_ousmane(df):
    """
    Ousmane Method: HF is inactive if it doesn't report for 6 consecutive months
    including current month
    """
    results = []
    
    # Get unique health facilities
    hf_list = df['hf_uid'].unique()
    
    # Get all unique months in the dataset
    df['year_month'] = df['date'].dt.to_period('M')
    all_months = sorted(df['year_month'].unique())
    
    for hf in hf_list:
        hf_data = df[df['hf_uid'] == hf].copy()
        hf_data = hf_data.sort_values('date')
        
        # Create a complete month series for this HF
        hf_months = {}
        for month in all_months:
            month_data = hf_data[hf_data['year_month'] == month]
            if len(month_data) > 0:
                hf_months[month] = month_data['is_reporting'].any()
            else:
                hf_months[month] = False
        
        # Check each month for 6 consecutive non-reporting periods
        for i, month in enumerate(all_months):
            # Look at current month and previous 5 months (total 6 months)
            if i >= 5:  # Need at least 6 months of data
                last_6_months = all_months[i-5:i+1]
                reporting_status = [hf_months.get(m, False) for m in last_6_months]
                
                # If all 6 months show no reporting, HF is inactive
                if not any(reporting_status):
                    included = False
                else:
                    included = True
                
                reported = hf_months.get(month, False)
                
                results.append({
                    'hf_uid': hf,
                    'year_month': month,
                    'method': 'Ousmane',
                    'included_in_denominator': included,
                    'reported': reported,
                    'consecutive_non_reporting': not any(reporting_status)
                })
            else:
                # For first 5 months, include all HFs
                reported = hf_months.get(month, False)
                results.append({
                    'hf_uid': hf,
                    'year_month': month,
                    'method': 'Ousmane',
                    'included_in_denominator': True,
                    'reported': reported,
                    'consecutive_non_reporting': False
                })
    
    return pd.DataFrame(results)

def method_mohamed(df):
    """
    Mohamed Method: Exclude HFs with <25% reporting rate since first report,
    then include from first report onwards
    """
    results = []
    
    # Get unique health facilities
    hf_list = df['hf_uid'].unique()
    
    # Get all unique months in the dataset
    df['year_month'] = df['date'].dt.to_period('M')
    all_months = sorted(df['year_month'].unique())
    max_date = df['date'].max()
    
    for hf in hf_list:
        hf_data = df[df['hf_uid'] == hf].copy()
        hf_data = hf_data.sort_values('date')
        
        # Find first reporting date
        reporting_records = hf_data[hf_data['is_reporting'] == True]
        
        if len(reporting_records) > 0:
            first_report_date = reporting_records.iloc[0]['date']
            first_report_month = reporting_records.iloc[0]['year_month']
            
            # Calculate reporting rate from first report to max date
            months_since_first = []
            reports_since_first = []
            
            for month in all_months:
                if month >= first_report_month:
                    months_since_first.append(month)
                    month_data = hf_data[hf_data['year_month'] == month]
                    if len(month_data) > 0:
                        reports_since_first.append(month_data['is_reporting'].any())
                    else:
                        reports_since_first.append(False)
            
            # Calculate overall reporting rate
            if len(months_since_first) > 0:
                reporting_rate = sum(reports_since_first) / len(months_since_first)
                include_hf = reporting_rate >= 0.25
            else:
                include_hf = False
            
            # If HF qualifies, include from first report onwards
            if include_hf:
                for month in all_months:
                    if month >= first_report_month:
                        month_data = hf_data[hf_data['year_month'] == month]
                        
                        if len(month_data) > 0:
                            reported = month_data['is_reporting'].any()
                        else:
                            reported = False
                        
                        results.append({
                            'hf_id': hf,
                            'year_month': month,
                            'method': 'Mohamed',
                            'included_in_denominator': True,
                            'reported': reported,
                            'overall_reporting_rate': reporting_rate,
                            'first_report_date': first_report_date
                        })
    
    return pd.DataFrame(results)

def calculate_reporting_rates(method_results):
    """Calculate monthly reporting rates for each method"""
    monthly_rates = method_results.groupby(['method', 'year_month']).agg({
        'included_in_denominator': 'sum',
        'reported': 'sum'
    }).reset_index()
    
    monthly_rates['reporting_rate'] = (monthly_rates['reported'] / 
                                     monthly_rates['included_in_denominator'] * 100).round(2)
    
    return monthly_rates

def create_visualizations(monthly_rates, method_results):
    """Create visualizations for the reporting rates"""
    
    # Convert period to string for plotting
    monthly_rates['month_str'] = monthly_rates['year_month'].astype(str)
    
    # 1. Line chart comparing all three methods
    fig1 = px.line(monthly_rates, 
                   x='month_str', 
                   y='reporting_rate', 
                   color='method',
                   title='Reporting Rates Comparison: WHO vs Ousmane vs Mohamed Methods',
                   labels={'month_str': 'Month', 'reporting_rate': 'Reporting Rate (%)'})
    
    fig1.update_layout(
        xaxis_tickangle=45,
        height=500,
        showlegend=True
    )
    
    # 2. Bar chart showing denominators
    fig2 = px.bar(monthly_rates, 
                  x='month_str', 
                  y='included_in_denominator', 
                  color='method',
                  title='Number of Health Facilities in Denominator by Method',
                  labels={'month_str': 'Month', 'included_in_denominator': 'Number of HFs'},
                  barmode='group')
    
    fig2.update_layout(
        xaxis_tickangle=45,
        height=500
    )
    
    # 3. Summary statistics table
    summary_stats = monthly_rates.groupby('method').agg({
        'reporting_rate': ['mean', 'min', 'max', 'std'],
        'included_in_denominator': ['mean', 'min', 'max'],
        'reported': 'mean'
    }).round(2)
    
    return fig1, fig2, summary_stats

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Data Upload")
    
    uploaded_file = st.file_uploader(
        "Upload your data file",
        type=['csv', 'xlsx', 'xls'],
        help="File should contain: hf_id, date, allout, susp, test, conf, treat"
    )
    
    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success("✅ File uploaded successfully!")
            st.info(f"📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Validate data
            if validate_data(df):
                df = calculate_total_cases(df)
                st.session_state.df = df
                st.success("✅ Data validation passed!")
                
                # Show data summary
                st.subheader("📋 Data Summary")
                st.write(f"**Date range:** {df['date'].min().date()} to {df['date'].max().date()}")
                st.write(f"**Health facilities:** {df['hf_id'].nunique()}")
                st.write(f"**Total records:** {len(df)}")
                
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    # Sample data option
    if st.session_state.df is None and st.button("📊 Use Sample Data"):
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', '2024-12-31', freq='M')
        hf_ids = [f'HF_{i:03d}' for i in range(1, 51)]  # 50 health facilities
        
        sample_data = []
        for hf in hf_ids:
            for date in dates:
                # Simulate different reporting patterns
                if np.random.random() > 0.3:  # 70% chance of reporting
                    allout = np.random.poisson(5)
                    susp = np.random.poisson(3)
                    test = np.random.poisson(4)
                    conf = np.random.poisson(2)
                    treat = np.random.poisson(2)
                else:
                    allout = susp = test = conf = treat = 0
                
                sample_data.append({
                    'hf_uid': hf,
                    'date': date,
                    'allout': allout,
                    'susp': susp,
                    'test': test,
                    'conf': conf,
                    'treat': treat
                })
        
        df = pd.DataFrame(sample_data)
        df = calculate_total_cases(df)
        st.session_state.df = df
        st.success("✅ Sample data loaded!")
        st.rerun()

# Main content
if st.session_state.df is not None:
    df = st.session_state.df
    
    st.subheader("🔍 Method Descriptions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="method-card">
            <h4>🟢 WHO Method</h4>
            <p>Health facility becomes active from the first date when total cases > 0 and remains in denominator for all subsequent months.</p>
            <ul>
                <li>Include from first reporting onwards</li>
                <li>Never exclude once active</li>
                <li>Conservative approach</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="method-card">
            <h4>🟡 Ousmane Method</h4>
            <p>Health facility is excluded if it doesn't report for 6 consecutive months including the current month.</p>
            <ul>
                <li>6-month sliding window</li>
                <li>Dynamic inclusion/exclusion</li>
                <li>Responsive to inactivity</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="method-card">
            <h4>🔵 Mohamed Method</h4>
            <p>Exclude health facilities with <25% reporting rate since first report, then include active ones from first report onwards.</p>
            <ul>
                <li>Quality-based filtering</li>
                <li>Overall performance assessment</li>
                <li>Minimum 25% threshold</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Analysis button
    if st.button("🚀 Run Analysis", type="primary"):
        with st.spinner("Analyzing reporting rates using all three methods..."):
            
            # Run all three methods
            who_results = method_who(df)
            ousmane_results = method_ousmane(df)
            mohamed_results = method_mohamed(df)
            
            # Combine results
            all_results = pd.concat([who_results, ousmane_results, mohamed_results], 
                                  ignore_index=True)
            
            # Calculate monthly reporting rates
            monthly_rates = calculate_reporting_rates(all_results)
            
            # Store results
            st.session_state.results = {
                'all_results': all_results,
                'monthly_rates': monthly_rates,
                'who_results': who_results,
                'ousmane_results': ousmane_results,
                'mohamed_results': mohamed_results
            }
            st.session_state.analysis_complete = True
        
        st.success("✅ Analysis completed!")
        st.rerun()
    
    # Show results if analysis is complete
    if st.session_state.analysis_complete and st.session_state.results:
        results = st.session_state.results
        
        st.subheader("📈 Analysis Results")
        
        # Create and display visualizations
        fig1, fig2, summary_stats = create_visualizations(
            results['monthly_rates'], 
            results['all_results']
        )
        
        # Display charts
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        # Calculate overall stats for each method
        method_stats = results['monthly_rates'].groupby('method').agg({
            'reporting_rate': 'mean',
            'included_in_denominator': 'mean',
            'reported': 'mean'
        }).round(2)
        
        methods = ['WHO', 'Ousmane', 'Mohamed']
        colors = ['#4CAF50', '#FF9800', '#2196F3']
        
        for i, method in enumerate(methods):
            with [col1, col2, col3][i]:
                if method in method_stats.index:
                    avg_rate = method_stats.loc[method, 'reporting_rate']
                    avg_denom = method_stats.loc[method, 'included_in_denominator']
                    avg_reported = method_stats.loc[method, 'reported']
                    
                    st.markdown(f"""
                    <div class="metric-card" style="border-top-color: {colors[i]};">
                        <h4>{method} Method</h4>
                        <h2>{avg_rate:.1f}%</h2>
                        <p>Average Reporting Rate</p>
                        <small>Avg Denominator: {avg_denom:.0f} HFs<br>
                        Avg Reporting: {avg_reported:.0f} HFs</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Detailed results tables
        st.subheader("📋 Detailed Results")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Monthly Rates", "WHO Details", "Ousmane Details", "Mohamed Details"])
        
        with tab1:
            st.write("### Monthly Reporting Rates by Method")
            pivot_table = results['monthly_rates'].pivot(
                index='year_month', 
                columns='method', 
                values='reporting_rate'
            ).round(2)
            st.dataframe(pivot_table, use_container_width=True)
        
        with tab2:
            st.write("### WHO Method - Detailed Results")
            st.dataframe(results['who_results'], use_container_width=True)
        
        with tab3:
            st.write("### Ousmane Method - Detailed Results")
            st.dataframe(results['ousmane_results'], use_container_width=True)
        
        with tab4:
            st.write("### Mohamed Method - Detailed Results")
            st.dataframe(results['mohamed_results'], use_container_width=True)
        
        # Download section
        st.subheader("💾 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download
            csv_buffer = io.StringIO()
            results['monthly_rates'].to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Monthly Rates (CSV)",
                data=csv_data,
                file_name=f"reporting_rates_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel download with all results
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                results['monthly_rates'].to_excel(writer, sheet_name='Monthly Rates', index=False)
                results['who_results'].to_excel(writer, sheet_name='WHO Method', index=False)
                results['ousmane_results'].to_excel(writer, sheet_name='Ousmane Method', index=False)
                results['mohamed_results'].to_excel(writer, sheet_name='Mohamed Method', index=False)
                
                # Add summary sheet
                summary_df = results['monthly_rates'].groupby('method').agg({
                    'reporting_rate': ['mean', 'min', 'max', 'std'],
                    'included_in_denominator': ['mean', 'min', 'max'],
                    'reported': ['mean', 'min', 'max']
                }).round(2)
                summary_df.to_excel(writer, sheet_name='Summary Statistics')
            
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📥 Download All Results (Excel)",
                data=excel_data,
                file_name=f"reporting_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    # Show instructions when no data is uploaded
    st.markdown("""
    <div class="info-box">
        <h3>📋 Getting Started</h3>
        <p>Upload your health facility data file to begin the reporting rate analysis.</p>
        
        <h4>Required Columns:</h4>
        <ul>
            <li><strong>hf_id:</strong> Health facility identifier</li>
            <li><strong>date:</strong> Date of the report</li>
            <li><strong>allout:</strong> All-out cases</li>
            <li><strong>susp:</strong> Suspected cases</li>
            <li><strong>test:</strong> Test cases</li>
            <li><strong>conf:</strong> Confirmed cases</li>
            <li><strong>treat:</strong> Treatment cases</li>
        </ul>
        
        <p>The tool will calculate reporting rates using three different methods and provide comprehensive analysis and visualizations.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 Health Facility Reporting Rate Analysis Tool | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
