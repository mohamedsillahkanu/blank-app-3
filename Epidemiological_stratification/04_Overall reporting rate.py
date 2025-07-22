import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io

class OverallReportingProcessor:
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

    def pivot_heatmap_data(self, data):
        heatmap_data = data.pivot(index='adm3', columns='date', values='reporting_rate')
        heatmap_data.columns = heatmap_data.columns.strftime('%Y-%m')
        heatmap_data['average_reporting_rate'] = heatmap_data.mean(axis=1, skipna=True)
        heatmap_data = heatmap_data.sort_values(by='average_reporting_rate', ascending=False)
        return heatmap_data.drop(columns=['average_reporting_rate'])

    def plot_overall_heatmap(self):
        overall_data = self.grouped.groupby(['adm3', 'date'])['reporting_rate'].mean().reset_index()
        heatmap_data = self.pivot_heatmap_data(overall_data)

        fig, ax = plt.subplots(figsize=(16, 10))
        sns.heatmap(
            data=heatmap_data,
            annot=False,
            fmt=".1f",
            cmap="viridis",
            linewidths=0,
            cbar_kws={'label': 'Reporting Rate (%)'},
            yticklabels=False
        )
        plt.title('Overall Monthly Reporting Rate by District', fontsize=16, fontweight='bold')
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
    st.title("Overall Health Facility Reporting Rate Analysis")
    st.snow()
    st.balloons()
    
    processor = OverallReportingProcessor()
    
    if processor.load_data():
        with st.spinner("Processing data..."):
            try:
                processor.calculate_reporting_rate()
                
                # Overall Heatmap
                st.header("Overall Reporting Rate Heatmap")
                fig_overall = processor.plot_overall_heatmap()
                st.pyplot(fig_overall)
                
                overall_bytes = save_fig_to_bytes(fig_overall)
                st.download_button(
                    label="Download Overall Heatmap",
                    data=overall_bytes,
                    file_name="overall_reporting_rate.png",
                    mime="image/png"
                )
                
                st.snow()
                st.balloons()
                
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()
