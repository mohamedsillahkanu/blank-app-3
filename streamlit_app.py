import streamlit as st
import streamlit.components.v1 as components
import random
import time
import threading

# Set page config to make it wide mode by default
st.set_page_config(
    page_title="Automated Geospatial Analysis for Malaria Interventions",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Main title
st.title("Automated Geospatial Analysis for Sub-National Tailoring of Malaria Interventions")

# Particles.js HTML configuration with responsive settings
particles_js = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Particles.js</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        #particles-js {
            position: fixed;
            width: 100vw;
            height: 100vh;
            top: 0;
            left: 0;
            z-index: 0;
            background-color: transparent;
        }
        
        .content {
            position: relative;
            z-index: 1;
            width: 100%;
        }
    </style>
</head>
<body>
    <div id="particles-js"></div>
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <script>
        particlesJS("particles-js", {
            "particles": {
                "number": {"value": 300, "density": {"enable": true, "value_area": 800}},
                "color": {"value": "#ffffff"},
                "shape": {"type": "circle"},
                "opacity": {"value": 0.5, "random": false},
                "size": {"value": 2, "random": true},
                "line_linked": {
                    "enable": true,
                    "distance": 100,
                    "color": "#ffffff",
                    "opacity": 0.22,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 0.2,
                    "direction": "none",
                    "random": false,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": true
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": {"enable": true, "mode": "grab"},
                    "onclick": {"enable": true, "mode": "repulse"},
                    "resize": true
                }
            },
            "retina_detect": true
        });
        
        // Make particles responsive to window resize
        window.addEventListener('resize', function() {
            particlesJS('particles-js', particlesConfig);
        });
    </script>
