import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


import pandas as pd
import numpy as np
from jellyfish import jaro_winkler_similarity
from io import BytesIO
from PIL import Image
import random
import time
import threading

# Page configuration
st.set_page_config(page_title="Geospatial Analysis Tool", page_icon="🗺️", layout="wide")

# Theme definitions
themes = {
    "Black Modern": {
        "bg": "#000000",
        "accent": "#3498db",
        "text": "#FFFFFF",
        "gradient": "linear-gradient(135deg, #3498db, #2ecc71)"
    },
    "Light Silver": {
        "bg": "#F5F5F5",
        "accent": "#1E88E5",
        "text": "#212121",
        "gradient": "linear-gradient(135deg, #1E88E5, #64B5F6)"
    },
    "Light Sand": {
        "bg": "#FAFAFA",
        "accent": "#FF7043",
        "text": "#424242",
        "gradient": "linear-gradient(135deg, #FF7043, #FFB74D)"
    },
    "Light Modern": {
        "bg": "#FFFFFF",
        "accent": "#3498db",
        "text": "#333333",
        "gradient": "linear-gradient(135deg, #3498db, #2ecc71)"
    },
    "Dark Modern": {
        "bg": "#0E1117",
        "accent": "#3498db",
        "text": "#E0E0E0",
        "gradient": "linear-gradient(135deg, #3498db, #2ecc71)"
    },
    "Dark Elegance": {
        "bg": "#1a1a1a",
        "accent": "#e74c3c",
        "text": "#E0E0E0",
        "gradient": "linear-gradient(135deg, #e74c3c, #c0392b)"
    },
    "Dark Nature": {
        "bg": "#1E1E1E",
        "accent": "#27ae60",
        "text": "#E0E0E0",
        "gradient": "linear-gradient(135deg, #27ae60, #2ecc71)"
    },
    "Dark Cosmic": {
        "bg": "#2c0337",
        "accent": "#9b59b6",
        "text": "#E0E0E0",
        "gradient": "linear-gradient(135deg, #9b59b6, #8e44ad)"
    },
    "Dark Ocean": {
        "bg": "#1A2632",
        "accent": "#00a8cc",
        "text": "#E0E0E0",
        "gradient": "linear-gradient(135deg, #00a8cc, #0089a7)"
    }
}

