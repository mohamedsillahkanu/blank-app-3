import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

st.set_page_config(layout="wide", page_title="Health Facility Map Generator")

st.title("Interactive Health Facility Map Generator")
st.write("Upload your shapefiles and health facility data to generate a customized map.")

# Create two columns for file uploads
col1, col2 = st.columns(2)

with col1:
    st.header("Upload Shapefiles")
    shp_file = st.file_uploader("Upload .shp file", type=["shp"], key="shp")
    shx_file = st.file_uploader("Upload .shx file", type=["shx"], key="shx")
    dbf_file = st.file_uploader("Upload .dbf file", type=["dbf"], key="dbf")

with col2:
    st.header("Upload Health Facility Data")
    facility_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"], key="facility")

# Check if all required files are uploaded
if all([shp_file, shx_file, dbf_file, facility_file]):
    try:
        # Read shapefiles
        with open("temp.shp", "wb") as f:
            f.write(shp_file.read())
        with open("temp.shx", "wb") as f:
            f.write(shx_file.read())
        with open("temp.dbf", "wb") as f:
            f.write(dbf_file.read())
        shapefile = gpd.read_file("temp.shp")

        # Read facility data
        coordinates_data = pd.read_excel(facility_file)

        # Display data preview
        st.subheader("Data Preview")
        st.dataframe(coordinates_data.head())

        # Map customization options
        st.header("Map Customization")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            # Coordinate column selection
            longitude_col = st.selectbox(
                "Select Longitude Column",
                coordinates_data.columns,
                index=coordinates_data.columns.get_loc("w_long") if "w_long" in coordinates_data.columns else 0
            )
            latitude_col = st.selectbox(
                "Select Latitude Column",
                coordinates_data.columns,
                index=coordinates_data.columns.get_loc("w_lat") if "w_lat" in coordinates_data.columns else 0
            )

        with col4:
            # Visual customization
            map_title = st.text_input("Map Title", "Health Facility Distribution")
            point_size = st.slider("Point Size", 10, 200, 50)
            point_alpha = st.slider("Point Transparency", 0.1, 1.0, 0.7)

        with col5:
            # Color selection
            background_colors = ["white", "lightgray", "beige", "lightblue"]
            point_colors = ["#47B5FF", "red", "green", "purple", "orange"]
            
            background_color = st.selectbox("Background Color", background_colors)
            point_color = st.selectbox("Point Color", point_colors)

        # Data processing
        # Remove missing coordinates
        coordinates_data = coordinates_data.dropna(subset=[longitude_col, latitude_col])
        
        # Filter invalid coordinates
        coordinates_data = coordinates_data[
            (coordinates_data[longitude_col].between(-180, 180)) &
            (coordinates_data[latitude_col].between(-90, 90))
        ]

        if len(coordinates_data) == 0:
            st.error("No valid coordinates found in the data after filtering.")
            st.stop()

        # Convert to GeoDataFrame
        geometry = [Point(xy) for xy in zip(coordinates_data[longitude_col], coordinates_data[latitude_col])]
        coordinates_gdf = gpd.GeoDataFrame(coordinates_data, geometry=geometry, crs="EPSG:4326")

        # Ensure consistent CRS
        if shapefile.crs is None:
            shapefile = shapefile.set_crs(epsg=4326)
        else:
            shapefile = shapefile.to_crs(epsg=4326)

        # Create the map with fixed aspect
        fig, ax = plt.subplots(figsize=(15, 10))

        # Plot shapefile with custom style
        shapefile.plot(ax=ax, color=background_color, edgecolor='black', linewidth=0.5)

        # Calculate and set appropriate aspect ratio
        bounds = shapefile.total_bounds
        mid_y = np.mean([bounds[1], bounds[3]])  # middle latitude
        aspect = 1.0  # default aspect ratio
        
        if -90 < mid_y < 90:  # check if latitude is valid
            try:
                aspect = 1 / np.cos(np.radians(mid_y))
                if not np.isfinite(aspect) or aspect <= 0:
                    aspect = 1.0
            except:
                aspect = 1.0
        
        ax.set_aspect(aspect)

        # Plot points with custom style
        coordinates_gdf.plot(
            ax=ax,
            color=point_color,
            markersize=point_size,
            alpha=point_alpha
        )

        # Customize map appearance
        plt.title(map_title, fontsize=20, pad=20)
        plt.axis('off')

        # Add statistics
        stats_text = (
            f"Total Facilities: {len(coordinates_data)}\n"
            f"Coordinates Range:\n"
            f"Longitude: {coordinates_data[longitude_col].min():.2f}° to {coordinates_data[longitude_col].max():.2f}°\n"
            f"Latitude: {coordinates_data[latitude_col].min():.2f}° to {coordinates_data[latitude_col].max():.2f}°"
        )
        plt.figtext(0.02, 0.02, stats_text, fontsize=8, bbox=dict(facecolor='white', alpha=0.8))

        # Display the map
        st.pyplot(fig)

        # Download options
        col6, col7 = st.columns(2)
        
        with col6:
            # Save high-resolution PNG
            output_path_png = "health_facility_map.png"
            plt.savefig(output_path_png, dpi=300, bbox_inches='tight', pad_inches=0.1)
            with open(output_path_png, "rb") as file:
                st.download_button(
                    label="Download Map (PNG)",
                    data=file,
                    file_name="health_facility_map.png",
                    mime="image/png"
                )

        with col7:
            # Export coordinates as CSV
            csv = coordinates_data.to_csv(index=False)
            st.download_button(
                label="Download Processed Data (CSV)",
                data=csv,
                file_name="processed_coordinates.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Please check your input files and try again.")

else:
    st.info("Please upload all required files to generate the map.")
    
    # Show example data format
    st.subheader("Expected Data Format")
    st.write("""
    Your Excel file should contain at minimum:
    - A column for longitude (e.g., 'w_long')
    - A column for latitude (e.g., 'w_lat')
    
    The coordinates should be in decimal degrees format.
    """)