</body>
</html>
"""

# Inject particles.js to fill the entire screen
components.html(particles_js, height=1000)

# Styling with fullscreen responsive design
st.markdown("""
    <style>
        /* Reset and ensure full viewport usage */
        body {
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow-x: hidden;
        }
        
        .stApp {
            background-color: #0E1117 !important;
            color: #E0E0E0 !important;
            width: 100vw !important;
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow-x: hidden !important;
        }
        
        /* Container modifications for full width */
        .container {
            max-width: 100% !important;
            padding: 0 !important;
        }
        
        /* Main content area */
        .main .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Updated Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0E1117 !important;
            border-right: 1px solid #2E2E2E;
            z-index: 2;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdown"],
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: white !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: white !important;
            font-weight: bold;
        }

        [data-testid="stSidebar"] button {
            color: white !important;
            border-color: #47B5FF !important;
        }
        
        /* Content styling */
        .stMarkdown, p, h1, h2, h3 {
            color: #E0E0E0 !important;
            position: relative;
            z-index: 1;
        }
        
        .stButton, .stSelectbox, .stTextInput, .stHeader {
            position: relative;
            z-index: 1;
        }

        /* Responsive section cards */
        .section-card {
            background: #1E1E1E !important;
            color: #E0E0E0 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border-left: 5px solid #3498db;
            transition: transform 0.3s ease;
            width: 100%;
            box-sizing: border-box;
        }
        
        .section-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.5);
            background: #2E2E2E !important;
        }

        .section-header {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #3498db !important;
        }

        .custom-bullet {
            margin-left: 30px;
            position: relative;
            padding: 10px 0;
            display: block;
            color: #E0E0E0 !important;
        }
        
        .custom-bullet::before {
            content: "•";
            color: #3498db;
            position: absolute;
            left: -20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 24px;
            line-height: 1;
        }

        .content-text {
            color: #E0E0E0 !important;
            line-height: 1.6;
        }
        
        /* Make image responsive */
        .img-container img {
            width: 80%;
            max-width: 500px;
            margin: 20px auto;
            display: block;
            height: auto;
        }
        
        /* Responsive design for different screen sizes */
        @media (max-width: 768px) {
            .section-card {
                padding: 15px;
                margin: 15px 0;
            }
            
            .section-header {
                font-size: 1.2rem;
            }
            
            .img-container img {
                width: 95%;
            }
            
            .custom-bullet {
                margin-left: 20px;
            }
        }
        
        @media (max-width: 480px) {
            .section-card {
                padding: 10px;
                margin: 10px 0;
            }
            
            .section-header {
                font-size: 1.1rem;
            }
            
            .custom-bullet {
                margin-left: 15px;
                padding: 5px 0;
            }
            
            .custom-bullet::before {
                left: -15px;
                font-size: 20px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Welcome animation (only on first load)
if 'first_load' not in st.session_state:
    st.session_state.first_load = True

if st.session_state.first_load:
    st.balloons()
    st.snow()
    welcome_placeholder = st.empty()
    st.session_state.first_load = False

# Map image - make it responsive
st.markdown("""
    <div class="img-container" style="text-align: center;">
        <img src="https://github.com/mohamedsillahkanu/si/raw/b0706926bf09ba23d8e90c394fdbb17e864121d8/Sierra%20Leone%20Map.png" 
             alt="Sierra Leone Map">
    </div>
""", unsafe_allow_html=True)

# Sections content
sections = {
    "Overview": """Before now, the Sub-National Tailoring (SNT) process took a considerable amount of time to complete analysis. Based on the experience of the 2023 SNT implementation, we have developed an automated tool using the same validated codes with additional enhanced features. This innovation aims to build the capacity of National Malaria Control Program (NMCP) to conduct SNT easily on a yearly basis and monitor activities effectively using this tool. The tool is designed to be user-friendly and offers high processing speed.

The integration of automation in geospatial analysis significantly enhances the efficiency and effectiveness of data management and visualization tasks. With the introduction of this automated system, analysis time has been drastically reduced from one year to one week. This shift not only streamlines operations but also allows analysts to focus on interpreting results rather than being bogged down by technical processes.""",
    
    "Objectives": """The main objectives of implementing automated systems for geospatial analysis and data management are:
    <div class='custom-bullet'>Reduce Time and Effort: Significantly decrease the time required to create maps and analyze data, enabling quicker decision-making.</div>
    <div class='custom-bullet'>Enhance Skill Accessibility: Provide tools that can be used effectively by individuals without extensive technical training.</div>
    <div class='custom-bullet'>Improve Data Management Efficiency: Streamline data management processes that currently can take days to complete.</div>
    <div class='custom-bullet'>Facilitate Rapid Analysis: Enable automated analysis of uploaded datasets within minutes.</div>""",
    
    "Scope": """
    <div class='custom-bullet'>The development and implementation of an automated system that simplifies the creation of geospatial visualizations.</div>
    <div class='custom-bullet'>A comprehensive automated data analysis tool that processes datasets quickly and efficiently, enabling analysts to obtain insights in less than 20 minutes.</div>
    <div class='custom-bullet'>Training and support for users to maximize the benefits of these tools, ensuring that even those with limited technical skills can leverage automation for their analytical needs.</div>""",
    
    "Target Audience": """
    <div class='custom-bullet'>Public health officials and analysts working within NMCPs who require efficient mapping and data analysis solutions.</div>
    <div class='custom-bullet'>Data managers and decision-makers seeking to improve operational efficiency and responsiveness to health challenges.</div>
    <div class='custom-bullet'>Organizations interested in integrating automation into their workflows to enhance data-driven decision-making capabilities.</div>""",
    
    "Conclusion": """The adoption of this automated system for SNT analysis represents a transformative opportunity for NMCPs. By significantly reducing the time and effort required for these tasks, programs can enhance their efficiency, improve the quality of their analyses, and ultimately lead to more timely and informed decision-making. This tool, built on the experience of the 2023 SNT implementation, not only addresses existing operational challenges but also empowers analysts to focus on deriving insights rather than getting lost in technical details. The user-friendly interface and high processing speed make it an invaluable asset for regular SNT updates and monitoring of malaria control activities."""
}

# Display sections in a single column
for title, content in sections.items():
    st.markdown(f"""
        <div class="section-card">
            <div class="section-header">{title}</div>
            <div class="content-text">{content}</div>
        </div>
    """, unsafe_allow_html=True)

# Add a footer
st.markdown("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #333; position: relative; z-index: 1;">
        <p style="color: #888;">© 2025 National Malaria Control Program. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True)
