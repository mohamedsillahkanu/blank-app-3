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
    layout="wide"
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
    required_cols = ['hf_uid', 'month', 'year', 'allout', 'susp', 'test', 'conf', 'maltreat']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return False
    
    # Create year_month and date columns from month and year
    try:
        st.info("🔄 Creating year_mon and date columns from month and year...")
        
        # Ensure month and year are numeric
        df['month'] = pd.to_numeric(df['month'], errors='coerce')
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        # Check for invalid values
        if df['month'].isna().any() or df['year'].isna().any():
            st.error("❌ Invalid values found in month or year columns")
            return False
        
        if (df['month'] < 1).any() or (df['month'] > 12).any():
            st.error("❌ Month values must be between 1 and 12")
            return False
        
        # Create year_mon in YYYY-MM format
        df['year_mon'] = df['year'].astype(int).astype(str) + '-' + df['month'].astype(int).astype(str).str.zfill(2)
        
        # Create date column in YYYY-MM format
        df['date'] = pd.to_datetime(df['year_mon'], format='%Y-%m')
        
        st.success("✅ Successfully created year_mon and date columns from month and year")
                
    except Exception as e:
        st.error(f"❌ Error creating date columns from month and year: {str(e)}")
        return False
    
    # Use hf_uid directly (no need for hf_id)
    st.info("✅ Using hf_uid for health facility identification")
    
    # Rename maltreat to treat for consistency with existing code
    df['treat'] = df['maltreat']
    st.info("✅ Mapped maltreat to treat for analysis")
    
    # Ensure numeric columns are numeric
    numeric_cols = ['allout', 'susp', 'test', 'conf', 'treat']
    for col in numeric_cols:
        original_type = df[col].dtype
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if original_type != df[col].dtype:
            st.info(f"✅ Converted {col} to numeric (filled NaN with 0)")
    
    st.success(f"✅ All validation checks passed! Date column created with {len(df)} records")
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
                            'hf_uid': hf,
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
    
    # 3. Individual heatmaps for each method showing reporting status by HF and month
    method_heatmaps = {}
    for method in ['WHO', 'Ousmane', 'Mohamed']:
        method_data = method_results[method_results['method'] == method].copy()
        if len(method_data) > 0:
            # Convert year_month to string for proper ordering
            method_data['month_str'] = method_data['year_month'].astype(str)
            
            # Create pivot table for heatmap
            pivot_data = method_data.pivot_table(
                index='hf_uid', 
                columns='month_str', 
                values='reported', 
                fill_value=0
            )
            
            # Create heatmap
            fig_heatmap = px.imshow(
                pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                color_continuous_scale='viridis',
                title=f'{method} Method: Reporting Status by Health Facility and Month',
                labels={'x': 'Date (YYYY-MM)', 'y': 'Health Facility UID', 'color': 'Reported'},
                aspect='auto'
            )
            
            fig_heatmap.update_layout(
                height=max(400, len(pivot_data) * 20),  # Adjust height based on number of HFs
                xaxis_tickangle=45
            )
            
            # Update colorbar
            fig_heatmap.update_coloraxes(
                colorbar_title="Reporting Status",
                colorbar=dict(
                    tickvals=[0, 1],
                    ticktext=['Not Reported', 'Reported']
                )
            )
            
            method_heatmaps[method] = fig_heatmap
    
    # 4. Summary statistics table
    summary_stats = monthly_rates.groupby('method').agg({
        'reporting_rate': ['mean', 'min', 'max', 'std'],
        'included_in_denominator': ['mean', 'min', 'max'],
        'reported': 'mean'
    }).round(2)
    
    return fig1, fig2, method_heatmaps, summary_stats

# File upload section (in main area, not sidebar)
st.header("📁 Data Upload")

uploaded_file = st.file_uploader(
    "Upload your data file",
    type=['csv', 'xlsx', 'xls'],
    help="File should contain: hf_uid, month, year, allout, susp, test, conf, maltreat"
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
        
        # Show original data structure
        with st.expander("🔍 Original Data Structure (First 10 rows)"):
            st.write("**Original Columns:**")
            st.write(list(df.columns))
            st.write("**Sample Records:**")
            st.dataframe(df.head(10), use_container_width=True)
        
        # Validate data
        if validate_data(df):
            df = calculate_total_cases(df)
            st.session_state.df = df
            st.success("✅ Data validation passed!")
            
            # Show data summary
            st.subheader("📋 Data Summary")
            st.write(f"**Date range:** {df['date'].min().date()} to {df['date'].max().date()}")
            st.write(f"**Health facilities:** {df['hf_uid'].nunique()}")
            st.write(f"**Total records:** {len(df)}")
            
            # Show processed data
            with st.expander("🔍 View Processed Data (First 10 rows)"):
                display_cols = ['hf_uid', 'month', 'year', 'year_mon', 'date', 'allout', 'susp', 'test', 'conf', 'maltreat', 'total_cases']
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols].head(10), use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")

