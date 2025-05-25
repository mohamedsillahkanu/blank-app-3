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
    
    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 2rem 0 1rem 0;
        text-align: center;
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
    
    .stats-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Health Facility Reporting Status Analysis</h1>
    <p>Comprehensive heatmap visualization and performance analysis</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None

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

def generate_regional_heatmap(df, admin_col, no_report_color='pink', report_color='lightblue', 
                             main_title='Health Facility Reporting Status', legend_title='Reporting status', 
                             no_report_label='Do not report', report_label='Report'):
    """Generate regional heatmap for a specific dataset"""
    
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['Status'] = df[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0).astype(int)
    
    custom_cmap = ListedColormap([no_report_color, report_color])
    admin_groups = df[admin_col].unique()[:16]  # Limit to 16 regions
    
    n_rows, n_cols = 4, 4
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 16))
    axes = axes.flatten()
    
    for i, admin_group in enumerate(admin_groups):
        subset = df[df[admin_col] == admin_group]
        
        if len(subset) == 0:
            axes[i].axis('off')
            continue
        
        hf_order = subset.groupby('hf_uid')['Status'].sum().sort_values(ascending=False).index
        subset = subset.copy()
        subset['hf_uid'] = pd.Categorical(subset['hf_uid'], categories=hf_order, ordered=True)
        subset = subset.sort_values('hf_uid')
        
        heatmap_data = subset.pivot(index='hf_uid', columns='Date', values='Status')
        heatmap_data.fillna(0, inplace=True)
        
        if heatmap_data.empty:
            axes[i].axis('off')
            continue
        
        sns.heatmap(
            heatmap_data,
            cmap=custom_cmap,
            linewidths=0,
            cbar=False,
            yticklabels=len(heatmap_data) <= 20,
            annot=False,
            ax=axes[i]
        )
        axes[i].set_title(f'{admin_group}', fontsize=12, fontweight='bold')
        axes[i].set_xlabel('Date', fontsize=10)
        axes[i].tick_params(axis='x', labelrotation=90)
    
    for j in range(len(admin_groups), len(axes)):
        axes[j].axis('off')
    
    legend_labels = [no_report_label, report_label]
    legend_colors = [custom_cmap(0), custom_cmap(1)]
    legend_patches = [Patch(color=color, label=label) 
                     for color, label in zip(legend_colors, legend_labels)]
    
    fig.legend(
        handles=legend_patches,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.95),
        ncol=2,
        title=legend_title,
        fontsize=12,
        title_fontsize=14
    )
    
    plt.suptitle(main_title, fontsize=16, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.92])
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
    
    regional_stats = df.groupby(admin_col).agg({
        'hf_uid': 'nunique',
        'has_reporting': ['sum', 'count'],
        'total_cases': 'sum'
    }).round(2)
    
    regional_stats.columns = ['Health_Facilities', 'Months_Reported', 'Total_Months', 'Total_Cases']
    regional_stats['Reporting_Rate_%'] = (regional_stats['Months_Reported'] / regional_stats['Total_Months'] * 100).round(2)
    
    return {
        'total_hfs': total_hfs,
        'total_months': total_months,
        'total_records': total_records,
        'overall_reporting_rate': reporting_rate,
        'regional_stats': regional_stats
    }

