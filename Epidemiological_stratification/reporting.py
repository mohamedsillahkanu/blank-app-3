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
    
    .feature-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Health Facility Reporting Status Analysis</h1>
    <p>Advanced heatmap visualization for health facility reporting patterns by region</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

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
            st.error("❌ No Date, month/year, or year_mon columns found. Please ensure your data has date information.")
            return False
    
    # Check if adm1 column exists, if not create artificial regions
    if 'adm1' not in df.columns:
        st.info("🔄 Creating artificial ADM1 regions for visualization...")
        unique_hfs = df['hf_uid'].unique()
        n_groups = min(16, max(4, len(unique_hfs) // 10))
        
        sorted_hfs = sorted(unique_hfs)
        group_size = len(sorted_hfs) // n_groups + 1
        
        adm1_mapping = {}
        for i, hf in enumerate(sorted_hfs):
            group_num = i // group_size
            adm1_mapping[hf] = f'Region_{group_num + 1:02d}'
        
        df['adm1'] = df['hf_uid'].map(adm1_mapping)
        st.success(f"✅ Created {n_groups} artificial ADM1 regions")
    
    # Ensure numeric columns are numeric
    numeric_cols = ['allout', 'susp', 'test', 'conf', 'maltreat']
    for col in numeric_cols:
        original_type = df[col].dtype
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if original_type != df[col].dtype:
            st.info(f"✅ Converted {col} to numeric (filled NaN with 0)")
    
    st.success(f"✅ All validation checks passed! Ready for analysis with {len(df)} records")
    return True

def generate_heatmaps(df, no_report_color='pink', report_color='lightblue', main_title='Health Facility Reporting Status by ADM1', legend_title='Reporting status', no_report_label='Do not report', report_label='Report'):
    """Generate heatmaps showing reporting status by ADM1 region with customizable colors and titles"""
    # Define the specific variables we want to analyze
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    
    df['Status'] = df[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0).astype(int)
    
    custom_cmap = ListedColormap([no_report_color, report_color])
    adm1_groups = df['adm1'].unique()
    
    n_rows, n_cols = 4, 4
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 20))
    axes = axes.flatten()
    
    for i, adm1 in enumerate(adm1_groups):
        subset = df[df['adm1'] == adm1]
        
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
            yticklabels=len(heatmap_data) <= 20,  # Show labels only if not too many
            annot=False,
            ax=axes[i]
        )
        axes[i].set_title(f'{adm1}', fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Date', fontsize=10)
        axes[i].tick_params(axis='x', labelrotation=90)
    
    for j in range(len(adm1_groups), len(axes)):
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
    
    plt.suptitle(main_title, fontsize=18, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    return fig

def create_summary_stats(df):
    """Create summary statistics for the data"""
    selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
    df['total_cases'] = df[selected_variables].sum(axis=1)
    df['has_reporting'] = (df['total_cases'] > 0).astype(int)
    
    # Overall statistics
    total_hfs = df['hf_uid'].nunique()
    total_months = df['Date'].nunique()
    total_records = len(df)
    reporting_rate = (df['has_reporting'].sum() / len(df) * 100).round(2)
    
    # Regional statistics
    regional_stats = df.groupby('adm1').agg({
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

# File upload section
st.header("📁 Data Upload")

uploaded_file = st.file_uploader(
    "Upload your health facility data file",
    type=['csv', 'xlsx', 'xls'],
    help="File should contain: hf_uid, allout, susp, test, conf, maltreat, Date (or month/year)"
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
            st.session_state.df = df
            st.success("✅ Data validation passed!")
            
            # Show data summary
            st.subheader("📋 Data Summary")
            stats = create_summary_stats(df)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Health Facilities</h4>
                    <h2>{stats['total_hfs']}</h2>
                    <p>Unique facilities</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Time Periods</h4>
                    <h2>{stats['total_months']}</h2>
                    <p>Unique months</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Total Records</h4>
                    <h2>{stats['total_records']:,}</h2>
                    <p>Data points</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Reporting Rate</h4>
                    <h2>{stats['overall_reporting_rate']}%</h2>
                    <p>Overall rate</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Show processed data
            with st.expander("🔍 View Processed Data (First 10 rows)"):
                display_cols = ['hf_uid', 'adm1', 'Date', 'allout', 'susp', 'test', 'conf', 'maltreat']
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols].head(10), use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")



# Main analysis section
if st.session_state.df is not None:
    df = st.session_state.df
    

    
    # Interactive customization options
    st.write("### 🎯 Visualization Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎨 Color Customization**")
        no_report_color = st.color_picker("No Report Color", "#FFC0CB", help="Color for facilities that don't report")
        report_color = st.color_picker("Report Color", "#ADD8E6", help="Color for facilities that do report")
    
    with col2:
        st.markdown("**📝 Text Customization**")
        main_title = st.text_input("Main Title", "Health Facility Reporting Status by ADM1", help="Title for the entire heatmap")
        legend_title = st.text_input("Legend Title", "Reporting status", help="Title for the legend")
    
    col3, col4 = st.columns(2)
    
    with col3:
        no_report_label = st.text_input("No Report Label", "Do not report", help="Label for non-reporting facilities")
    
    with col4:
        report_label = st.text_input("Report Label", "Report", help="Label for reporting facilities")
    
    # Color preview
    st.write("### 🎨 Color Preview")
    col_prev1, col_prev2, col_prev3 = st.columns(3)
    
    with col_prev1:
        st.markdown(f"""
        <div style="background-color: {no_report_color}; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0;">
            <strong>{no_report_label}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col_prev2:
        st.markdown(f"""
        <div style="background-color: #f0f0f0; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0; border: 2px dashed #ccc;">
            <strong>VS</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col_prev3:
        st.markdown(f"""
        <div style="background-color: {report_color}; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0;">
            <strong>{report_label}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    
    if st.button("🚀 Generate Customized Analysis", type="primary"):
        with st.spinner("Generating your customized reporting analysis..."):
            try:
                # Generate heatmap with custom parameters
                fig = generate_heatmaps(
                    df, 
                    no_report_color=no_report_color,
                    report_color=report_color,
                    main_title=main_title,
                    legend_title=legend_title,
                    no_report_label=no_report_label,
                    report_label=report_label
                )
                
                # Generate statistics
                stats = create_summary_stats(df)
                
                st.session_state.analysis_complete = True
                st.session_state.heatmap_fig = fig
                st.session_state.stats = stats
                st.session_state.custom_settings = {
                    'no_report_color': no_report_color,
                    'report_color': report_color,
                    'main_title': main_title,
                    'legend_title': legend_title,
                    'no_report_label': no_report_label,
                    'report_label': report_label
                }
                
            except Exception as e:
                st.error(f"Error generating analysis: {str(e)}")
        
        st.success("✅ Customized analysis completed!")
        st.rerun()
    
    # Show results if analysis is complete
    if st.session_state.analysis_complete:
        st.subheader("📈 Your Customized Analysis Results")
        
        # Show current settings
        if hasattr(st.session_state, 'custom_settings'):
            settings = st.session_state.custom_settings
            st.markdown(f"""
            <div class="feature-highlight">
                <h4>🎨 Current Visualization Settings</h4>
                <p><strong>Title:</strong> {settings['main_title']}</p>
                <p><strong>Legend:</strong> {settings['legend_title']}</p>
                <p><strong>Labels:</strong> {settings['no_report_label']} vs {settings['report_label']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show heatmap
        st.write("### 🗺️ Interactive Reporting Status Heatmap")
        st.pyplot(st.session_state.heatmap_fig)
        
        # Quick regeneration options
        st.write("### 🔄 Quick Style Changes")
        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
        
        with quick_col1:
            if st.button("🌸 Classic Pink/Blue", help="Traditional pink and light blue colors"):
                st.session_state.quick_regen = {
                    'no_report_color': '#FFC0CB',
                    'report_color': '#ADD8E6',
                    'main_title': 'Health Facility Reporting Status by ADM1',
                    'legend_title': 'Reporting status',
                    'no_report_label': 'Do not report',
                    'report_label': 'Report'
                }
                st.rerun()
        
        with quick_col2:
            if st.button("🔥 Heat Colors", help="Red for no report, green for report"):
                st.session_state.quick_regen = {
                    'no_report_color': '#FF6B6B',
                    'report_color': '#4ECDC4',
                    'main_title': 'Facility Reporting Heat Map',
                    'legend_title': 'Status',
                    'no_report_label': 'No Activity',
                    'report_label': 'Active'
                }
                st.rerun()
        
        with quick_col3:
            if st.button("🌊 Ocean Theme", help="Deep blue theme"):
                st.session_state.quick_regen = {
                    'no_report_color': '#E8F4FD',
                    'report_color': '#1E3A8A',
                    'main_title': 'Reporting Ocean: Facility Status Depths',
                    'legend_title': 'Activity Level',
                    'no_report_label': 'Shallow',
                    'report_label': 'Deep'
                }
                st.rerun()
        
        with quick_col4:
            if st.button("🍂 Autumn Theme", help="Warm autumn colors"):
                st.session_state.quick_regen = {
                    'no_report_color': '#FFF8DC',
                    'report_color': '#D2691E',
                    'main_title': 'Autumn Reporting Landscape',
                    'legend_title': 'Harvest Status',
                    'no_report_label': 'Dormant',
                    'report_label': 'Harvesting'
                }
                st.rerun()
        
        # Handle quick regeneration
        if hasattr(st.session_state, 'quick_regen'):
            with st.spinner("Applying new theme..."):
                settings = st.session_state.quick_regen
                fig = generate_heatmaps(
                    df,
                    no_report_color=settings['no_report_color'],
                    report_color=settings['report_color'],
                    main_title=settings['main_title'],
                    legend_title=settings['legend_title'],
                    no_report_label=settings['no_report_label'],
                    report_label=settings['report_label']
                )
                st.session_state.heatmap_fig = fig
                st.session_state.custom_settings = settings
                del st.session_state.quick_regen
                st.rerun()
        
        # Add celebration button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎉 Celebrate Results!", type="secondary"):
                st.balloons()
                st.snow()
        
        
        # Download section
        st.subheader("💾 Download Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Full dataset download
            df_with_status = df.copy()
            selected_variables = ['allout', 'susp', 'test', 'conf', 'maltreat']
            df_with_status['Status'] = df_with_status[selected_variables].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)
            
            csv_full = io.StringIO()
            df_with_status.to_csv(csv_full, index=False)
            
            st.download_button(
                label="📥 Download Full Dataset (CSV)",
                data=csv_full.getvalue(),
                file_name=f"full_dataset_with_status_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        


else:
    # When no data is uploaded, show nothing or minimal message
    pass

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 Health Facility Reporting Status Analysis Tool | Built with Streamlit & Matplotlib</p>
</div>
""", unsafe_allow_html=True)
