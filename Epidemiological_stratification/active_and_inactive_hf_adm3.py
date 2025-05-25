import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Health Facility District-Level Analysis",
    page_icon="🏥",
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
    
    .download-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .region-selector {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🏥 Health Facility District-Level Distribution Analysis</h1>
    <p>Comprehensive district-level analysis of health facility activity patterns within regions</p>
</div>
""", unsafe_allow_html=True)

class HealthFacilityProcessor:
    def __init__(self):
        self.df = None
    
    def load_data(self, uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'):
                self.df = pd.read_csv(uploaded_file)
            else:
                self.df = pd.read_excel(uploaded_file)
            st.success("✅ Data successfully loaded!")
            return True
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            return False
    
    def validate_data(self):
        """Validate that the dataframe has required columns"""
        required_cols = ['hf_uid', 'allout', 'susp', 'test', 'conf', 'maltreat', 'month', 'year', 'adm1', 'adm3']
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            return False
        
        st.success(f"✅ All validation checks passed! Using ADM1 (regions) and ADM3 (districts)")
        
        # Show data structure info
        regions = self.df['adm1'].unique()
        districts = self.df['adm3'].unique()
        st.info(f"📍 Found {len(regions)} regions and {len(districts)} districts")
        
        return True
    
    def process_data(self):
        # Calculate report column
        self.df['report'] = (self.df[['allout', 'susp', 'test', 'conf', 'maltreat']] > 0).sum(axis=1, min_count=1)
        
        # Create date column and calculate first month reported
        self.df['month'] = self.df['month'].astype(int).astype(str).str.zfill(2)
        self.df['year'] = self.df['year'].astype(int).astype(str)
        self.df['date'] = pd.to_datetime(self.df['year'] + '-' + self.df['month'], format='%Y-%m')
        
        # Calculate first month reported
        report_positive = self.df[self.df['report'] > 0]
        first_months = report_positive.groupby('hf_uid')['date'].min()
        self.df['First_month_hf_reported'] = self.df['hf_uid'].map(first_months)
        
        # Split active and inactive
        active_df = self.df[self.df['First_month_hf_reported'].notna()]
        inactive_df = self.df[self.df['First_month_hf_reported'].isna()]
        
        return active_df, inactive_df

    def plot_by_adm3_for_each_adm1(self, active_df, inactive_df, selected_adm1, active_color='#47B5FF', inactive_color='#FFB6C1'):
        """
        Create plot for selected adm1, showing adm3 distributions.
        """
        # Filter data for this adm1
        active_adm1 = active_df[active_df['adm1'] == selected_adm1]
        inactive_adm1 = inactive_df[inactive_df['adm1'] == selected_adm1]
        
        # Get adm3 values for this adm1
        adm3_values = sorted(set(active_adm1['adm3'].unique()) | set(inactive_adm1['adm3'].unique()))
        
        if not adm3_values:
            return None
            
        # Calculate counts for each adm3
        active_counts = active_adm1.groupby('adm3')['hf_uid'].nunique()
        inactive_counts = inactive_adm1.groupby('adm3')['hf_uid'].nunique()
        
        # Create figure with better sizing
        fig, ax = plt.subplots(figsize=(16, max(8, len(adm3_values) * 0.5)))
        
        # Create bars
        y = np.arange(len(adm3_values))
        height = 0.8
        
        # Plot stacked bars with custom colors
        active_data = [active_counts.get(adm3, 0) for adm3 in adm3_values]
        inactive_data = [inactive_counts.get(adm3, 0) for adm3 in adm3_values]
        
        ax.barh(y, active_data, height, label='Active Facilities', color=active_color, alpha=0.8)
        ax.barh(y, inactive_data, height, left=active_data,
                label='Inactive Facilities', color=inactive_color, alpha=0.8)
        
        # Add count labels with better formatting
        for i, adm3 in enumerate(adm3_values):
            active_count = active_counts.get(adm3, 0)
            inactive_count = inactive_counts.get(adm3, 0)
            total = active_count + inactive_count
            
            if total > 0:
                # Add labels with count
                if active_count > 0:
                    ax.text(active_count/2, i, f'{active_count:,}',
                            ha='center', va='center', fontweight='bold', fontsize=10)
                if inactive_count > 0:
                    ax.text(active_count + inactive_count/2, i,
                            f'{inactive_count:,}',
                            ha='center', va='center', fontweight='bold', fontsize=10)
        
        # Enhanced styling
        plt.title(f'Health Facility Distribution in {selected_adm1} by District', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Number of Health Facilities', fontsize=12, fontweight='bold', labelpad=10)
        plt.ylabel('District (ADM3)', fontsize=12, fontweight='bold', labelpad=10)
        plt.yticks(y, adm3_values, fontsize=10)
        plt.legend(loc='lower right', fontsize=11)
        
        # Add grid for better readability
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        return fig

def save_fig_to_bytes(fig):
    """Convert a matplotlib figure to bytes for downloading."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

def create_district_summary_stats(active_df, inactive_df, selected_region):
    """Create summary statistics for the selected region"""
    # Filter data for selected region
    active_region = active_df[active_df['adm1'] == selected_region]
    inactive_region = inactive_df[inactive_df['adm1'] == selected_region]
    
    total_facilities = len(pd.concat([active_region, inactive_region])['hf_uid'].unique())
    active_facilities = len(active_region['hf_uid'].unique())
    inactive_facilities = len(inactive_region['hf_uid'].unique())
    total_districts = len(set(active_region['adm3'].unique()) | set(inactive_region['adm3'].unique()))
    activity_rate = (active_facilities / total_facilities * 100) if total_facilities > 0 else 0
    
    return {
        'total_facilities': total_facilities,
        'active_facilities': active_facilities,
        'inactive_facilities': inactive_facilities,
        'total_districts': total_districts,
        'activity_rate': round(activity_rate, 2)
    }

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

# File upload section
st.header("📁 Data Upload")

uploaded_file = st.file_uploader(
    "Upload your health facility data file",
    type=['csv', 'xlsx', 'xls'],
    help="File should contain: hf_uid, allout, susp, test, conf, maltreat, month, year, adm1, adm3"
)

if uploaded_file is not None:
    processor = HealthFacilityProcessor()
    
    if processor.load_data(uploaded_file):
        st.info(f"📊 Shape: {processor.df.shape[0]} rows × {processor.df.shape[1]} columns")
        
        # Show original data structure
        with st.expander("🔍 Original Data Structure (First 10 rows)"):
            st.write("**Available Columns:**")
            st.write(list(processor.df.columns))
            st.write("**Sample Records:**")
            st.dataframe(processor.df.head(10), use_container_width=True)
        
        # Validate data
        if processor.validate_data():
            
            # Show processed data preview
            with st.expander("🔍 View Processed Data (First 10 rows)"):
                display_cols = ['hf_uid', 'adm1', 'adm3', 'month', 'year', 'allout', 'susp', 'test', 'conf', 'maltreat']
                available_cols = [col for col in display_cols if col in processor.df.columns]
                st.dataframe(processor.df[available_cols].head(10), use_container_width=True)
            
            # Analysis customization
            st.subheader("🎨 Customize Your District Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎨 Color Customization**")
                active_color = st.color_picker("Active Facilities Color", "#47B5FF", help="Color for active facilities")
                inactive_color = st.color_picker("Inactive Facilities Color", "#FFB6C1", help="Color for inactive facilities")
            
            with col2:
                st.markdown("**📊 Analysis Description**")
                st.markdown("""
                <div class="info-box">
                    <p><strong>District-Level Analysis:</strong></p>
                    <ul>
                        <li>Select a region (ADM1) to analyze</li>
                        <li>View facility distribution by districts (ADM3)</li>
                        <li>Compare active vs inactive facilities</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Color preview
            st.write("### 🎨 Color Preview")
            col_prev1, col_prev2, col_prev3 = st.columns(3)
            
            with col_prev1:
                st.markdown(f"""
                <div style="background-color: {active_color}; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0;">
                    <strong>Active Facilities</strong>
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
                <div style="background-color: {inactive_color}; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0;">
                    <strong>Inactive Facilities</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Analysis features
            st.write("### 📊 Analysis Features")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="method-card">
                    <h4>🏥 District-Level Breakdown</h4>
                    <p>Detailed analysis within each region:</p>
                    <ul>
                        <li><strong>Region Selection:</strong> Choose any ADM1 region</li>
                        <li><strong>District View:</strong> See ADM3 district distributions</li>
                        <li><strong>Activity Status:</strong> Active vs inactive facilities</li>
                        <li><strong>Count Labels:</strong> Exact facility numbers</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="method-card">
                    <h4>📈 Interactive Features</h4>
                    <p>Comprehensive analysis tools:</p>
                    <ul>
                        <li><strong>Region Selector:</strong> Dynamic region switching</li>
                        <li><strong>Custom Colors:</strong> Personalized visualizations</li>
                        <li><strong>High-Quality Export:</strong> PNG downloads</li>
                        <li><strong>Summary Statistics:</strong> Key metrics dashboard</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Process data button
            if st.button("🚀 Generate District-Level Analysis", type="primary"):
                with st.spinner("Processing health facility data for district-level analysis..."):
                    try:
                        active_df, inactive_df = processor.process_data()
                        st.session_state.processed_data = {
                            'active_df': active_df,
                            'inactive_df': inactive_df,
                            'processor': processor,
                            'active_color': active_color,
                            'inactive_color': inactive_color
                        }
                        st.success("✅ Analysis completed successfully!")
                        
                        # Add celebration effects
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing data: {str(e)}")
                
                st.rerun()

# Show results if analysis is complete
if st.session_state.processed_data is not None:
    data = st.session_state.processed_data
    active_df = data['active_df']
    inactive_df = data['inactive_df']
    processor = data['processor']
    
    st.subheader("🗺️ District-Level Distribution Analysis")
    
    # Region selector with enhanced styling
    st.markdown('<div class="region-selector">', unsafe_allow_html=True)
    
    # Get unique regions
    regions = sorted(processor.df['adm1'].unique())
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_region = st.selectbox(
            "🌍 Select a region to view district-level distribution:",
            regions,
            help="Choose a region (ADM1) to analyze facility distribution across its districts (ADM3)"
        )
    
    with col2:
        st.markdown("**Region Info:**")
        districts_in_region = processor.df[processor.df['adm1'] == selected_region]['adm3'].nunique()
        st.info(f"📍 {districts_in_region} districts in {selected_region}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary statistics for selected region
    stats = create_district_summary_stats(active_df, inactive_df, selected_region)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Facilities</h4>
            <h2>{stats['total_facilities']}</h2>
            <p>In {selected_region}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Active Facilities</h4>
            <h2>{stats['active_facilities']}</h2>
            <p>Have reported data</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Inactive Facilities</h4>
            <h2>{stats['inactive_facilities']}</h2>
            <p>Never reported</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Districts</h4>
            <h2>{stats['total_districts']}</h2>
            <p>ADM3 levels</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Activity Rate</h4>
            <h2>{stats['activity_rate']}%</h2>
            <p>Regional activity</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show district distribution for selected region
    st.write(f"### 📊 Facility Distribution in {selected_region} by District")
    fig_district = processor.plot_by_adm3_for_each_adm1(
        active_df, inactive_df, selected_region, 
        data['active_color'], data['inactive_color']
    )
    
    if fig_district is not None:
        st.pyplot(fig_district)
        
        # Download section
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            district_bytes = save_fig_to_bytes(fig_district)
            st.download_button(
                label=f"📥 Download {selected_region} District Analysis (PNG)",
                data=district_bytes,
                file_name=f"district_distribution_{selected_region.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                mime="image/png"
            )
        
        with col2:
            # Export district data for selected region
            region_data = processor.df[processor.df['adm1'] == selected_region]
            csv_region = io.StringIO()
            region_data.to_csv(csv_region, index=False)
            
            st.download_button(
                label=f"📥 Download {selected_region} Data (CSV)",
                data=csv_region.getvalue(),
                file_name=f"district_data_{selected_region.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.warning(f"⚠️ No district-level data available for {selected_region}")
    
    # Add celebration button
    col_center = st.columns([1, 1, 1])[1]
    with col_center:
        if st.button("🎉 Celebrate Results!", type="secondary"):
            st.balloons()
            st.snow()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🏥 Health Facility District-Level Distribution Analysis Tool | Built with Streamlit & Matplotlib</p>
</div>
""", unsafe_allow_html=True)