def create_top_bottom_performers(df, admin_cols_available, n=10):
    """Create enhanced top and bottom performers tables with administrative levels"""
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['Status'] = df[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0).astype(int)
    
    # Calculate reporting rates by facility
    hf_stats = df.groupby('hf_uid').agg({
        'Status': ['sum', 'count'],
        **{col: 'first' for col in admin_cols_available if col in df.columns}
    }).reset_index()
    
    # Flatten column names
    hf_stats.columns = ['hf_uid'] + ['reported_months', 'total_months'] + [col for col in admin_cols_available if col in df.columns]
    hf_stats['reporting_rate'] = (hf_stats['reported_months'] / hf_stats['total_months'] * 100).round(2)
    
    # Sort by reporting rate
    hf_stats_sorted = hf_stats.sort_values('reporting_rate', ascending=False)
    
    # Prepare columns for display
    display_cols = ['hf_uid']
    display_names = ['Health Facility ID']
    
    # Add admin columns that exist
    for admin_col in ['adm1', 'adm2', 'adm3']:
        if admin_col in df.columns:
            display_cols.append(admin_col)
            display_names.append(admin_col.upper())
    
    display_cols.extend(['reporting_rate', 'reported_months', 'total_months'])
    display_names.extend(['Reporting Rate (%)', 'Reported Months', 'Total Months'])
    
    # Get top and bottom performers
    top_performers = hf_stats_sorted.head(n)[display_cols].copy()
    bottom_performers = hf_stats_sorted.tail(n)[display_cols].copy()
    
    # Rename columns for display
    top_performers.columns = display_names
    bottom_performers.columns = display_names
    
    return top_performers, bottom_performers, hf_stats_sorted

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
            "Select Administrative Level for Regional Analysis",
            options=admin_cols,
            index=0,
            help="Choose which administrative boundary to use for regional heatmaps"
        )
    
    with col2:
        st.info(f"**Selected:** {selected_admin_col}")
        unique_regions = df[selected_admin_col].nunique()
        st.write(f"**Number of regions:** {unique_regions}")
        if unique_regions > 16:
            st.warning("⚠️ More than 16 regions detected. Only first 16 will be displayed.")
    
    st.subheader("🎨 Customize Colors and Labels")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎨 Colors**")
        no_report_color = st.color_picker("No Report Color", "#FFC0CB")
        report_color = st.color_picker("Report Color", "#ADD8E6")
    
    with col2:
        st.markdown("**📝 Labels**")
        no_report_label = st.text_input("No Report Label", "Do not report")
        report_label = st.text_input("Report Label", "Report")
        legend_title = st.text_input("Legend Title", "Reporting status")
    
    # Prepare datasets
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['total_reporting'] = df[selected_variables].sum(axis=1)
    
    df_all = df.copy()
    df_with_records = df[df['total_reporting'] > 0].copy()
    
    # =============================================================================
    # SECTION 1: REGIONAL ANALYSIS - ALL HEALTH FACILITIES
    # =============================================================================
    
    st.markdown("""
    <div class="section-header">
        <h2>📍 Section 1: Regional Analysis - All Health Facilities</h2>
        <p>Shows reporting patterns for ALL health facilities grouped by administrative regions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics for all HFs
    stats_all = create_summary_stats(df_all, selected_admin_col)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Health Facilities</h4>
            <h2>{stats_all['total_hfs']}</h2>
            <p>All facilities in dataset</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Time Periods</h4>
            <h2>{stats_all['total_months']}</h2>
            <p>Unique months</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Records</h4>
            <h2>{stats_all['total_records']:,}</h2>
            <p>Data points</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Overall Reporting Rate</h4>
            <h2>{stats_all['overall_reporting_rate']}%</h2>
            <p>All facilities</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Generate heatmap for all HFs
    if st.button("🚀 Generate Regional Heatmap - All Health Facilities", type="primary"):
        with st.spinner("Generating regional heatmap for all health facilities..."):
            try:
                fig_all = generate_regional_heatmap(
                    df_all, 
                    admin_col=selected_admin_col,
                    no_report_color=no_report_color,
                    report_color=report_color,
                    main_title=f"All Health Facilities by {selected_admin_col.upper()}",
                    legend_title=legend_title,
                    no_report_label=no_report_label,
                    report_label=report_label
                )
                
                st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
                st.pyplot(fig_all)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show regional statistics
                st.markdown('<div class="stats-container">', unsafe_allow_html=True)
                st.write("### 📊 Regional Statistics - All Health Facilities")
                st.dataframe(stats_all['regional_stats'], use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error generating analysis: {str(e)}")
    
    # =============================================================================
    # SECTION 2: REGIONAL ANALYSIS - FACILITIES WITH RECORDS ONLY
    # =============================================================================
    
    st.markdown("""
    <div class="section-header">
        <h2>📍 Section 2: Regional Analysis - Facilities with Records Only</h2>
        <p>Shows reporting patterns for health facilities that have at least one record (allout + susp + test + conf + maltreat > 0)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics for HFs with records
    if len(df_with_records) > 0:
        stats_with_records = create_summary_stats(df_with_records, selected_admin_col)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Active Health Facilities</h4>
                <h2>{stats_with_records['total_hfs']}</h2>
                <p>Facilities with records</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Time Periods</h4>
                <h2>{stats_with_records['total_months']}</h2>
                <p>Unique months</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Active Records</h4>
                <h2>{stats_with_records['total_records']:,}</h2>
                <p>Records with data</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Active Reporting Rate</h4>
                <h2>{stats_with_records['overall_reporting_rate']}%</h2>
                <p>Among active facilities</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Generate heatmap for HFs with records
        if st.button("🎯 Generate Regional Heatmap - Active Facilities Only", type="secondary"):
            with st.spinner("Generating regional heatmap for active facilities..."):
                try:
                    fig_active = generate_regional_heatmap(
                        df_with_records, 
                        admin_col=selected_admin_col,
                        no_report_color=no_report_color,
                        report_color=report_color,
                        main_title=f"Active Health Facilities by {selected_admin_col.upper()}",
                        legend_title=legend_title,
                        no_report_label=no_report_label,
                        report_label=report_label
                    )
                    
                    st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
                    st.pyplot(fig_active)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Show regional statistics
                    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
                    st.write("### 📊 Regional Statistics - Active Health Facilities")
                    st.dataframe(stats_with_records['regional_stats'], use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error generating analysis: {str(e)}")
    else:
        st.warning("⚠️ No facilities with records found in the dataset.")
    
    # =============================================================================
    # SECTION 3: INDIVIDUAL FACILITY PERFORMANCE - ALL FACILITIES
    # =============================================================================
    
    st.markdown("""
    <div class="section-header">
        <h2>🏥 Section 3: Individual Facility Performance - All Facilities Sorted</h2>
        <p>Shows ALL health facilities sorted by reporting rate (highest to lowest)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate individual performance analysis for all facilities
    if st.button("📈 Generate Individual Performance Analysis - All Facilities", type="primary"):
        with st.spinner("Generating individual facility performance analysis..."):
            try:
                fig_sorted_all, hf_rates_all = generate_all_hfs_sorted_heatmap(
                    df_all,
                    no_report_color=no_report_color,
                    report_color=report_color,
                    main_title="All Health Facilities Sorted by Reporting Rate",
                    legend_title=legend_title,
                    no_report_label=no_report_label,
                    report_label=report_label
                )
                
                st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
                st.pyplot(fig_sorted_all)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Performance distribution metrics
                st.markdown('<div class="stats-container">', unsafe_allow_html=True)
                st.markdown("### 📊 Performance Distribution - All Facilities")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_rate = hf_rates_all['reporting_rate'].mean()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Average Rate</h4>
                        <h2>{avg_rate:.1f}%</h2>
                        <p>Mean reporting rate</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    median_rate = hf_rates_all['reporting_rate'].median()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Median Rate</h4>
                        <h2>{median_rate:.1f}%</h2>
                        <p>50th percentile</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    high_performers = (hf_rates_all['reporting_rate'] >= 80).sum()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>High Performers</h4>
                        <h2>{high_performers}</h2>
                        <p>≥80% reporting rate</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    low_performers = (hf_rates_all['reporting_rate'] <= 20).sum()
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Low Performers</h4>
                        <h2>{low_performers}</h2>
                        <p>≤20% reporting rate</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Top and bottom performers with admin details
                top_performers_all, bottom_performers_all, _ = create_top_bottom_performers(df_all, admin_cols)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🏆 Top 10 Performing Health Facilities")
                    st.dataframe(top_performers_all, use_container_width=True)
                
                with col2:
                    st.markdown("### ⚠️ Bottom 10 Performing Health Facilities")
                    st.dataframe(bottom_performers_all, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error generating individual performance analysis: {str(e)}")
    
    # =============================================================================
    # SECTION 4: INDIVIDUAL FACILITY PERFORMANCE - ACTIVE FACILITIES ONLY
    # =============================================================================
    
    st.markdown("""
    <div class="section-header">
        <h2>🏥 Section 4: Individual Facility Performance - Active Facilities Only</h2>
        <p>Shows health facilities with records sorted by reporting rate (highest to lowest)</p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(df_with_records) > 0:
        # Generate individual performance analysis for active facilities
        if st.button("📈 Generate Individual Performance Analysis - Active Facilities", type="secondary"):
            with st.spinner("Generating active facility performance analysis..."):
                try:
                    fig_sorted_active, hf_rates_active = generate_all_hfs_sorted_heatmap(
                        df_with_records,
                        no_report_color=no_report_color,
                        report_color=report_color,
                        main_title="Active Health Facilities Sorted by Reporting Rate",
                        legend_title=legend_title,
                        no_report_label=no_report_label,
                        report_label=report_label
                    )
                    
                    st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
                    st.pyplot(fig_sorted_active)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Performance distribution metrics for active facilities
                    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
                    st.markdown("### 📊 Performance Distribution - Active Facilities")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        avg_rate = hf_rates_active['reporting_rate'].mean()
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Average Rate</h4>
                            <h2>{avg_rate:.1f}%</h2>
                            <p>Mean reporting rate</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        median_rate = hf_rates_active['reporting_rate'].median()
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Median Rate</h4>
                            <h2>{median_rate:.1f}%</h2>
                            <p>50th percentile</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        high_performers = (hf_rates_active['reporting_rate'] >= 80).sum()
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>High Performers</h4>
                            <h2>{high_performers}</h2>
                            <p>≥80% reporting rate</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        low_performers = (hf_rates_active['reporting_rate'] <= 20).sum()
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Low Performers</h4>
                            <h2>{low_performers}</h2>
                            <p>≤20% reporting rate</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Top and bottom performers with admin details for active facilities
                    top_performers_active, bottom_performers_active, _ = create_top_bottom_performers(df_with_records, admin_cols)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 🏆 Top 10 Performing Active Health Facilities")
                        st.dataframe(top_performers_active, use_container_width=True)
                    
                    with col2:
                        st.markdown("### ⚠️ Bottom 10 Performing Active Health Facilities")
                        st.dataframe(bottom_performers_active, use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error generating active facility performance analysis: {str(e)}")
    else:
        st.warning("⚠️ No active facilities found for individual performance analysis.")
    
    # =============================================================================
    # SECTION 5: DOWNLOAD CENTER
    # =============================================================================
    
    st.markdown("""
    <div class="section-header">
        <h2>💾 Section 5: Download Center</h2>
        <p>Download all analysis results and datasets</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 All Health Facilities Data")
        
        # Enhanced dataset with all info
        df_download_all = df_all.copy()
        df_download_all['Status'] = df_download_all[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)
        df_download_all['Has_Records'] = df_download_all['Status']
        
        # Add reporting rates for each facility
        hf_rates = df_download_all.groupby('hf_uid')['Status'].agg(['sum', 'count']).reset_index()
        hf_rates['reporting_rate'] = (hf_rates['sum'] / hf_rates['count'] * 100).round(2)
        rates_dict = dict(zip(hf_rates['hf_uid'], hf_rates['reporting_rate']))
        df_download_all['HF_Reporting_Rate'] = df_download_all['hf_uid'].map(rates_dict)
        
        csv_all = io.StringIO()
        df_download_all.to_csv(csv_all, index=False)
        
        st.download_button(
            label="📥 Download All HFs Dataset",
            data=csv_all.getvalue(),
            file_name=f"all_hfs_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("#### 📈 Active Health Facilities Data")
        
        if len(df_with_records) > 0:
            # Enhanced dataset for active facilities
            df_download_active = df_with_records.copy()
            df_download_active['Status'] = df_download_active[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)
            
            # Add reporting rates for active facilities
            hf_rates_active = df_download_active.groupby('hf_uid')['Status'].agg(['sum', 'count']).reset_index()
            hf_rates_active['reporting_rate'] = (hf_rates_active['sum'] / hf_rates_active['count'] * 100).round(2)
            rates_dict_active = dict(zip(hf_rates_active['hf_uid'], hf_rates_active['reporting_rate']))
            df_download_active['HF_Reporting_Rate'] = df_download_active['hf_uid'].map(rates_dict_active)
            
            csv_active = io.StringIO()
            df_download_active.to_csv(csv_active, index=False)
            
            st.download_button(
                label="📥 Download Active HFs Dataset",
                data=csv_active.getvalue(),
                file_name=f"active_hfs_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.write("No active facilities to download")
    
    with col3:
        st.markdown("#### 📋 Summary Reports")
        
        # Create comprehensive summary report
        summary_data = []
        
        # Overall statistics
        stats_all = create_summary_stats(df_all, selected_admin_col)
        summary_data.append({
            'Category': 'All Health Facilities',
            'Total_HFs': stats_all['total_hfs'],
            'Total_Records': stats_all['total_records'],
            'Reporting_Rate_%': stats_all['overall_reporting_rate'],
            'Time_Periods': stats_all['total_months']
        })
        
        if len(df_with_records) > 0:
            stats_active = create_summary_stats(df_with_records, selected_admin_col)
            summary_data.append({
                'Category': 'Active Health Facilities',
                'Total_HFs': stats_active['total_hfs'],
                'Total_Records': stats_active['total_records'],
                'Reporting_Rate_%': stats_active['overall_reporting_rate'],
                'Time_Periods': stats_active['total_months']
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        csv_summary = io.StringIO()
        summary_df.to_csv(csv_summary, index=False)
        
        st.download_button(
            label="📥 Download Summary Report",
            data=csv_summary.getvalue(),
            file_name=f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 Enhanced Health Facility Reporting Analysis Tool | Built with Streamlit & Matplotlib</p>
    <p>Features: Multi-Section Analysis • Regional & Individual Views • Administrative Level Selection • Comprehensive Statistics • Enhanced Performance Tables</p>
</div>
""", unsafe_allow_html=True)
