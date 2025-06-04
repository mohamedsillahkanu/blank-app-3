import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Set page configuration
st.set_page_config(
    page_title="Solution Center - Find Any Service",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color theme - exact blue and white palette from original design
COLORS = {
    "primary": "#1E88E5",       # Primary blue
    "secondary": "#90CAF9",     # Light blue
    "background": "#E3F2FD",    # Very light blue background
    "text": "#0D47A1",          # Dark blue text
    "accent": "#64B5F6",        # Accent blue
    "white": "#FFFFFF",
    "light_gray": "#F1F5F9"
}

# Sample data for services (in real app, this would come from a database)
SAMPLE_SERVICES = [
    {
        "name": "Salone Elite Tailoring",
        "category": "Fashion & Clothing",
        "subcategory": "Tailoring",
        "city": "Freetown",
        "area": "Aberdeen",
        "district": "Western Area Urban",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-76-123-456",
        "email": "info@saloneelite.sl",
        "rating": 4.8,
        "price_range": "$",
        "description": "Premium tailoring services for men and women. Custom suits, traditional wear, and geles for special occasions.",
        "services": ["Custom Suits", "Traditional Wear", "Gele Tying", "Wedding Outfits", "Kaba & Slits"]
    },
    {
        "name": "Kamara Car Rentals",
        "category": "Transportation",
        "subcategory": "Car Rental",
        "city": "Freetown",
        "area": "Lumley",
        "district": "Western Area Urban",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-88-765-432",
        "email": "bookings@kamaracars.sl",
        "rating": 4.5,
        "price_range": "$$",
        "description": "Reliable car rental services with well-maintained vehicles. Airport transfers and city tours available.",
        "services": ["Economy Cars", "SUVs", "Lungi Airport Transfers", "City Tours", "Wedding Cars"]
    },
    {
        "name": "Aminata's Beauty Palace",
        "category": "Beauty & Wellness",
        "subcategory": "Hair Salon",
        "city": "Bo",
        "area": "Bo Town Center",
        "district": "Bo District",
        "country": "Sierra Leone",
        "gender_served": "Women",
        "phone": "+232-76-456-789",
        "email": "aminata@beautypalace.sl",
        "rating": 4.9,
        "price_range": "$",
        "description": "Full-service beauty salon specializing in natural hair care, braiding, and traditional Sierra Leonean styles.",
        "services": ["Natural Hair Care", "Braiding", "Locs Maintenance", "Makeup", "Henna Designs"]
    },
    {
        "name": "TechFix Salone",
        "category": "Technology",
        "subcategory": "Computer Repair",
        "city": "Freetown",
        "area": "Congo Cross",
        "district": "Western Area Urban",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-77-123-456",
        "email": "support@techfixsalone.sl",
        "rating": 4.6,
        "price_range": "$",
        "description": "Professional computer and mobile device repair services. Software installation and data recovery.",
        "services": ["Laptop Repair", "Phone Repair", "Data Recovery", "Software Installation", "CCTV Setup"]
    },
    {
        "name": "Mama Fatmata's Kitchen",
        "category": "Food & Catering",
        "subcategory": "Catering",
        "city": "Kenema",
        "area": "Kenema City",
        "district": "Kenema District",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-76-987-654",
        "email": "orders@mamafatmata.sl",
        "rating": 4.7,
        "price_range": "$",
        "description": "Authentic Sierra Leonean cuisine for events and daily meals. Specializing in jollof rice, cassava leaves, and groundnut soup.",
        "services": ["Event Catering", "Daily Meals", "Traditional Dishes", "Wedding Catering", "Corporate Lunch"]
    },
    {
        "name": "Green Hills Landscaping",
        "category": "Home & Garden",
        "subcategory": "Landscaping",
        "city": "Freetown",
        "area": "Hill Station",
        "district": "Western Area Rural",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-88-234-567",
        "email": "info@greenhills.sl",
        "rating": 4.4,
        "price_range": "$$",
        "description": "Professional landscaping and garden maintenance services for residential and commercial properties.",
        "services": ["Garden Design", "Lawn Maintenance", "Tree Planting", "Irrigation Systems", "Compound Cleaning"]
    },
    {
        "name": "Salone Express Logistics",
        "category": "Transportation",
        "subcategory": "Logistics",
        "city": "Makeni",
        "area": "Makeni Town",
        "district": "Bombali District",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-76-345-678",
        "email": "info@saloneexpress.sl",
        "rating": 4.3,
        "price_range": "$",
        "description": "Reliable logistics and delivery services across Sierra Leone. Same-day delivery in major cities.",
        "services": ["Package Delivery", "Moving Services", "Cargo Transport", "Same-Day Delivery", "Interstate Transport"]
    },
    {
        "name": "Dr. Bangura Medical Clinic",
        "category": "Health & Medical",
        "subcategory": "Clinics",
        "city": "Freetown",
        "area": "Kissy Street",
        "district": "Western Area Urban",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-22-123-456",
        "email": "clinic@drbangura.sl",
        "rating": 4.6,
        "price_range": "$",
        "description": "Full-service medical clinic providing quality healthcare services. General practice and specialist consultations.",
        "services": ["General Consultation", "Laboratory Tests", "Vaccination", "Health Checkups", "Emergency Care"]
    },
    {
        "name": "Salone Skills Academy",
        "category": "Education",
        "subcategory": "Training Centers",
        "city": "Freetown",
        "area": "Fourah Bay",
        "district": "Western Area Urban",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-76-789-012",
        "email": "info@saloneskills.sl",
        "rating": 4.5,
        "price_range": "$",
        "description": "Professional training center offering skills development in technology, business, and vocational trades.",
        "services": ["Computer Training", "Business Skills", "Vocational Training", "English Classes", "Digital Literacy"]
    },
    {
        "name": "Njala Agricultural Services",
        "category": "Professional Services",
        "subcategory": "Agricultural Consulting",
        "city": "Njala",
        "area": "Njala University Area",
        "district": "Moyamba District",
        "country": "Sierra Leone",
        "gender_served": "All",
        "phone": "+232-77-456-789",
        "email": "info@njalaagri.sl",
        "rating": 4.4,
        "price_range": "$",
        "description": "Agricultural consulting and farming services. Crop management, soil testing, and farming equipment rental.",
        "services": ["Crop Consulting", "Soil Testing", "Equipment Rental", "Irrigation Setup", "Pest Control"]
    }
]

# Service categories and subcategories
SERVICE_CATEGORIES = {
    "Fashion & Clothing": ["Tailoring", "Shoe Repair", "Dry Cleaning", "Fashion Design", "Gele Tying"],
    "Transportation": ["Car Rental", "Taxi Service", "Logistics", "Moving Services", "Okada (Motorcycle)", "Poda Poda"],
    "Beauty & Wellness": ["Hair Salon", "Barber Shop", "Spa", "Fitness Center", "Massage Therapy", "Traditional Medicine"],
    "Technology": ["Computer Repair", "Phone Repair", "Web Development", "IT Support", "CCTV Installation"],
    "Food & Catering": ["Catering", "Restaurant", "Food Delivery", "Baking", "Street Food"],
    "Home & Garden": ["Landscaping", "Cleaning Service", "Plumbing", "Electrical", "Carpentry", "Roofing"],
    "Professional Services": ["Legal Services", "Accounting", "Consulting", "Real Estate", "Agricultural Consulting"],
    "Education": ["Tutoring", "Training Centers", "Language Classes", "Skill Development", "Computer Training"],
    "Health & Medical": ["Clinics", "Pharmacy", "Dental Care", "Traditional Healing", "Laboratory Services"],
    "Entertainment": ["Event Planning", "Photography", "Music", "DJ Services", "Traditional Dancing"],
    "Agriculture": ["Farming Services", "Equipment Rental", "Crop Consulting", "Livestock", "Fish Farming"],
    "Construction": ["Building Construction", "Road Construction", "Renovation", "Painting", "Tiling"]
}

# CSS for styling
def get_css():
    return f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, {COLORS["background"]} 0%, {COLORS["primary"]} 100%);
            min-height: 100vh;
        }}
        
        .main-header {{
            background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        
        .search-container {{
            background: {COLORS["white"]};
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .service-card {{
            background: {COLORS["white"]};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid {COLORS["accent"]};
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}
        
        .service-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .service-name {{
            color: {COLORS["primary"]};
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .service-category {{
            background: {COLORS["secondary"]};
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            display: inline-block;
            margin-bottom: 10px;
        }}
        
        .service-location {{
            color: {COLORS["text"]};
            font-weight: 500;
            margin-bottom: 8px;
        }}
        
        .service-rating {{
            color: #FFA500;
            font-weight: bold;
        }}
        
        .service-contact {{
            background: {COLORS["light_gray"]};
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
        }}
        
        .filter-section {{
            background: {COLORS["white"]};
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .stats-container {{
            display: flex;
            justify-content: space-around;
            background: {COLORS["white"]};
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: {COLORS["primary"]};
        }}
        
        .stat-label {{
            color: {COLORS["text"]};
            font-size: 0.9em;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: {COLORS["text"]};
            background: {COLORS["white"]};
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
    </style>
    """

def get_greeting():
    current_hour = datetime.now().hour
    if current_hour < 12:
        return "Good Morning"
    elif current_hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"

# Initialize session state for modal
if 'selected_service' not in st.session_state:
    st.session_state.selected_service = None
if 'show_modal' not in st.session_state:
    st.session_state.show_modal = False

def get_sample_products(service_category):
    """Get sample product images based on service category"""
    product_samples = {
        "Fashion & Clothing": [
            {"icon": "👔", "name": "Custom Suits"},
            {"icon": "👗", "name": "Traditional Wear"},
            {"icon": "👒", "name": "Accessories"},
            {"icon": "🧵", "name": "Alterations"},
            {"icon": "👜", "name": "Bags & Purses"},
            {"icon": "👠", "name": "Shoes & Footwear"}
        ],
        "Transportation": [
            {"icon": "🚗", "name": "Economy Cars"},
            {"icon": "🚙", "name": "SUVs"},
            {"icon": "🏍️", "name": "Motorcycles"},
            {"icon": "🚐", "name": "Vans"},
            {"icon": "🛻", "name": "Pickup Trucks"},
            {"icon": "🚕", "name": "Luxury Cars"}
        ],
        "Beauty & Wellness": [
            {"icon": "💇", "name": "Hair Styling"},
            {"icon": "💅", "name": "Nail Care"},
            {"icon": "💄", "name": "Makeup"},
            {"icon": "🧴", "name": "Hair Products"},
            {"icon": "🌿", "name": "Natural Treatments"},
            {"icon": "✨", "name": "Spa Services"}
        ],
        "Technology": [
            {"icon": "💻", "name": "Laptops"},
            {"icon": "📱", "name": "Mobile Phones"},
            {"icon": "🖥️", "name": "Desktop PCs"},
            {"icon": "📷", "name": "Cameras"},
            {"icon": "🎮", "name": "Gaming"},
            {"icon": "⌚", "name": "Smart Watches"}
        ],
        "Food & Catering": [
            {"icon": "🍛", "name": "Jollof Rice"},
            {"icon": "🥘", "name": "Traditional Dishes"},
            {"icon": "🎂", "name": "Cakes & Desserts"},
            {"icon": "🥤", "name": "Beverages"},
            {"icon": "🍖", "name": "Grilled Meats"},
            {"icon": "🥗", "name": "Salads & Sides"}
        ],
        "Home & Garden": [
            {"icon": "🌺", "name": "Flower Gardens"},
            {"icon": "🌳", "name": "Trees & Plants"},
            {"icon": "🏡", "name": "Landscaping"},
            {"icon": "🚿", "name": "Plumbing"},
            {"icon": "💡", "name": "Electrical"},
            {"icon": "🔨", "name": "Carpentry"}
        ],
        "Professional Services": [
            {"icon": "⚖️", "name": "Legal Documents"},
            {"icon": "📊", "name": "Accounting"},
            {"icon": "📈", "name": "Consulting"},
            {"icon": "🏠", "name": "Real Estate"},
            {"icon": "📝", "name": "Business Plans"},
            {"icon": "💼", "name": "Corporate Services"}
        ],
        "Education": [
            {"icon": "📚", "name": "Books & Materials"},
            {"icon": "💻", "name": "Computer Training"},
            {"icon": "🌍", "name": "Language Classes"},
            {"icon": "🎓", "name": "Certificates"},
            {"icon": "✏️", "name": "Tutoring"},
            {"icon": "🔬", "name": "Science Labs"}
        ],
        "Health & Medical": [
            {"icon": "🩺", "name": "Medical Checkups"},
            {"icon": "💊", "name": "Medications"},
            {"icon": "🧪", "name": "Lab Tests"},
            {"icon": "🦷", "name": "Dental Care"},
            {"icon": "👁️", "name": "Eye Care"},
            {"icon": "🚑", "name": "Emergency Services"}
        ],
        "Entertainment": [
            {"icon": "🎵", "name": "Music Events"},
            {"icon": "📸", "name": "Photography"},
            {"icon": "🎥", "name": "Videography"},
            {"icon": "🎤", "name": "DJ Services"},
            {"icon": "🎊", "name": "Event Planning"},
            {"icon": "🎭", "name": "Entertainment"}
        ],
        "Agriculture": [
            {"icon": "🌾", "name": "Crop Farming"},
            {"icon": "🐄", "name": "Livestock"},
            {"icon": "🐟", "name": "Fish Farming"},
            {"icon": "🚜", "name": "Farm Equipment"},
            {"icon": "🌱", "name": "Seeds & Plants"},
            {"icon": "💧", "name": "Irrigation"}
        ],
        "Construction": [
            {"icon": "🏗️", "name": "Building Construction"},
            {"icon": "🛤️", "name": "Road Construction"},
            {"icon": "🎨", "name": "Painting"},
            {"icon": "🧱", "name": "Masonry"},
            {"icon": "🔧", "name": "Roofing"},
            {"icon": "⚡", "name": "Electrical Work"}
        ]
    }
    
    # Return default if category not found
    return product_samples.get(service_category, [
        {"icon": "📦", "name": "Product 1"},
        {"icon": "📦", "name": "Product 2"},
        {"icon": "📦", "name": "Product 3"},
        {"icon": "📦", "name": "Product 4"},
        {"icon": "📦", "name": "Product 5"},
        {"icon": "📦", "name": "Product 6"}
    ])

def display_service_modal(service):
    """Display service details in a modal with product gallery"""
    if not st.session_state.show_modal or not service:
        return
    
    # Get sample products for this service category
    products = get_sample_products(service["category"])
    
    modal_html = f"""
    <div class="service-modal" onclick="this.style.display='none'">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <button class="close-button" onclick="this.parentElement.parentElement.parentElement.style.display='none'">×</button>
                <h2>{service["name"]}</h2>
                <p>{service["category"]} - {service["subcategory"]}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <h3 style="color: {COLORS['text']}; margin-bottom: 15px;">📍 Location & Contact</h3>
                <div style="background-color: {COLORS['background']}; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p><strong>Address:</strong> {service["area"]}, {service["city"]}, {service["district"]}</p>
                    <p><strong>Phone:</strong> {service["phone"]}</p>
                    <p><strong>Email:</strong> {service["email"]}</p>
                    <p><strong>Rating:</strong> {'⭐' * int(service["rating"])} {service["rating"]}/5.0</p>
                    <p><strong>Price Range:</strong> {service["price_range"]}</p>
                    <p><strong>Gender Served:</strong> {service["gender_served"]}</p>
                </div>
                
                <h3 style="color: {COLORS['text']}; margin-bottom: 15px;">📝 About This Service</h3>
                <div style="background-color: {COLORS['secondary']}; color: {COLORS['text']}; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p>{service["description"]}</p>
                </div>
                
                <h3 style="color: {COLORS['text']}; margin-bottom: 15px;">🛍️ Services & Products</h3>
                <div style="margin-bottom: 20px;">
                    <p><strong>Available Services:</strong> {", ".join(service["services"])}</p>
                </div>
                
                <h3 style="color: {COLORS['text']}; margin-bottom: 15px;">📸 Sample Products/Services</h3>15px;">🛍️ Services & Products</h3>
                <div style="margin-bottom: 20px;">
                    <p><strong>Available Services:</strong> {", ".join(service["services"])}</p>
                </div>
                
                <h3 style="color: {COLORS['primary']}; margin-bottom: 15px;">📸 Sample Products/Services</h3>
                <div class="product-gallery">
    """
    
    # Add product images
    for product in products:
        modal_html += f"""
                    <div>
                        <div class="product-image">{product["icon"]}</div>
                        <div class="product-label">{product["name"]}</div>
                    </div>
        """
    
    modal_html += f"""
                </div>
                
                <div style="margin-top: 30px; text-align: center;">
                    <button onclick="this.parentElement.parentElement.parentElement.parentElement.style.display='none'" 
                            style="background: {COLORS['primary']}; color: white; padding: 12px 30px; border: none; border-radius: 25px; font-size: 1.1em; font-weight: bold; cursor: pointer;">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(modal_html, unsafe_allow_html=True)
    """Display a service in a card format with fixed dimensions"""
    rating_stars = "⭐" * int(service["rating"])
    
    card_html = f"""
    <div class="service-card">
        <div class="service-card-content">
            <div class="service-name">{service["name"]}</div>
            <div class="service-category">{service["category"]} - {service["subcategory"]}</div>
            <div class="service-location">📍 {service["area"]}, {service["city"]}, {service["district"]}</div>
            <div class="service-rating">{rating_stars} {service["rating"]}/5.0 | {service["price_range"]}</div>
            <div class="service-description">{service["description"]}</div>
            <div class="service-services"><strong>Services:</strong> {", ".join(service["services"])}</div>
            <div class="service-gender"><strong>Gender Served:</strong> {service["gender_served"]}</div>
            <div class="service-contact">
                <strong>Contact:</strong><br>
                📞 {service["phone"]}<br>
                📧 {service["email"]}
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def filter_services(services, filters):
    """Filter services based on user criteria"""
    filtered = services.copy()
    
    # Filter by search query
    if filters.get("search_query"):
        query = filters["search_query"].lower()
        filtered = [s for s in filtered if 
                   query in s["name"].lower() or 
                   query in s["description"].lower() or 
                   query in s["category"].lower() or
                   query in s["subcategory"].lower() or
                   any(query in service.lower() for service in s["services"])]
    
    # Filter by category
    if filters.get("category") and filters["category"] != "All Categories":
        filtered = [s for s in filtered if s["category"] == filters["category"]]
    
    # Filter by subcategory
    if filters.get("subcategory") and filters["subcategory"] != "All Subcategories":
        filtered = [s for s in filtered if s["subcategory"] == filters["subcategory"]]
    
    # Filter by district
    if filters.get("district") and filters["district"] != "All Districts":
        filtered = [s for s in filtered if s["district"] == filters["district"]]
    
    # Filter by city
    if filters.get("city") and filters["city"] != "All Cities":
        filtered = [s for s in filtered if s["city"] == filters["city"]]
    
    # Filter by area
    if filters.get("area") and filters["area"] != "All Areas":
        filtered = [s for s in filtered if s["area"] == filters["area"]]
    
    # Filter by gender
    if filters.get("gender") and filters["gender"] != "All":
        filtered = [s for s in filtered if s["gender_served"] in ["All", filters["gender"]]]
    
    # Filter by rating
    if filters.get("min_rating"):
        filtered = [s for s in filtered if s["rating"] >= filters["min_rating"]]
    
    # Filter by price range
    if filters.get("price_range") and filters["price_range"] != "Any Price":
        filtered = [s for s in filtered if s["price_range"] == filters["price_range"]]
    
    return filtered

def main():
    # Apply custom CSS
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # Main header
    header_html = f"""
    <div class="main-header">
        <h1>🔍 Solution Center</h1>
        <h3>Find Any Service, Anywhere, Anytime</h3>
        <p>{get_greeting()} | {datetime.now().strftime("%A, %B %d, %Y")}</p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Statistics section
    total_services = len(SAMPLE_SERVICES)
    total_categories = len(SERVICE_CATEGORIES)
    total_cities = len(set(s["city"] for s in SAMPLE_SERVICES))
    total_districts = len(set(s["district"] for s in SAMPLE_SERVICES))
    avg_rating = sum(s["rating"] for s in SAMPLE_SERVICES) / len(SAMPLE_SERVICES)
    
    stats_html = f"""
    <div class="stats-container">
        <div class="stat-item">
            <div class="stat-number">{total_services}+</div>
            <div class="stat-label">Services Listed</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{total_categories}</div>
            <div class="stat-label">Categories</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{total_districts}</div>
            <div class="stat-label">Districts Covered</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{avg_rating:.1f}</div>
            <div class="stat-label">Avg Rating</div>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)
    
    # Search and Filter Section
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Search bar
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search for any service...", 
                                   placeholder="e.g., tailoring, car rental, beauty salon")
    with col2:
        search_button = st.button("Search", type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced Filters
    with st.expander("🎯 Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Category filter
            categories = ["All Categories"] + list(SERVICE_CATEGORIES.keys())
            selected_category = st.selectbox("Category", categories)
            
            # Subcategory filter (dynamic based on category)
            if selected_category != "All Categories":
                subcategories = ["All Subcategories"] + SERVICE_CATEGORIES[selected_category]
            else:
                all_subcategories = []
                for cat_subs in SERVICE_CATEGORIES.values():
                    all_subcategories.extend(cat_subs)
                subcategories = ["All Subcategories"] + list(set(all_subcategories))
            
            selected_subcategory = st.selectbox("Subcategory", subcategories)
        
        with col2:
            # Location filters
            districts = ["All Districts"] + sorted(list(set(s["district"] for s in SAMPLE_SERVICES)))
            selected_district = st.selectbox("District", districts)
            
            # Cities (dynamic based on district)
            if selected_district != "All Districts":
                cities = ["All Cities"] + sorted([s["city"] for s in SAMPLE_SERVICES if s["district"] == selected_district])
            else:
                cities = ["All Cities"] + sorted(list(set(s["city"] for s in SAMPLE_SERVICES)))
            
            selected_city = st.selectbox("City", cities)
            
            # Areas (dynamic based on city)
            if selected_city != "All Cities":
                areas = ["All Areas"] + sorted([s["area"] for s in SAMPLE_SERVICES if s["city"] == selected_city])
            else:
                areas = ["All Areas"] + sorted(list(set(s["area"] for s in SAMPLE_SERVICES)))
            
            selected_area = st.selectbox("Area", areas)
        
        with col3:
            # Other filters
            selected_gender = st.selectbox("Gender Preference", ["All", "Men", "Women"])
            min_rating = st.select_slider("Minimum Rating", 
                                        options=[1.0, 2.0, 3.0, 4.0, 4.5, 5.0],
                                        value=1.0)
            price_ranges = ["Any Price", "$", "$$", "$$$"]
            selected_price = st.selectbox("Price Range", price_ranges)
    
    # Compile filters
    filters = {
        "search_query": search_query,
        "category": selected_category,
        "subcategory": selected_subcategory,
        "district": selected_district,
        "city": selected_city,
        "area": selected_area,
        "gender": selected_gender,
        "min_rating": min_rating,
        "price_range": selected_price
    }
    
    # Filter services
    filtered_services = filter_services(SAMPLE_SERVICES, filters)
    
    # Sort options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_by = st.selectbox("Sort by", ["Rating (High to Low)", "Rating (Low to High)", 
                                         "Name (A-Z)", "Name (Z-A)"])
    
    # Apply sorting
    if sort_by == "Rating (High to Low)":
        filtered_services.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "Rating (Low to High)":
        filtered_services.sort(key=lambda x: x["rating"])
    elif sort_by == "Name (A-Z)":
        filtered_services.sort(key=lambda x: x["name"])
    elif sort_by == "Name (Z-A)":
        filtered_services.sort(key=lambda x: x["name"], reverse=True)
    
    # Display results
    st.markdown(f"### Found {len(filtered_services)} service(s)")
    
    if filtered_services:
        # Display services in a grid
        for i in range(0, len(filtered_services), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                display_service_card(filtered_services[i])
            
            if i + 1 < len(filtered_services):
                with col2:
                    display_service_card(filtered_services[i + 1])
    
    # Display modal if a service is selected
    if st.session_state.show_modal and st.session_state.selected_service:
        display_service_modal(st.session_state.selected_service)
        
        # Add a close button in the sidebar or main area
        if st.button("❌ Close Details", type="secondary"):
            st.session_state.show_modal = False
            st.session_state.selected_service = None
            st.rerun()
    else:
        # No results found
        no_results_html = f"""
        <div class="no-results">
            <h3>🔍 No Services Found</h3>
            <p>Try adjusting your search criteria or filters.</p>
            <p><strong>Suggestions:</strong></p>
            <ul style="text-align: left; display: inline-block;">
                <li>Use broader search terms</li>
                <li>Remove some filters</li>
                <li>Check spelling</li>
                <li>Try searching by category instead</li>
            </ul>
        </div>
        """
        st.markdown(no_results_html, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    
    # Add service section
    with st.expander("📝 Add Your Service to Solution Center"):
        st.markdown("**Are you a service provider?** Join our platform to reach more customers!")
        
        with st.form("add_service_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                business_name = st.text_input("Business Name*")
                business_category = st.selectbox("Category*", list(SERVICE_CATEGORIES.keys()))
                business_phone = st.text_input("Phone Number*")
                business_email = st.text_input("Email Address*")
            
            with col2:
                business_city = st.text_input("City*")
                business_area = st.text_input("Area*")
                business_district = st.text_input("District*")
                business_gender = st.selectbox("Gender Served", ["All", "Men", "Women"])
            
            business_description = st.text_area("Business Description*")
            business_services = st.text_input("Services Offered (comma-separated)*")
            
            submitted = st.form_submit_button("Submit for Review")
            
            if submitted:
                if business_name and business_category and business_phone and business_email:
                    st.success("Thank you! Your service has been submitted for review. We'll contact you within 24 hours.")
                else:
                    st.error("Please fill in all required fields (*)")
    
    # Footer
    footer_html = f"""
    <div style="background: {COLORS['primary']}; color: white; padding: 20px; border-radius: 12px; margin-top: 30px; text-align: center;">
        <h4>Solution Center Sierra Leone</h4>
        <p>Your trusted directory for all services across Salone | © 2025 Solution Center SL</p>
        <p>📧 info@solutioncenter.sl | 📞 +232-76-SOLUTION</p>
        <p><small>Connecting you to the best services from Freetown to Bo, Kenema to Makeni</small></p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
