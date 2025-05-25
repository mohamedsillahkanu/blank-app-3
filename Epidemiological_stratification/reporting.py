import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# Set page config
st.set_page_config(
    page_title="Health Facility Reporting Analysis",
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
    
    .info-box {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #bbdefb;
        margin: 1rem 0;
    }
    
    .heatmap-container {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Health Facility Reporting Status Analysis</h1>
    <p>Advanced heatmap visualization for health facility reporting patterns</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def detect_admin_columns(df):
    """Detect columns that could be used as administrative levels"""
    admin_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if 'adm' in col_lower:
            admin_cols.append(col)
    return admin_cols

def validate_data(df):
    """Validate that the dataframe has required columns"""
    required_cols = ['hf_uid', 'allout', 'susp', 'test', 'conf', 'maltreat']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return False
    
    # Check if Date column exists, if not try to create it
    if 'Date' not in df.columns:
        if 'month' in df.columns and 'year' in df.columns:
            try:
                st.info("🔄 Creating Date column from month and year...")
                df['month'] = pd.to_numeric(df['month'], errors='coerce')
                df['year'] = pd.to_numeric(df['year'], errors='coerce')
                
                if df['month'].isna().any() or df['year'].isna().any():
                    st.error("❌ Invalid values found in month or year columns")
                    return False
                
                if (df['month'] < 1).any() or (df['month'] > 12).any():
                    st.error("❌ Month values must be between 1 and 12")
                    return False
                
                df['Date'] = df['year'].astype(int).astype(str) + '-' + df['month'].astype(int).astype(str).str.zfill(2)
                st.success("✅ Successfully created Date column from month and year")
            except Exception as e:
                st.error(f"❌ Error creating Date column: {str(e)}")
                return False
        elif 'year_mon' in df.columns:
            try:
                st.info("🔄 Using year_mon as Date column...")
                df['Date'] = df['year_mon'].astype(str)
                st.success("✅ Successfully used year_mon as Date column")
            except Exception as e:
                st.error(f"❌ Error using year_mon as Date: {str(e)}")
                return False
        else:
            st.error("❌ No Date, month/year, or year_mon columns found.")
            return False
    
    # Detect admin columns
    admin_cols = detect_admin_columns(df)
    if not admin_cols:
        st.info("🔄 Creating artificial ADM1 regions...")
        unique_hfs = df['hf_uid'].unique()
        n_groups = min(16, max(4, len(unique_hfs) // 10))
        
        sorted_hfs = sorted(unique_hfs)
        group_size = len(sorted_hfs) // n_groups + 1
        
        adm1_mapping = {}
        for i, hf in enumerate(sorted_hfs):
            group_num = i // group_size
            adm1_mapping[hf] = f'Region_{group_num + 1:02d}'
        
        df['adm1'] = df['hf_uid'].map(adm1_mapping)
        st.success(f"✅ Created artificial ADM1 with {n_groups} regions")
    else:
        st.success(f"✅ Detected admin columns: {', '.join(admin_cols)}")
    
    # Ensure numeric columns are numeric
    numeric_cols = ['allout', 'susp', 'test', 'conf', 'maltreat']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.success(f"✅ Validation passed! Ready for analysis with {len(df)} records")
    return True

def generate_dual_heatmaps(df, admin_col, no_report_color='pink', report_color='lightblue', 
                          main_title='Health Facility Reporting Status', legend_title='Reporting status', 
                          no_report_label='Do not report', report_label='Report'):
    """Generate dual heatmaps: All HFs and HFs with at least one record"""
    
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['Status'] = df[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0).astype(int)
    
    df_all = df.copy()
    df_with_records = df[df['Status'] == 1].copy()
    
    custom_cmap = ListedColormap([no_report_color, report_color])
    
    def create_heatmap_subplot(data, ax_list):
        if len(data) == 0:
            return
            
        admin_groups = data[admin_col].unique()
        
        for i, admin_group in enumerate(admin_groups[:16]):
            if i >= len(ax_list):
                break
                
            subset = data[data[admin_col] == admin_group]
            
            if len(subset) == 0:
                ax_list[i].axis('off')
                continue
            
            hf_order = subset.groupby('hf_uid')['Status'].sum().sort_values(ascending=False).index
            subset = subset.copy()
            subset['hf_uid'] = pd.Categorical(subset['hf_uid'], categories=hf_order, ordered=True)
            subset = subset.sort_values('hf_uid')
            
            heatmap_data = subset.pivot(index='hf_uid', columns='Date', values='Status')
            heatmap_data.fillna(0, inplace=True)
            
            if heatmap_data.empty:
                ax_list[i].axis('off')
                continue
            
            sns.heatmap(
                heatmap_data,
                cmap=custom_cmap,
                linewidths=0,
                cbar=False,
                yticklabels=len(heatmap_data) <= 20,
                annot=False,
                ax=ax_list[i]
            )
            ax_list[i].set_title(f'{admin_group}', fontsize=12, fontweight='bold')
            ax_list[i].set_xlabel('Date', fontsize=9)
            ax_list[i].tick_params(axis='x', labelrotation=90)
        
        for j in range(len(admin_groups), len(ax_list)):
            ax_list[j].axis('off')
    
    fig = plt.figure(figsize=(24, 20))
    
    axes_all = []
    for i in range(4):
        for j in range(4):
            ax = plt.subplot2grid((8, 4), (i, j))
            axes_all.append(ax)
    
    axes_with_records = []
    for i in range(4):
        for j in range(4):
            ax = plt.subplot2grid((8, 4), (i+4, j))
            axes_with_records.append(ax)
    
    create_heatmap_subplot(df_all, axes_all)
    create_heatmap_subplot(df_with_records, axes_with_records)
    
    fig.text(0.5, 0.95, f'{main_title} - All Health Facilities', 
             fontsize=16, fontweight='bold', ha='center')
    fig.text(0.5, 0.48, f'{main_title} - Health Facilities with At Least One Record', 
             fontsize=16, fontweight='bold', ha='center')
    
    legend_labels = [no_report_label, report_label]
    legend_colors = [custom_cmap(0), custom_cmap(1)]
    legend_patches = [Patch(color=color, label=label) 
                     for color, label in zip(legend_colors, legend_labels)]
    
    fig.legend(
        handles=legend_patches,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.98),
        ncol=2,
        title=legend_title,
        fontsize=12,
        title_fontsize=14
    )
    
    plt.tight_layout()
    return fig

def generate_all_hfs_sorted_heatmap(df, no_report_color='pink', report_color='lightblue', 
                                    main_title='All Health Facilities Sorted by Reporting Rate', 
                                    legend_title='Reporting status', no_report_label='Do not report', 
                                    report_label='Report'):
    """Generate a single heatmap with all HFs sorted by reporting rate"""
    
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['Status'] = df[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0).astype(int)
    
    hf_reporting_rates = df.groupby('hf_uid')['Status'].agg(['sum', 'count']).reset_index()
    hf_reporting_rates['reporting_rate'] = (hf_reporting_rates['sum'] / hf_reporting_rates['count'] * 100).round(2)
    hf_reporting_rates = hf_reporting_rates.sort_values('reporting_rate', ascending=False)
    
    hf_order = hf_reporting_rates['hf_uid'].tolist()
    
    df_sorted = df.copy()
    df_sorted['hf_uid'] = pd.Categorical(df_sorted['hf_uid'], categories=hf_order, ordered=True)
    df_sorted = df_sorted.sort_values('hf_uid')
    
    heatmap_data = df_sorted.pivot(index='hf_uid', columns='Date', values='Status')
    heatmap_data.fillna(0, inplace=True)
    
    n_hfs = len(hf_order)
    height = max(12, min(50, n_hfs * 0.3))
    width = max(16, len(heatmap_data.columns) * 0.5)
    
    custom_cmap = ListedColormap([no_report_color, report_color])
    
    fig, ax = plt.subplots(figsize=(width, height))
    
    sns.heatmap(
        heatmap_data,
        cmap=custom_cmap,
        linewidths=0.1,
        cbar=False,
        yticklabels=True,
        xticklabels=True,
        annot=False,
        ax=ax
    )
    
    ax.set_title(main_title, fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=14)
    ax.set_ylabel('Health Facility ID (Sorted by Reporting Rate: High → Low)', fontsize=14)
    
    ax.tick_params(axis='x', labelrotation=45, labelsize=10)
    ax.tick_params(axis='y', labelsize=8)
    
    legend_labels = [no_report_label, report_label]
    legend_colors = [custom_cmap(0), custom_cmap(1)]
    legend_patches = [Patch(color=color, label=label) 
                     for color, label in zip(legend_colors, legend_labels)]
    
    ax.legend(
        handles=legend_patches,
        loc='upper right',
        bbox_to_anchor=(1.15, 1),
        title=legend_title,
        fontsize=12,
        title_fontsize=14
    )
    
    for i, hf_uid in enumerate(hf_order[:min(50, len(hf_order))]):
        rate = hf_reporting_rates[hf_reporting_rates['hf_uid'] == hf_uid]['reporting_rate'].iloc[0]
        ax.text(len(heatmap_data.columns) + 0.5, i + 0.5, f'{rate}%', 
                va='center', ha='left', fontsize=8, alpha=0.8)
    
    ax.text(len(heatmap_data.columns) + 0.5, -1, 'Rate%', 
            va='center', ha='left', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    return fig, hf_reporting_rates

def create_summary_stats(df, admin_col):
    """Create summary statistics for the data"""
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['total_cases'] = df[selected_variables].sum(axis=1)
    df['has_reporting'] = (df['total_cases'] > 0).astype(int)
    
    total_hfs = df['hf_uid'].nunique()
    total_months = df['Date'].nunique()
    total_records = len(df)
    reporting_rate = (df['has_reporting'].sum() / len(df) * 100).round(2)
    
    hfs_with_records = df[df['has_reporting'] == 1]['hf_uid'].nunique()
    records_with_data = len(df[df['has_reporting'] == 1])
    
    regional_stats = df.groupby(admin_col).agg({
        'hf_uid': 'nunique',
        'has_reporting': ['sum', 'count'],
        'total_cases': 'sum'
    }).round(2)
    
    regional_stats.columns = ['Health_Facilities', 'Months_Reported', 'Total_Months', 'Total_Cases']
    regional_stats['Reporting_Rate_%'] = (regional_stats['Months_Reported'] / regional_stats['Total_Months'] * 100).round(2)
    
    regional_stats_with_records = df[df['has_reporting'] == 1].groupby(admin_col).agg({
        'hf_uid': 'nunique',
        'has_reporting': ['sum', 'count'],
        'total_cases': 'sum'
    }).round(2)
    
    if not regional_stats_with_records.empty:
        regional_stats_with_records.columns = ['HFs_With_Records', 'Active_Months', 'Total_Active_Months', 'Total_Cases_Active']
        regional_stats_with_records['Active_Rate_%'] = (regional_stats_with_records['Active_Months'] / regional_stats_with_records['Total_Active_Months'] * 100).round(2)
    else:
        regional_stats_with_records = pd.DataFrame()
    
    return {
        'total_hfs': total_hfs,
        'total_months': total_months,
        'total_records': total_records,
        'overall_reporting_rate': reporting_rate,
        'hfs_with_records': hfs_with_records,
        'records_with_data': records_with_data,
        'regional_stats': regional_stats,
        'regional_stats_with_records': regional_stats_with_records
    }

# File upload section
st.header("📁 Data Upload")

uploaded_file = st.file_uploader(
    "Upload your health facility data file",
    type=['csv', 'xlsx', 'xls'],
    help="File should contain: hf_uid, allout, susp, test, conf, maltreat, Date (or month/year)"
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("✅ File uploaded successfully!")
        st.info(f"📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        
        with st.expander("🔍 Original Data Structure (First 10 rows)"):
            st.write("**Original Columns:**")
            st.write(list(df.columns))
            st.write("**Sample Records:**")
            st.dataframe(df.head(10), use_container_width=True)
        
        if validate_data(df):
            st.session_state.df = df
            st.success("✅ Data validation passed!")
            
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")

# Sample data option
col1, col2 = st.columns([1, 1])
with col1:
    if st.session_state.df is None and st.button("📊 Use Sample Data", type="secondary"):
        np.random.seed(42)
        years = [2023, 2024]
        months = list(range(1, 13))
        hf_uids = [f'HF_{i:03d}' for i in range(1, 101)]
        
        regions = ['North', 'South', 'East', 'West']
        districts = {
            'North': ['North_A', 'North_B', 'North_C'],
            'South': ['South_A', 'South_B', 'South_C'],
            'East': ['East_A', 'East_B', 'East_C'],
            'West': ['West_A', 'West_B', 'West_C']
        }
        
        sample_data = []
        for hf in hf_uids:
            adm1 = np.random.choice(regions)
            adm2 = np.random.choice(districts[adm1])
            adm3 = f"{adm2}_{np.random.randint(1, 4)}"
            
            for year in years:
                for month in months:
                    if np.random.random() > 0.3:
                        allout = np.random.poisson(5)
                        susp = np.random.poisson(3)
                        test = np.random.poisson(4)
                        conf = np.random.poisson(2)
                        maltreat = np.random.poisson(2)
                    else:
                        allout = susp = test = conf = maltreat = 0
                    
                    date_str = f"{year}-{month:02d}"
                    
                    sample_data.append({
                        'hf_uid': hf,
                        'adm1': adm1,
                        'adm2': adm2,
                        'adm3': adm3,
                        'Date': date_str,
                        'allout': allout,
                        'susp': susp,
                        'test': test,
                        'conf': conf,
                        'maltreat': maltreat
                    })
        
        df = pd.DataFrame(sample_data)
        
        if validate_data(df):
            st.session_state.df = df
            st.success("✅ Sample data loaded with multiple administrative levels!")
            st.rerun()

# Main analysis section
if st.session_state.df is not None:
    df = st.session_state.df
    
    admin_cols = detect_admin_columns(df)
    if not admin_cols:
        admin_cols = ['adm1']
    
    st.subheader("🗺️ Administrative Level Selection")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_admin_col = st.selectbox(
            "Select Administrative Level for Analysis",
            options=admin_cols,
            index=0,
            help="Choose which administrative boundary to use for grouping"
        )
    
    with col2:
        st.info(f"**Selected:** {selected_admin_col}")
        unique_regions = df[selected_admin_col].nunique()
        st.write(f"**Number of regions:** {unique_regions}")
        if unique_regions > 16:
            st.warning("⚠️ More than 16 regions detected. Only first 16 will be displayed.")
    
    st.subheader("📋 Data Summary")
    stats = create_summary_stats(df, selected_admin_col)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>All Health Facilities</h4>
            <h2>{stats['total_hfs']}</h2>
            <p>Unique facilities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>HFs with Records</h4>
            <h2>{stats['hfs_with_records']}</h2>
            <p>Facilities with data</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Time Periods</h4>
            <h2>{stats['total_months']}</h2>
            <p>Unique months</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Overall Reporting Rate</h4>
            <h2>{stats['overall_reporting_rate']}%</h2>
            <p>All records</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.subheader("🎨 Customize Your Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎨 Color Customization**")
        no_report_color = st.color_picker("No Report Color", "#FFC0CB")
        report_color = st.color_picker("Report Color", "#ADD8E6")
    
    with col2:
        st.markdown("**📝 Text Customization**")
        main_title = st.text_input("Main Title", f"Health Facility Reporting Status by {selected_admin_col.upper()}")
        legend_title = st.text_input("Legend Title", "Reporting status")
    
    col3, col4 = st.columns(2)
    
    with col3:
        no_report_label = st.text_input("No Report Label", "Do not report")
    
    with col4:
        report_label = st.text_input("Report Label", "Report")
    
    # Analysis buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Generate Dual Heatmap Analysis", type="primary"):
            with st.spinner("Generating dual heatmap analysis..."):
                try:
                    fig = generate_dual_heatmaps(
                        df, 
                        admin_col=selected_admin_col,
                        no_report_color=no_report_color,
                        report_color=report_color,
                        main_title=main_title,
                        legend_title=legend_title,
                        no_report_label=no_report_label,
                        report_label=report_label
                    )
                    
                    st.session_state.analysis_complete = True
                    st.session_state.heatmap_fig = fig
                    st.session_state.stats = stats
                    st.session_state.selected_admin_col = selected_admin_col
                    st.session_state.analysis_type = "dual"
                    
                except Exception as e:
                    st.error(f"Error generating analysis: {str(e)}")
            
            st.success("✅ Dual heatmap analysis completed!")
            st.rerun()
    
    with col2:
        if st.button("📈 Generate All HFs Sorted Heatmap", type="secondary"):
            with st.spinner("Generating sorted heatmap..."):
                try:
                    fig, hf_rates = generate_all_hfs_sorted_heatmap(
                        df,
                        no_report_color=no_report_color,
                        report_color=report_color,
                        main_title="All Health Facilities Sorted by Reporting Rate",
                        legend_title=legend_title,
                        no_report_label=no_report_label,
                        report_label=report_label
                    )
                    
                    st.session_state.analysis_complete = True
                    st.session_state.heatmap_fig = fig
                    st.session_state.hf_reporting_rates = hf_rates
                    st.session_state.stats = stats
                    st.session_state.selected_admin_col = selected_admin_col
                    st.session_state.analysis_type = "sorted"
                    
                except Exception as e:
                    st.error(f"Error generating sorted analysis: {str(e)}")
            
            st.success("✅ Sorted heatmap analysis completed!")
            st.rerun()
    
    # Show results if analysis is complete
    if st.session_state.analysis_complete:
        analysis_type = getattr(st.session_state, 'analysis_type', 'dual')
        
        if analysis_type == "dual":
            st.subheader("📈 Dual Heatmap Analysis Results")
            
            st.markdown("""
            <div class="info-box">
                <h4>📊 Understanding the Dual Heatmaps</h4>
                <p><strong>Top Heatmap:</strong> Shows ALL health facilities in your dataset</p>
                <p><strong>Bottom Heatmap:</strong> Shows only health facilities with at least one record</p>
                <p>This comparison helps identify consistently reporting vs inactive facilities.</p>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.subheader("📈 All Health Facilities Sorted by Reporting Rate")
            
            st.markdown("""
            <div class="info-box">
                <h4>📊 Understanding the Sorted Heatmap</h4>
                <p><strong>Y-Axis:</strong> All health facilities sorted by reporting rate (highest to lowest)</p>
                <p><strong>X-Axis:</strong> Time periods showing reporting patterns</p>
                <p><strong>Right Side:</strong> Reporting rate percentage for each facility</p>
                <p>This view helps identify top performers and facilities needing attention.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if hasattr(st.session_state, 'hf_reporting_rates'):
                rates_df = st.session_state.hf_reporting_rates
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🏆 Top 10 Performing Health Facilities")
                    top_10 = rates_df.head(10)[['hf_uid', 'reporting_rate', 'sum', 'count']].copy()
                    top_10.columns = ['Health Facility', 'Reporting Rate (%)', 'Reported Months', 'Total Months']
                    st.dataframe(top_10, use_container_width=True)
                
                with col2:
                    st.markdown("### ⚠️ Bottom 10 Performing Health Facilities")
                    bottom_10 = rates_df.tail(10)[['hf_uid', 'reporting_rate', 'sum', 'count']].copy()
                    bottom_10.columns = ['Health Facility', 'Reporting Rate (%)', 'Reported Months', 'Total Months']
                    st.dataframe(bottom_10, use_container_width=True)
                
                st.markdown("### 📊 Reporting Rate Distribution")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_rate = rates_df['reporting_rate'].mean()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Average Rate</h4>
                        <h2>{avg_rate:.1f}%</h2>
                        <p>Mean reporting rate</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    median_rate = rates_df['reporting_rate'].median()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Median Rate</h4>
                        <p>50th percentile</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    high_performers = (rates_df['reporting_rate'] >= 80).sum()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>High Performers</h4>
                        <h2>{high_performers}</h2>
                        <p>≥80% reporting rate</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    low_performers = (rates_df['reporting_rate'] <= 20).sum()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Low Performers</h4>
                        <h2>{low_performers}</h2>
                        <p>≤20% reporting rate</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Show heatmaps
        st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
        st.pyplot(st.session_state.heatmap_fig)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show detailed statistics for dual analysis
        if analysis_type == "dual":
            st.write("### 📊 Regional Statistics - All Health Facilities")
            st.dataframe(st.session_state.stats['regional_stats'], use_container_width=True)
            
            if not st.session_state.stats['regional_stats_with_records'].empty:
                st.write("### 📊 Regional Statistics - Health Facilities with Records Only")
                st.dataframe(st.session_state.stats['regional_stats_with_records'], use_container_width=True)
        
        # Download section
        st.subheader("💾 Download Results")
        
        if analysis_type == "dual":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                df_with_status = df.copy()
                selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
                df_with_status['Status'] = df_with_status[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)
                df_with_status['Has_Records'] = df_with_status['Status']
                
                csv_full = io.StringIO()
                df_with_status.to_csv(csv_full, index=False)
                
                st.download_button(
                    label="📥 Download Full Dataset (CSV)",
                    data=csv_full.getvalue(),
                    file_name=f"dual_analysis_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                csv_regional = io.StringIO()
                st.session_state.stats['regional_stats'].to_csv(csv_regional)
                
                st.download_button(
                    label="📥 Download All HFs Stats (CSV)",
                    data=csv_regional.getvalue(),
                    file_name=f"all_hfs_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            with col3:
                if not st.session_state.stats['regional_stats_with_records'].empty:
                    csv_active = io.StringIO()
                    st.session_state.stats['regional_stats_with_records'].to_csv(csv_active)
                    
                    st.download_button(
                        label="📥 Download Active HFs Stats (CSV)",
                        data=csv_active.getvalue(),
                        file_name=f"active_hfs_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
        
        else:  # sorted analysis downloads
            col1, col2, col3 = st.columns(3)
            
            with col1:
                df_with_rates = df.copy()
                selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
                df_with_rates['Status'] = df_with_rates[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)
                
                if hasattr(st.session_state, 'hf_reporting_rates'):
                    rates_dict = dict(zip(st.session_state.hf_reporting_rates['hf_uid'], 
                                        st.session_state.hf_reporting_rates['reporting_rate']))
                    df_with_rates['HF_Reporting_Rate'] = df_with_rates['hf_uid'].map(rates_dict)
                
                csv_full = io.StringIO()
                df_with_rates.to_csv(csv_full, index=False)
                
                st.download_button(
                    label="📥 Download Dataset with Rates (CSV)",
                    data=csv_full.getvalue(),
                    file_name=f"sorted_analysis_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                if hasattr(st.session_state, 'hf_reporting_rates'):
                    csv_rates = io.StringIO()
                    st.session_state.hf_reporting_rates.to_csv(csv_rates, index=False)
                    
                    st.download_button(
                        label="📥 Download HF Reporting Rates (CSV)",
                        data=csv_rates.getvalue(),
                        file_name=f"hf_reporting_rates_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if hasattr(st.session_state, 'hf_reporting_rates'):
                    rates_df = st.session_state.hf_reporting_rates
                    performance_summary = pd.DataFrame({
                        'Performance_Category': [
                            'High Performers (≥80%)', 
                            'Medium Performers (20-79%)', 
                            'Low Performers (≤20%)', 
                            'Zero Performers (0%)'
                        ],
                        'Count': [
                            (rates_df['reporting_rate'] >= 80).sum(),
                            ((rates_df['reporting_rate'] >= 20) & (rates_df['reporting_rate'] < 80)).sum(),
                            ((rates_df['reporting_rate'] > 0) & (rates_df['reporting_rate'] <= 20)).sum(),
                            (rates_df['reporting_rate'] == 0).sum()
                        ],
                        'Percentage': [
                            ((rates_df['reporting_rate'] >= 80).sum() / len(rates_df) * 100).round(2),
                            (((rates_df['reporting_rate'] >= 20) & (rates_df['reporting_rate'] < 80)).sum() / len(rates_df) * 100).round(2),
                            (((rates_df['reporting_rate'] > 0) & (rates_df['reporting_rate'] <= 20)).sum() / len(rates_df) * 100).round(2),
                            ((rates_df['reporting_rate'] == 0).sum() / len(rates_df) * 100).round(2)
                        ]
                    })
                    
                    csv_summary = io.StringIO()
                    performance_summary.to_csv(csv_summary, index=False)
                    
                    st.download_button(
                        label="📥 Download Performance Summary (CSV)",
                        data=csv_summary.getvalue(),
                        file_name=f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 Enhanced Health Facility Reporting Analysis Tool | Built with Streamlit & Matplotlib</p>
    <p>Features: Administrative Level Selection • Dual Heatmap Analysis • Individual Performance Ranking • Comprehensive Statistics</p>
</div>
""", unsafe_allow_html=True)
