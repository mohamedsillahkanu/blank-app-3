import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io

class IndividualRegionProcessor:
    def __init__(self):
        self.df = None
        self.grouped = None

    def load_data(self):
        try:
            self.df = pd.read_excel("active_health_facilities.xlsx")
            st.success("Data successfully loaded!")
            return True
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return False

    def calculate_reporting_rate(self):
        self.grouped = (
            self.df.groupby(['adm1', 'adm3', 'date'])
            .agg(
                report_conf_sum=('report_conf', 'sum'),
                hf_expected_sum=('hf_expected_to_report_month', 'sum')
            )
            .reset_index()
        )

        self.grouped['reporting_rate'] = (
            self.grouped['report_conf_sum'].div(self.grouped['hf_expected_sum']) * 100
        ).round(2)

    def get_available_regions(self):
        if self.grouped is not None:
            return sorted(self.grouped['adm1'].unique())
        return []

    def pivot_heatmap_data(self, data):
        heatmap_data = data.pivot(index='adm3', columns='date', values='reporting_rate')
        heatmap_data.columns = heatmap_data.columns.strftime('%Y-%m')
        heatmap_data['average_reporting_rate'] = heatmap_data.mean(axis=1, skipna=True)
        heatmap_data = heatmap_data.sort_values(by='average_reporting_rate', ascending=False)
        return heatmap_data.drop(columns=['average_reporting_rate'])

    def plot_individual_heatmap(self, selected_adm1):
        adm1_data = self.grouped[self.grouped['adm1'] == selected_adm1]
        
        if adm1_data.empty:
            st.warning(f"No data found for region: {selected_adm1}")
            return None
            
        heatmap_data = self.pivot_heatmap_data(adm1_data)

        fig, ax = plt.subplots(figsize=(16, 10))
        sns.heatmap(
            data=heatmap_data,
            annot=False,
            fmt=".1f",
            cmap="viridis",
            linewidths=0,
            cbar_kws={'label': 'Reporting Rate (%)'},
            yticklabels=True
        )
        plt.title(f'Monthly Reporting Rate by District ({selected_adm1})', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('District', fontsize=12)
        plt.xticks(rotation=90, ha='right')
        plt.tight_layout()
        
        return fig

def save_fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

def main():
    st.title("Individual Region Health Facility Reporting Rate Analysis")
    st.snow()
    st.balloons()
    
    processor = IndividualRegionProcessor()
    
    if processor.load_data():
        with st.spinner("Processing data..."):
            try:
                processor.calculate_reporting_rate()
                
                # Get available regions
                available_regions = processor.get_available_regions()
                
                if not available_regions:
                    st.error("No regions found in the data.")
                    return
                
                # Region selection dropdown
                st.header("Select Region to Analyze")
                selected_region = st.selectbox(
                    "Choose a region:",
                    available_regions,
                    index=0,
                    help="Select a region to view its detailed reporting rate heatmap"
                )
                
                if selected_region:
                    st.header(f"Reporting Rate Heatmap - {selected_region}")
                    
                    # Plot individual heatmap for selected region
                    fig_individual = processor.plot_individual_heatmap(selected_region)
                    
                    if fig_individual:
                        st.pyplot(fig_individual)
                        
                        # Download button for the selected region
                        individual_bytes = save_fig_to_bytes(fig_individual)
                        st.download_button(
                            label=f"Download {selected_region} Heatmap",
                            data=individual_bytes,
                            file_name=f"reporting_rate_{selected_region.replace(' ', '_')}.png",
                            mime="image/png"
                        )
                        
                        # Display some statistics about the selected region
                        region_data = processor.grouped[processor.grouped['adm1'] == selected_region]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            avg_rate = region_data['reporting_rate'].mean()
                            st.metric("Average Reporting Rate", f"{avg_rate:.1f}%")
                        
                        with col2:
                            num_districts = region_data['adm3'].nunique()
                            st.metric("Number of Districts", num_districts)
                        
                        with col3:
                            max_rate = region_data['reporting_rate'].max()
                            st.metric("Highest Reporting Rate", f"{max_rate:.1f}%")
                
                st.snow()
                st.balloons()
                
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()
