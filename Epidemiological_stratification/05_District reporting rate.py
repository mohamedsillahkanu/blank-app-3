import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io

class RegionalReportingProcessor:
    def __init__(self):
        self.df = None
        self.grouped = None

    def load_data(self):
        try:
            self.df = pd.read_excel("active_health_facilities (4).xlsx")
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

    def plot_subplots_by_adm1(self):
        adm1_groups = sorted(self.grouped['adm1'].unique())
        total_adm1 = len(adm1_groups)

        rows = (total_adm1 - 1) // 4 + 1
        fig, axes = plt.subplots(nrows=rows, ncols=4, figsize=(20, rows * 5), constrained_layout=True)
        axes = axes.flatten()

        for idx, adm1 in enumerate(adm1_groups):
            adm1_data = self.grouped[self.grouped['adm1'] == adm1]
            heatmap_data = self.pivot_heatmap_data(adm1_data)

            sns.heatmap(
                data=heatmap_data,
                annot=False,
                fmt=".1f",
                cmap="viridis",
                linewidths=0,
                ax=axes[idx],
                cbar_kws={'label': 'Reporting Rate (%)'},
                yticklabels=False
            )
            axes[idx].set_title(f'{adm1}', fontsize=14, fontweight='bold')
            axes[idx].set_xlabel('Date', fontsize=10)
            axes[idx].set_ylabel('District', fontsize=10)
            axes[idx].tick_params(axis='x', rotation=90)

        for ax in axes[len(adm1_groups):]:
            ax.axis('off')

        plt.suptitle('Monthly Reporting Rate by District (Grouped by Region)', fontsize=16, fontweight='bold')
        
        return fig

def save_fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

def main():
    st.title("Regional Health Facility Reporting Rate Analysis")
    st.snow()
    st.balloons()
    
    processor = RegionalReportingProcessor()
    
    if processor.load_data():
        with st.spinner("Processing data..."):
            try:
                processor.calculate_reporting_rate()
                
                # Regional Subplots
                st.header("Regional Reporting Rate Heatmaps")
                fig_subplots = processor.plot_subplots_by_adm1()
                st.pyplot(fig_subplots)
                
                subplots_bytes = save_fig_to_bytes(fig_subplots)
                st.download_button(
                    label="Download Regional Heatmaps",
                    data=subplots_bytes,
                    file_name="regional_reporting_rates.png",
                    mime="image/png"
                )
                
                st.snow()
                st.balloons()
                
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()