# Sample data option
col1, col2 = st.columns([1, 1])
with col1:
    if st.session_state.df is None and st.button("📊 Use Sample Data", type="secondary"):
        # Create sample data with month and year columns
        np.random.seed(42)
        years = [2023, 2024]
        months = list(range(1, 13))  # 1-12
        hf_uids = [f'HF_{i:03d}' for i in range(1, 51)]  # 50 health facilities
        
        sample_data = []
        for hf in hf_uids:
            for year in years:
                for month in months:
                    # Simulate different reporting patterns
                    if np.random.random() > 0.3:  # 70% chance of reporting
                        allout = np.random.poisson(5)
                        susp = np.random.poisson(3)
                        test = np.random.poisson(4)
                        conf = np.random.poisson(2)
                        maltreat = np.random.poisson(2)
                    else:
                        allout = susp = test = conf = maltreat = 0
                    
                    sample_data.append({
                        'hf_uid': hf,
                        'month': month,
                        'year': year,
                        'allout': allout,
                        'susp': susp,
                        'test': test,
                        'conf': conf,
                        'maltreat': maltreat
                    })
        
        df = pd.DataFrame(sample_data)
        
        # Validate and process the sample data
        if validate_data(df):
            df = calculate_total_cases(df)
            st.session_state.df = df
            st.success("✅ Sample data loaded!")
            st.rerun()

# Main content
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Debug section - show current dataframe structure
    with st.expander("🔍 Current Data Structure (First 10 rows)"):
        st.write("**Available Columns:**")
        st.write(list(df.columns))
        st.write("**Data Types:**")
        st.write(df.dtypes)
        st.write("**Sample Records:**")
        st.dataframe(df.head(10), use_container_width=True)
    
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
        fig1, fig2, method_heatmaps, summary_stats = create_visualizations(
            results['monthly_rates'], 
            results['all_results']
        )
        
        # Display main charts
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Display individual method heatmaps
        st.subheader("📊 Individual Method Analysis")
        
        for method, fig_heatmap in method_heatmaps.items():
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
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
            st.write("### Monthly Reporting Rates by Method (First 10 rows)")
            pivot_table = results['monthly_rates'].pivot(
                index='year_month', 
                columns='method', 
                values='reporting_rate'
            ).round(2)
            st.dataframe(pivot_table.head(10), use_container_width=True)
            
            # Download button for monthly rates
            csv_monthly = io.StringIO()
            pivot_table.to_csv(csv_monthly)
            st.download_button(
                label="📥 Download Monthly Rates (CSV)",
                data=csv_monthly.getvalue(),
                file_name=f"monthly_rates_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with tab2:
            st.write("### WHO Method - Detailed Results (First 10 rows)")
            st.dataframe(results['who_results'].head(10), use_container_width=True)
            
            # Download button for WHO results
            csv_who = io.StringIO()
            results['who_results'].to_csv(csv_who, index=False)
            st.download_button(
                label="📥 Download WHO Results (CSV)",
                data=csv_who.getvalue(),
                file_name=f"who_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with tab3:
            st.write("### Ousmane Method - Detailed Results (First 10 rows)")
            st.dataframe(results['ousmane_results'].head(10), use_container_width=True)
            
            # Download button for Ousmane results
            csv_ousmane = io.StringIO()
            results['ousmane_results'].to_csv(csv_ousmane, index=False)
            st.download_button(
                label="📥 Download Ousmane Results (CSV)",
                data=csv_ousmane.getvalue(),
                file_name=f"ousmane_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with tab4:
            st.write("### Mohamed Method - Detailed Results (First 10 rows)")
            st.dataframe(results['mohamed_results'].head(10), use_container_width=True)
            
            # Download button for Mohamed results
            csv_mohamed = io.StringIO()
            results['mohamed_results'].to_csv(csv_mohamed, index=False)
            st.download_button(
                label="📥 Download Mohamed Results (CSV)",
                data=csv_mohamed.getvalue(),
                file_name=f"mohamed_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        # Download section
        st.subheader("💾 Download All Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download for all results combined
            csv_all = io.StringIO()
            results['all_results'].to_csv(csv_all, index=False)
            
            st.download_button(
                label="📥 Download All Combined Results (CSV)",
                data=csv_all.getvalue(),
                file_name=f"all_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Summary statistics download
            csv_summary = io.StringIO()
            summary_df = results['monthly_rates'].groupby('method').agg({
                'reporting_rate': ['mean', 'min', 'max', 'std'],
                'included_in_denominator': ['mean', 'min', 'max'],
                'reported': ['mean', 'min', 'max']
            }).round(2)
            summary_df.to_csv(csv_summary)
            
            st.download_button(
                label="📥 Download Summary Statistics (CSV)",
                data=csv_summary.getvalue(),
                file_name=f"summary_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

else:
    # When no data is uploaded, show nothing or minimal message
    pass

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 Health Facility Reporting Rate Analysis Tool | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
