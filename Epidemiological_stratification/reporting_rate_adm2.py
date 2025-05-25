import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Health Facility Regional Distribution Analysis",
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
    
    .download-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Health Facility Regional Distribution Analysis</h1>
    <p>Advanced analytics for health facility activity patterns across administrative regions</p>
</div>
""", unsafe_allow_html=True)

class HealthFacilityProcessor:
    def __init__(self):
        self.df = None
        self.admin_col = None
    
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
        required_cols = ['hf_uid', 'allout', 'susp', 'test', 'conf', 'maltreat', 'month', 'year']
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            return False
        
        # Find admin column
        potential_admin_cols = [col for col in self.df.columns if 
                              any(keyword in col.lower() for keyword in ['adm', 'admin', 'region', 'district', 'province', 'state', 'county', 'zone'])]
        
        if not potential_admin_cols:
            excluded_cols = ['hf_uid', 'allout', 'susp', 'test', 'conf', 'maltreat', 'month', 'year']
            potential_admin_cols = [col for col in self.df.columns if col not in excluded_cols]
        
        if potential_admin_cols:
            self.admin_col = st.selectbox(
                "🗺️ Choose administrative level for regional analysis:",
                options=potential_admin_cols,
                help="Select the column that represents the administrative regions"
            )
            st.session_state.admin_col = self.admin_col
            st.info(f"✅ Selected '{self.admin_col}' as administrative grouping level")
            
            unique_regions = self.df[self.admin_col].unique()
            st.write(f"**Found {len(unique_regions)} regions:** {', '.join(map(str, sorted(unique_regions)))}")
        else:
            st.error("❌ No administrative level columns found in the data")
            return False
        
        st.success(f"✅ All validation checks passed! Ready for analysis with {len(self.df)} records")
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

    def plot_counts_by_region(self, active_df, inactive_df, active_color='#47B5FF', inactive_color='#FFB6C1'):
        """
        Create a horizontal stacked bar chart showing facility counts by region.
        """
        # Get unique admin values and sort them
        admin_values = sorted(self.df[self.admin_col].unique())

        # Calculate counts for each region
        active_counts = active_df.groupby(self.admin_col)['hf_uid'].nunique()
        inactive_counts = inactive_df.groupby(self.admin_col)['hf_uid'].nunique()

        # Create figure
        fig, ax = plt.subplots(figsize=(14, max(8, len(admin_values) * 0.6)))

        # Create bars
        y = np.arange(len(admin_values))
        height = 0.8

        # Plot stacked bars
        active_bars = ax.barh(y, [active_counts.get(admin, 0) for admin in admin_values],
                             height, label='Active Facilities', color=active_color, alpha=0.8)
        inactive_bars = ax.barh(y, [inactive_counts.get(admin, 0) for admin in admin_values],
                               height, left=[active_counts.get(admin, 0) for admin in admin_values],
                               label='Inactive Facilities', color=inactive_color, alpha=0.8)

        # Add count labels
        for i, admin in enumerate(admin_values):
            active_count = active_counts.get(admin, 0)
            inactive_count = inactive_counts.get(admin, 0)

            if active_count > 0:
                ax.text(active_count/2, i, f'{active_count}',
                        ha='center', va='center', fontweight='bold', fontsize=10)
            if inactive_count > 0:
                ax.text(active_count + inactive_count/2, i,
                        f'{inactive_count}',
                        ha='center', va='center', fontweight='bold', fontsize=10)

        admin_level_name = self.admin_col.upper()
        plt.title(f'Health Facility Counts by {admin_level_name}', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Number of Health Facilities', fontsize=12, fontweight='bold', labelpad=10)
        plt.ylabel(f'{admin_level_name}', fontsize=12, fontweight='bold', labelpad=10)
        plt.yticks(y, admin_values, fontsize=10)
        plt.legend(loc='lower right', fontsize=11)
        
        # Add grid for better readability
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        plt.tight_layout()
        return fig

    def plot_percentages_by_region(self, active_df, inactive_df, active_color='#47B5FF', inactive_color='#FFB6C1'):
        """
        Create a horizontal stacked bar chart showing facility percentages by region.
        """
        # Get unique admin values and sort them
        admin_values = sorted(self.df[self.admin_col].unique())
        
        # Calculate counts and percentages
        active_counts = active_df.groupby(self.admin_col)['hf_uid'].nunique()
        inactive_counts = inactive_df.groupby(self.admin_col)['hf_uid'].nunique()

        fig, ax = plt.subplots(figsize=(14, max(8, len(admin_values) * 0.6)))
        y = np.arange(len(admin_values))
        height = 0.8

        for i, admin in enumerate(admin_values):
            active_count = active_counts.get(admin, 0)
            inactive_count = inactive_counts.get(admin, 0)
            total = active_count + inactive_count

            if total > 0:
                active_pct = (active_count / total * 100)
                inactive_pct = (inactive_count / total * 100)

                ax.barh(i, active_pct, height, label='Active Facilities' if i == 0 else "",
                        color=active_color, alpha=0.8)
                ax.barh(i, inactive_pct, height, left=active_pct,
                        label='Inactive Facilities' if i == 0 else "", color=inactive_color, alpha=0.8)

                if active_pct > 5:  # Only show label if segment is large enough
                    ax.text(active_pct/2, i, f'{active_pct:.1f}%',
                            ha='center', va='center', fontweight='bold', fontsize=10)
                if inactive_pct > 5:
                    ax.text(active_pct + inactive_pct/2, i, f'{inactive_pct:.1f}%',
                            ha='center', va='center', fontweight='bold', fontsize=10)

        admin_level_name = self.admin_col.upper()
        plt.title(f'Health Facility Distribution by {admin_level_name} (%)', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Percentage of Health Facilities', fontsize=12, fontweight='bold', labelpad=10)
        plt.ylabel(f'{admin_level_name}', fontsize=12, fontweight='bold', labelpad=10)
        plt.yticks(y, admin_values, fontsize=10)
        plt.xlim(0, 100)
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

def create_summary_stats(active_df, inactive_df, admin_col):
    """Create summary statistics"""
    total_facilities = len(pd.concat([active_df, inactive_df])['hf_uid'].unique())
    active_facilities = len(active_df['hf_uid'].unique())
    inactive_facilities = len(inactive_df['hf_uid'].unique())
    activity_rate = (active_facilities / total_facilities * 100) if total_facilities > 0 else 0
    
    return {
        'total_facilities': total_facilities,
        'active_facilities': active_facilities,
        'inactive_facilities': inactive_facilities,
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
    help="File should contain: hf_uid, allout, susp, test, conf, maltreat, month, year, and administrative level columns"
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
        
        # Validate data and select admin level
        if processor.validate_data():
            
            # Show processed data preview
            with st.expander("🔍 View Processed Data (First 10 rows)"):
                display_cols = ['hf_uid', processor.admin_col, 'month', 'year', 'allout', 'susp', 'test', 'conf', 'maltreat']
                available_cols = [col for col in display_cols if col in processor.df.columns]
                st.dataframe(processor.df[available_cols].head(10), use_container_width=True)
            
            # Analysis customization
            st.subheader("🎨 Customize Your Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎨 Color Customization**")
                active_color = st.color_picker("Active Facilities Color", "#47B5FF", help="Color for active facilities")
                inactive_color = st.color_picker("Inactive Facilities Color", "#FFB6C1", help="Color for inactive facilities")
            
            with col2:
                st.markdown("**📊 Analysis Options**")
                show_counts = st.checkbox("Show Facility Counts", value=True)
                show_percentages = st.checkbox("Show Facility Percentages", value=True)
            
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
            
            # Analysis description
            st.write("### 📊 Analysis Features")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="method-card">
                    <h4>🏥 Active vs Inactive Classification</h4>
                    <p>Facilities are classified based on their reporting history:</p>
                    <ul>
                        <li><strong>Active:</strong> Have reported at least once</li>
                        <li><strong>Inactive:</strong> Have never reported any data</li>
                        <li>Based on all case types: allout, susp, test, conf, maltreat</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="method-card">
                    <h4>📈 Visualization Options</h4>
                    <p>Two complementary views of the data:</p>
                    <ul>
                        <li><strong>Counts:</strong> Absolute numbers by region</li>
                        <li><strong>Percentages:</strong> Relative distribution within regions</li>
                        <li>Interactive color customization</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Process data button
            if st.button("🚀 Generate Regional Analysis", type="primary"):
                with st.spinner("Processing health facility data and generating analysis..."):
                    try:
                        active_df, inactive_df = processor.process_data()
                        st.session_state.processed_data = {
                            'active_df': active_df,
                            'inactive_df': inactive_df,
                            'processor': processor,
                            'active_color': active_color,
                            'inactive_color': inactive_color,
                            'show_counts': show_counts,
                            'show_percentages': show_percentages
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
    
    st.subheader("📈 Regional Distribution Analysis Results")
    
    # Summary statistics
    stats = create_summary_stats(active_df, inactive_df, processor.admin_col)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Facilities</h4>
            <h2>{stats['total_facilities']}</h2>
            <p>In all regions</p>
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
            <h4>Activity Rate</h4>
            <h2>{stats['activity_rate']}%</h2>
            <p>Overall activity</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show visualizations
    if data['show_counts']:
        st.write(f"### 📊 Facility Counts by {processor.admin_col.upper()}")
        fig_counts = processor.plot_counts_by_region(active_df, inactive_df, 
                                                   data['active_color'], data['inactive_color'])
        st.pyplot(fig_counts)
        
        # Download section for counts
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        counts_bytes = save_fig_to_bytes(fig_counts)
        st.download_button(
            label="📥 Download Counts Visualization (PNG)",
            data=counts_bytes,
            file_name=f"facility_counts_{processor.admin_col}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
            mime="image/png"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    if data['show_percentages']:
        st.write(f"### 📈 Facility Distribution by {processor.admin_col.upper()} (%)")
        fig_percentages = processor.plot_percentages_by_region(active_df, inactive_df,
                                                             data['active_color'], data['inactive_color'])
        st.pyplot(fig_percentages)
        
        # Download section for percentages
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        percentages_bytes = save_fig_to_bytes(fig_percentages)
        st.download_button(
            label="📥 Download Percentages Visualization (PNG)",
            data=percentages_bytes,
            file_name=f"facility_percentages_{processor.admin_col}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
            mime="image/png"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Data export section
    st.subheader("💾 Download Processed Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Active facilities data
        csv_active = io.StringIO()
        active_df.to_csv(csv_active, index=False)
        
        st.download_button(
            label="📥 Download Active Facilities (CSV)",
            data=csv_active.getvalue(),
            file_name=f"active_facilities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Inactive facilities data
        csv_inactive = io.StringIO()
        inactive_df.to_csv(csv_inactive, index=False)
        
        st.download_button(
            label="📥 Download Inactive Facilities (CSV)",
            data=csv_inactive.getvalue(),
            file_name=f"inactive_facilities_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Summary statistics
        summary_data = {
            'Metric': ['Total Facilities', 'Active Facilities', 'Inactive Facilities', 'Activity Rate (%)'],
            'Value': [stats['total_facilities'], stats['active_facilities'], 
                     stats['inactive_facilities'], stats['activity_rate']]
        }
        summary_df = pd.DataFrame(summary_data)
        
        csv_summary = io.StringIO()
        summary_df.to_csv(csv_summary, index=False)
        
        st.download_button(
            label="📥 Download Summary Stats (CSV)",
            data=csv_summary.getvalue(),
            file_name=f"summary_statistics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
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
    <p>📊 Health Facility Regional Distribution Analysis Tool | Built with Streamlit & Matplotlib</p>
</div>
""", unsafe_allow_html=True)