# Custom CSS styles with enhanced button and input styling
st.markdown("""
    <style>
    .stApp {
        background-color: var(--bg-color, #0E1117) !important;
        color: var(--text-color, #E0E0E0) !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg, #1E1E1E) !important;
        border-right: 1px solid var(--border-color, #2E2E2E);
    }
    
    .stMarkdown, p, h1, h2, h3 {
        color: var(--text-color, #E0E0E0) !important;
    }

    /* Dark Theme Button Styling */
    [data-theme="dark"] .stButton > button,
    [data-theme="dark"] .stDownloadButton > button {
        color: black !important;
        font-weight: bold !important;
        background-color: black !important;
        border: 2px solid #3498db !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    [data-theme="dark"] .stButton > button:hover,
    [data-theme="dark"] .stDownloadButton > button:hover {
        background-color: blue !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
    }

    /* Light Theme Button Styling */
    [data-theme="light"] .stButton > button,
    [data-theme="light"] .stDownloadButton > button {
        color: black !important;
        font-weight: bold !important;
        background-color: white !important;
        border: 2px solid #2e2e2e !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    [data-theme="light"] .stButton > button:hover,
    [data-theme="light"] .stDownloadButton > button:hover {
        background-color: #f0f0f0 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
    }

    /* Dark Theme File Uploader */
    [data-theme="dark"] [data-testid="stFileUploader"] {
        background-color: #1E1E1E !important;
        padding: 1rem !important;
        border-radius: 4px !important;
        border: 2px solid #3498db !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    [data-theme="dark"] [data-testid="stFileUploader"] > div > div {
        color: white !important;
        font-weight: bold !important;
    }

    /* Light Theme File Uploader */
    [data-theme="light"] [data-testid="stFileUploader"] {
        background-color: white !important;
        padding: 1rem !important;
        border-radius: 4px !important;
        border: 2px solid #2e2e2e !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    [data-theme="light"] [data-testid="stFileUploader"] > div > div {
        color: black !important;
        font-weight: bold !important;
    }

    /* Dark Theme Select Box */
    [data-theme="dark"] .stSelectbox > div > div {
        color: white !important;
        font-weight: bold !important;
        background-color: #1E1E1E !important;
        border: 2px solid #3498db !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* Light Theme Select Box */
    [data-theme="light"] .stSelectbox > div > div {
        color: black !important;
        font-weight: bold !important;
        background-color: white !important;
        border: 2px solid #2e2e2e !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* Success Message Styling */
    [data-theme="dark"] .stSuccess {
        color: white !important;
        font-weight: bold !important;
        background-color: #1E1E1E !important;
        border: 2px solid #00ff00 !important;
        border-radius: 4px !important;
    }

    [data-theme="light"] .stSuccess {
        color: black !important;
        font-weight: bold !important;
        background-color: white !important;
        border: 2px solid #00aa00 !important;
        border-radius: 4px !important;
    }

    /* Error Message Styling */
    [data-theme="dark"] .stError {
        color: white !important;
        font-weight: bold !important;
        background-color: #1E1E1E !important;
        border: 2px solid #ff0000 !important;
        border-radius: 4px !important;
    }

    [data-theme="light"] .stError {
        color: black !important;
        font-weight: bold !important;
        background-color: white !important;
        border: 2px solid #ff0000 !important;
        border-radius: 4px !important;
    }

    /* DataFrame Styling */
    [data-theme="dark"] .stDataFrame {
        color: white !important;
        font-weight: bold !important;
        background-color: #1E1E1E !important;
        border: 2px solid #3498db !important;
        border-radius: 4px !important;
    }

    [data-theme="light"] .stDataFrame {
        color: black !important;
        font-weight: bold !important;
        background-color: white !important;
        border: 2px solid #2e2e2e !important;
        border-radius: 4px !important;
    }

    /* Slider Styling */
    [data-theme="dark"] .stSlider > div > div > div {
        background-color: #3498db !important;
    }

    [data-theme="dark"] .stSlider > div > div > div > div {
        background-color: white !important;
    }

    [data-theme="light"] .stSlider > div > div > div {
        background-color: #2e2e2e !important;
    }

    [data-theme="light"] .stSlider > div > div > div > div {
        background-color: black !important;
    }

    /* Text Input Styling */
    [data-theme="dark"] .stTextInput > div > div > input {
        color: white !important;
        font-weight: bold !important;
        background-color: #1E1E1E !important;
        border: 2px solid #3498db !important;
        border-radius: 4px !important;
    }

    [data-theme="light"] .stTextInput > div > div > input {
        color: black !important;
        font-weight: bold !important;
        background-color: white !important;
        border: 2px solid #2e2e2e !important;
        border-radius: 4px !important;
    }

    /* Custom Cards */
    .section-card {
        background: var(--card-bg, #1E1E1E) !important;
        color: var(--text-color, #E0E0E0) !important;
        box-shadow: 0 4px 6px var(--shadow-color, rgba(0, 0, 0, 0.3)) !important;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        border-left: 5px solid var(--accent-color, #3498db);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: slideIn 0.5s ease-out;
    }

    .section-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px var(--shadow-color, rgba(0, 0, 0, 0.5));
    }

    /* Custom Title */
    .custom-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes scaleIn {
        from { transform: scale(0.95); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide", page_title="Health Facility Map Generator")

st.title("Health Facility Distribution")
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


def show_confetti():
    """Display confetti animation."""
    st.markdown("""
        <style>
            @keyframes confetti {
                0% { transform: translateY(0) rotate(0deg); }
                100% { transform: translateY(100vh) rotate(360deg); }
            }
            .confetti {
                position: fixed;
                animation: confetti 4s linear;
                z-index: 9999;
            }
        </style>
    """, unsafe_allow_html=True)
    for i in range(50):
        color = f"hsl({random.randint(0, 360)}, 100%, 50%)"
        left = random.randint(0, 100)
        st.markdown(f"""
            <div class="confetti" style="left: {left}vw; background: {color}; 
            width: 10px; height: 10px; border-radius: 50%;"></div>
        """, unsafe_allow_html=True)

def show_sparkles():
    """Display sparkles animation."""
    st.markdown("""
        <style>
            @keyframes sparkle {
                0% { transform: scale(0); opacity: 0; }
                50% { transform: scale(1); opacity: 1; }
                100% { transform: scale(0); opacity: 0; }
            }
            .sparkle {
                position: fixed;
                animation: sparkle 2s infinite;
            }
        </style>
    """, unsafe_allow_html=True)
    for i in range(20):
        left = random.randint(0, 100)
        top = random.randint(0, 100)
        st.markdown(f"""
            <div class="sparkle" style="left: {left}vw; top: {top}vh; 
            background: gold; width: 5px; height: 5px; border-radius: 50%;"></div>
        """, unsafe_allow_html=True)

def show_fireworks():
    """Display random fireworks animation."""
    animations = [st.balloons(), st.snow(), show_confetti(), show_sparkles()]
    random.choice(animations)

# List of available animations
animations_list = [
    st.balloons,
    st.snow,
    show_confetti,
    show_sparkles,
    show_fireworks,
    lambda: [st.balloons(), st.snow()],
    lambda: [show_confetti(), show_sparkles()],
    lambda: [st.balloons(), show_confetti()],
    lambda: [st.snow(), show_sparkles()],
    lambda: [show_confetti(), st.snow()]
]

# Initialize session state for animations
if 'last_animation' not in st.session_state:
    st.session_state.last_animation = time.time()
    st.session_state.theme_index = list(themes.keys()).index("Black Modern")
    st.session_state.first_load = True

# Show welcome message on first load
if st.session_state.first_load:
    st.balloons()
    st.snow()
    welcome_placeholder = st.empty()
    welcome_placeholder.success("Welcome to the Geospatial Analysis Tool! 🌍")
    time.sleep(3)
    welcome_placeholder.empty()
    st.session_state.first_load = False

# Handle theme rotation
current_time = time.time()
if current_time - st.session_state.last_animation >= 30:
    st.session_state.last_animation = current_time
    theme_keys = list(themes.keys())
    st.session_state.theme_index = (st.session_state.theme_index + 1) % len(theme_keys)
    st.balloons()

# Theme selection
selected_theme = st.sidebar.selectbox(
    "🎨 Select Theme",
    list(themes.keys()),
    index=st.session_state.theme_index,
    key='theme_selector'
)

# Handle theme change animations
if 'previous_theme' not in st.session_state:
    st.session_state.previous_theme = selected_theme
if st.session_state.previous_theme != selected_theme:
    st.balloons()
    st.snow()
    st.session_state.previous_theme = selected_theme

# Apply selected theme
theme = themes[selected_theme]
is_light_theme = "Light" in selected_theme

st.markdown(f"""
    <style>
        :root {{
            --bg-color: {theme['bg']};
            --text-color: {theme['text']};
            --accent-color: {theme['accent']};
            --gradient: {theme['gradient']};
            --sidebar-bg: {theme['bg']};
            --card-bg: {'#F8F9FA' if is_light_theme else '#1E1E1E'};
            --card-hover-bg: {'#E9ECEF' if is_light_theme else '#2E2E2E'};
            --input-bg: {'#F8F9FA' if is_light_theme else '#1E1E1E'};
            --shadow-color: {f'rgba(0, 0, 0, 0.1)' if is_light_theme else 'rgba(0, 0, 0, 0.3)'};
            --border-color: {'#DEE2E6' if is_light_theme else '#2E2E2E'};
        }}
    </style>
""", unsafe_allow_html=True)



# Main execution
if __name__ == "__main__":
    st.title("Health Facility Name Matching")
    
    st.markdown("""
        <div class="img-container" style="text-align: center;">
            <img src="https://github.com/mohamedsillahkanu/si/raw/b0706926bf09ba23d8e90c394fdbb17e864121d8/Sierra%20Leone%20Map.png" 
                 style="width: 50%; max-width: 500px; margin: 20px auto;">
        </div>
    """, unsafe_allow_html=True)
    
    main()
    
    # Enable animations if checkbox is checked
    if st.sidebar.checkbox("Enable Auto Animations", value=False):
        def show_periodic_animations():
            while True:
                time.sleep(60)
                random.choice(animations_list)()
                time.sleep(10)
                random.choice(animations_list)()

        if not hasattr(st.session_state, 'animation_thread'):
            st.session_state.animation_thread = threading.Thread(target=show_periodic_animations)
            st.session_state.animation_thread.daemon = True
            st.session_state.animation_thread.start()





