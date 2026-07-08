import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import hashlib, json, os, datetime, re

# ─────────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────────
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)
_PW_HAS_LETTER = re.compile(r"[a-zA-Z]")
_PW_HAS_DIGIT  = re.compile(r"[0-9]")

def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))

def is_valid_password(pw: str) -> bool:
    return (
        len(pw) >= 6
        and bool(_PW_HAS_LETTER.search(pw))
        and bool(_PW_HAS_DIGIT.search(pw))
    )

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Roommate Matchmaker", page_icon="🏠", layout="wide",
                   initial_sidebar_state="expanded")

USERS_FILE = "users.json"
CSV_FILE   = "hostel_users_clustered.csv"
RENT_ORDER = ["Rs.3K-5K","Rs.5K-8K","Rs.8K-12K","Rs.12K-20K"]
ALL_AREAS  = ["Koramangala","Indiranagar","HSR Layout","Whitefield","BTM Layout","Marathahalli"]
FOOD_OPTS  = ["Vegetarian","Non-Vegetarian","Eggetarian"]
MAJORS     = ["CSE","ECE","Mech","Civil","IT","AI&DS"]

# ─────────────────────────────────────────────
# HOSTEL DATABASE  (static, curated for Bengaluru)
# ─────────────────────────────────────────────
HOSTELS = [
    {
        "name": "Stanza Living – Koramangala",
        "area": "Koramangala",
        "address": "3rd Block, Koramangala, Bengaluru – 560034",
        "price_range": "₹8,000 – ₹14,000/mo",
        "price_min": 8000,
        "rating": 4.5,
        "reviews": 312,
        "distance_km": 0.4,
        "tags": ["WiFi","AC","Meals","Laundry","CCTV","Study Room"],
        "gender": "Co-ed",
        "food": "Vegetarian",
        "maps_url": "https://www.google.com/maps/search/Stanza+Living+Koramangala+Bengaluru",
        "emoji": "🏢",
        "highlight": "Top Rated",
        "highlight_color": "#2E7D32",
        "photos": [
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Bedroom", "Common Hall", "Study Room"],
    },
    {
        "name": "Zolo Stay – HSR Layout",
        "area": "HSR Layout",
        "address": "Sector 1, HSR Layout, Bengaluru – 560102",
        "price_range": "₹6,500 – ₹11,000/mo",
        "price_min": 6500,
        "rating": 4.3,
        "reviews": 198,
        "distance_km": 1.2,
        "tags": ["WiFi","Meals","Housekeeping","Power Backup","Gym"],
        "gender": "Co-ed",
        "food": "Both",
        "maps_url": "https://www.google.com/maps/search/Zolo+Stay+HSR+Layout+Bengaluru",
        "emoji": "🏠",
        "highlight": "Best Value",
        "highlight_color": "#1565C0",
        "photos": [
            "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Bedroom", "Lounge Area", "Kitchen"],
    },
    {
        "name": "Your Space – Indiranagar",
        "area": "Indiranagar",
        "address": "12th Main Rd, Indiranagar, Bengaluru – 560008",
        "price_range": "₹10,000 – ₹18,000/mo",
        "price_min": 10000,
        "rating": 4.6,
        "reviews": 427,
        "distance_km": 2.8,
        "tags": ["WiFi","AC","Meals","Gym","Rooftop","CCTV","Housekeeping"],
        "gender": "Co-ed",
        "food": "Vegetarian",
        "maps_url": "https://www.google.com/maps/search/Your+Space+Hostel+Indiranagar+Bengaluru",
        "emoji": "🌟",
        "highlight": "Premium",
        "highlight_color": "#7B1FA2",
        "photos": [
            "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1560448204-603b3fc33ddc?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Premium Bedroom", "Common Hall", "Rooftop"],
    },
    {
        "name": "OYO Life – Whitefield",
        "area": "Whitefield",
        "address": "ITPL Main Rd, Whitefield, Bengaluru – 560066",
        "price_range": "₹5,500 – ₹9,000/mo",
        "price_min": 5500,
        "rating": 4.1,
        "reviews": 156,
        "distance_km": 8.5,
        "tags": ["WiFi","TV","Meals","Laundry","24×7 Security"],
        "gender": "Co-ed",
        "food": "Both",
        "maps_url": "https://www.google.com/maps/search/OYO+Life+Whitefield+Bengaluru",
        "emoji": "🏨",
        "highlight": "Budget Pick",
        "highlight_color": "#E65100",
        "photos": [
            "https://images.unsplash.com/photo-1505693314120-0d443867891c?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1484101403633-562f891dc89a?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Bedroom", "Common Area", "Dining Hall"],
    },
    {
        "name": "Moustache Hostel – BTM Layout",
        "area": "BTM Layout",
        "address": "2nd Stage, BTM Layout, Bengaluru – 560076",
        "price_range": "₹4,500 – ₹7,500/mo",
        "price_min": 4500,
        "rating": 4.2,
        "reviews": 89,
        "distance_km": 3.1,
        "tags": ["WiFi","Common Kitchen","Lounge","Lockers","Events"],
        "gender": "Co-ed",
        "food": "Vegetarian",
        "maps_url": "https://www.google.com/maps/search/Moustache+Hostel+BTM+Layout+Bengaluru",
        "emoji": "🎒",
        "highlight": "Social Hub",
        "highlight_color": "#00695C",
        "photos": [
            "https://images.unsplash.com/photo-1520277739336-7bf67edfa768?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=400&h=220&fit=crop&crop=left",
            "https://images.unsplash.com/photo-1529408686214-2f2e8292a0e3?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Dorm Room", "Social Lounge", "Common Kitchen"],
    },
    {
        "name": "Colive – Marathahalli",
        "area": "Marathahalli",
        "address": "Outer Ring Road, Marathahalli, Bengaluru – 560037",
        "price_range": "₹7,000 – ₹12,000/mo",
        "price_min": 7000,
        "rating": 4.4,
        "reviews": 241,
        "distance_km": 5.6,
        "tags": ["WiFi","AC","Meals","Gym","Study Room","Housekeeping","Pool Table"],
        "gender": "Co-ed",
        "food": "Both",
        "maps_url": "https://www.google.com/maps/search/Colive+Marathahalli+Bengaluru",
        "emoji": "🏙️",
        "highlight": "Tech Hub",
        "highlight_color": "#1976D2",
        "photos": [
            "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1571508601891-ca5e7a713859?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=400&h=220&fit=crop&crop=right",
        ],
        "photo_labels": ["AC Bedroom", "Gym Area", "Study Room"],
    },
    {
        "name": "GirlsOnly PG – Koramangala",
        "area": "Koramangala",
        "address": "5th Block, Koramangala, Bengaluru – 560095",
        "price_range": "₹6,000 – ₹10,000/mo",
        "price_min": 6000,
        "rating": 4.7,
        "reviews": 183,
        "distance_km": 0.9,
        "tags": ["WiFi","Meals","AC","Laundry","CCTV","Wardrobe"],
        "gender": "Female Only",
        "food": "Vegetarian",
        "maps_url": "https://www.google.com/maps/search/Girls+PG+Koramangala+5th+Block+Bengaluru",
        "emoji": "👩",
        "highlight": "Women's Safe Space",
        "highlight_color": "#C2185B",
        "photos": [
            "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?w=400&h=220&fit=crop&crop=right",
            "https://images.unsplash.com/photo-1560185127-6ed189bf02f4?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Cozy Bedroom", "Common Hall", "Wardrobe Room"],
    },
    {
        "name": "NestAway – Indiranagar",
        "area": "Indiranagar",
        "address": "100 Feet Rd, Indiranagar, Bengaluru – 560038",
        "price_range": "₹9,000 – ₹16,000/mo",
        "price_min": 9000,
        "rating": 4.0,
        "reviews": 302,
        "distance_km": 3.3,
        "tags": ["WiFi","Furnished","24×7 Support","Maintenance","No Brokerage"],
        "gender": "Co-ed",
        "food": "Both",
        "maps_url": "https://www.google.com/maps/search/NestAway+Indiranagar+Bengaluru",
        "emoji": "🔑",
        "highlight": "No Brokerage",
        "highlight_color": "#37474F",
        "photos": [
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=400&h=220&fit=crop",
            "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?w=400&h=220&fit=crop",
        ],
        "photo_labels": ["Furnished Room", "Living Area", "Dining Space"],
    },
]

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ═══════════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

:root {
  --accent:       #E8432D;
  --accent-light: #FFF1EE;
  --accent-mid:   #FFDDD8;
  --ink:          #0F1117;
  --ink-2:        #374151;
  --ink-3:        #6B7280;
  --ink-4:        #9CA3AF;
  --ink-5:        #D1D5DB;
  --surface:      #FFFFFF;
  --surface-2:    #F9FAFB;
  --surface-3:    #F3F4F6;
  --border:       #E5E7EB;
  --border-light: #F3F4F6;
  --radius-sm:    8px;
  --radius-md:    12px;
  --radius-lg:    18px;
  --radius-xl:    24px;
  --shadow-xs:    0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
  --shadow-sm:    0 2px 8px rgba(0,0,0,.06),0 1px 3px rgba(0,0,0,.04);
  --shadow-md:    0 4px 20px rgba(0,0,0,.07),0 2px 6px rgba(0,0,0,.04);
  --shadow-lg:    0 10px 40px rgba(0,0,0,.10),0 4px 12px rgba(0,0,0,.05);
  --font:         'DM Sans', sans-serif;
  --font-mono:    'DM Mono', monospace;
  --ease:         cubic-bezier(.16,1,.3,1);
}

/* ═══════════════════════════════════════════════
   BASE RESET & APP SHELL
═══════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }
* { font-family: var(--font) !important; }
.stApp { background: var(--surface-2) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

/* ═══════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
  padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 1.25rem 1rem !important; }
[data-testid="stSidebar"] label {
  font-weight: 600 !important;
  color: var(--ink-2) !important;
  font-size: 0.8rem !important;
  letter-spacing: .01em !important;
  text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stSlider { padding: 0 !important; }
[data-testid="stSidebar"] hr { border-color: var(--border-light) !important; margin: 0.75rem 0 !important; }

/* ═══════════════════════════════════════════════
   SLIDERS
═══════════════════════════════════════════════ */
div.stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"] {
  background-color: var(--accent) !important;
  box-shadow: 0 0 0 4px rgba(232,67,45,.15) !important;
}
div.stSlider > div[data-baseweb="slider"] > div > div { background: var(--accent) !important; }

/* ═══════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════ */
div.stButton > button {
  background: var(--ink) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  padding: .7rem 1.25rem !important;
  font-weight: 700 !important;
  font-size: .88rem !important;
  letter-spacing: .01em !important;
  width: 100% !important;
  transition: background .2s var(--ease), transform .15s var(--ease), box-shadow .2s var(--ease) !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.08), 0 0 0 1px rgba(0,0,0,.04) !important;
}
div.stButton > button:hover {
  background: #000 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,.18) !important;
}
div.stButton > button:active { transform: translateY(0) !important; }

/* ═══════════════════════════════════════════════
   TABS — SEGMENTED CONTROL
═══════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface-3) !important;
  border-radius: var(--radius-md) !important;
  padding: 4px !important;
  gap: 2px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--ink-3) !important;
  font-weight: 600 !important;
  font-size: .875rem !important;
  border-radius: 9px !important;
  padding: .5rem 1.25rem !important;
  flex: 1 !important;
  justify-content: center !important;
  transition: all .18s var(--ease) !important;
}
.stTabs [aria-selected="true"] {
  background: var(--surface) !important;
  color: var(--ink) !important;
  box-shadow: var(--shadow-xs) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ═══════════════════════════════════════════════
   INPUTS & SELECTS
═══════════════════════════════════════════════ */
.stTextInput input, .stSelectbox select,
[data-baseweb="input"] input,
[data-baseweb="select"] > div:first-child {
  border-radius: var(--radius-sm) !important;
  border: 1.5px solid var(--border) !important;
  background: var(--surface) !important;
  font-size: .88rem !important;
  transition: border-color .15s, box-shadow .15s !important;
}
.stTextInput input:focus,
[data-baseweb="input"] input:focus {
  border-color: var(--ink) !important;
  box-shadow: 0 0 0 3px rgba(15,17,23,.07) !important;
}
.stTextInput label, .stSelectbox label,
[data-testid="stWidgetLabel"] {
  font-size: .8rem !important;
  font-weight: 600 !important;
  color: var(--ink-2) !important;
  margin-bottom: 4px !important;
}

/* ═══════════════════════════════════════════════
   CARDS
═══════════════════════════════════════════════ */
.apple-card {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  margin-bottom: 16px;
  transition: transform .22s var(--ease), box-shadow .22s var(--ease);
}
.apple-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.glass-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid var(--border-light);
  margin-bottom: 14px;
  box-shadow: var(--shadow-xs);
  transition: transform .2s var(--ease), box-shadow .2s var(--ease);
}
.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.hostel-card {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  margin-bottom: 16px;
  transition: transform .22s var(--ease), box-shadow .22s var(--ease);
}
.hostel-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

/* ═══════════════════════════════════════════════
   METRIC CARDS
═══════════════════════════════════════════════ */
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 20px 14px;
  text-align: center;
  box-shadow: var(--shadow-xs);
  height: 100%;
}
.metric-value {
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--ink);
  line-height: 1;
  margin: 6px 0 4px;
  letter-spacing: -.03em;
}
.metric-label {
  font-size: .68rem;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: .12em;
  font-weight: 700;
}
.metric-sub {
  font-size: .76rem;
  color: var(--ink-4);
  margin-top: 3px;
}

/* ═══════════════════════════════════════════════
   TYPOGRAPHY
═══════════════════════════════════════════════ */
.hero-title {
  font-size: 2.75rem;
  font-weight: 800;
  color: var(--ink);
  letter-spacing: -1.5px;
  margin-bottom: 8px;
  line-height: 1.1;
}
.hero-title span { color: var(--accent); }
.hero-sub {
  font-size: .95rem;
  color: var(--ink-3);
  max-width: 400px;
  margin: 0 auto;
  line-height: 1.6;
}

.section-header {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--ink);
  margin-bottom: 14px;
  letter-spacing: -.4px;
}

/* ═══════════════════════════════════════════════
   BADGES & TAGS
═══════════════════════════════════════════════ */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 50px;
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .01em;
}
.badge-green  { background: #ECFDF5; color: #065F46; }
.badge-blue   { background: #EFF6FF; color: #1D4ED8; }
.badge-orange { background: #FFF7ED; color: #C2410C; }

.tag {
  display: inline-block;
  background: var(--surface-3);
  border: 1px solid var(--border);
  color: var(--ink-2);
  border-radius: 6px;
  padding: 2px 9px;
  font-size: .72rem;
  font-weight: 500;
  margin: 2px;
}
.htag {
  display: inline-block;
  background: #EEF2FF;
  border: 1px solid #C7D2FE;
  color: #4338CA;
  border-radius: 6px;
  padding: 3px 9px;
  font-size: .7rem;
  font-weight: 600;
  margin: 2px;
}

/* ═══════════════════════════════════════════════
   FILTER BAR
═══════════════════════════════════════════════ */
.filter-bar {
  background: var(--accent-light);
  border: 1px solid var(--accent-mid);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  margin-bottom: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.filter-chip {
  background: var(--accent-mid);
  color: #9B1C0F;
  border-radius: 6px;
  padding: 3px 10px;
  font-size: .74rem;
  font-weight: 700;
}

/* ═══════════════════════════════════════════════
   BANNERS
═══════════════════════════════════════════════ */
.welcome-banner {
  background: linear-gradient(135deg, var(--ink) 0%, var(--ink-2) 100%);
  border-radius: var(--radius-lg);
  padding: 14px 22px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.profile-setup-banner {
  background: linear-gradient(135deg, var(--accent) 0%, #FF7B54 100%);
  border-radius: var(--radius-lg);
  padding: 18px 22px;
  color: white;
  margin-bottom: 20px;
}

/* ═══════════════════════════════════════════════
   AUTH CONTAINER
═══════════════════════════════════════════════ */
.auth-logo-wrap {
  text-align: center;
  padding: 2rem 0 1.5rem;
}
.auth-logo-icon {
  font-size: 2.6rem;
  display: block;
  margin-bottom: 10px;
  animation: floatIcon 3s ease-in-out infinite;
}
@keyframes floatIcon {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(-5px); }
}

/* ═══════════════════════════════════════════════
   HOSTEL PHOTO STRIP
═══════════════════════════════════════════════ */
.photo-strip {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
  margin-bottom: 16px;
  border-radius: var(--radius-md);
  overflow: hidden;
}
.photo-strip-item {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  height: 110px;
}
.photo-strip-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform .3s ease;
}
.photo-strip-item:hover img { transform: scale(1.06); }
.photo-strip-label {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,.65));
  color: #fff;
  font-size: .62rem;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  padding: 14px 7px 5px;
  text-align: center;
}

.star-row { color: #F59E0B; font-size: .9rem; letter-spacing: .5px; }
.maps-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #4285F4;
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 7px 14px;
  font-size: .78rem;
  font-weight: 700;
  text-decoration: none;
  transition: background .18s var(--ease), transform .15s var(--ease);
  box-shadow: 0 1px 4px rgba(66,133,244,.3);
}
.maps-btn:hover {
  background: #1A73E8;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(66,133,244,.35);
}

/* ═══════════════════════════════════════════════
   SIDEBAR USER PILL
═══════════════════════════════════════════════ */
.user-pill {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  margin-bottom: 14px;
}
.user-pill-label {
  font-size: .64rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 2px;
}
.user-pill-name  { font-weight: 700; color: var(--ink); font-size: .9rem; }
.user-pill-email { font-size: .74rem; color: var(--ink-3); }

/* ═══════════════════════════════════════════════
   ANIMATIONS
═══════════════════════════════════════════════ */
@keyframes fadeIn {
  from { opacity:0; transform: translateY(8px); }
  to   { opacity:1; transform: translateY(0); }
}
.fade-in { animation: fadeIn .4s var(--ease) both; }

@keyframes slideUp {
  from { opacity:0; transform: translateY(16px); }
  to   { opacity:1; transform: translateY(0); }
}
.slide-up { animation: slideUp .5s var(--ease) both; }

/* ═══════════════════════════════════════════════
   STREAMLIT CONTAINER BORDERS
═══════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-radius: var(--radius-lg) !important;
  border-color: var(--border) !important;
  box-shadow: var(--shadow-xs) !important;
}

/* Dataframe */
.stDataFrame { border-radius: var(--radius-md) !important; overflow: hidden !important; }

/* Expander */
[data-testid="stExpander"] details summary p {
  font-weight: 700 !important;
  color: var(--ink-2) !important;
  font-size: .9rem !important;
}
[data-testid="stExpander"] details {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
  margin-bottom: 10px !important;
}
/* Fix: hide leaked ghost/key text that appears before expander labels */
[data-testid="stExpander"] details summary > span:first-child:not([data-testid]) {
  display: none !important;
}
div[data-testid="column"] > div:empty { display: none !important; }

/* Caption text */
.stCaptionContainer { color: var(--ink-3) !important; font-size: .8rem !important; }

/* Setup box */
.setup-box {
  background: var(--surface);
  border: 2px dashed var(--accent-mid);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 20px;
  text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# USER STORE
# ─────────────────────────────────────────────
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,"r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE,"w") as f:
        json.dump(users, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def rent_label_from_amount(amt):
    if amt < 5000:   return "Rs.3K-5K"
    elif amt < 8000: return "Rs.5K-8K"
    elif amt < 12000:return "Rs.8K-12K"
    else:            return "Rs.12K-20K"

def register_user(users, email, password, profile):
    if email in users:
        return False, "Email already registered."
    users[email] = {
        "password_hash": hash_pw(password),
        "profile": profile,
        "created_at": str(datetime.datetime.now()),
        "lifestyle_set": False,   # ← flag: lifestyle prefs not yet filled
    }
    save_users(users)
    append_user_to_csv(profile)
    return True, "Account created!"

def update_lifestyle(users, email, lifestyle):
    """Persist lifestyle prefs after registration."""
    if email in users:
        users[email]["profile"].update(lifestyle)
        users[email]["lifestyle_set"] = True
        save_users(users)

def append_user_to_csv(profile):
    new_row = {
        "ID": f"U{int(datetime.datetime.now().timestamp())}",
        "Name": profile.get("name",""), "Gender": profile.get("gender","Unknown"),
        "Major": profile.get("major",""), "Contact": profile.get("contact",""),
        "Area": profile.get("area","Koramangala"),
        "Monthly_Rent": profile.get("monthly_rent", 7000),
        "Rent_Label": profile.get("rent_label","Rs.5K-8K"),
        "Food_Preference": profile.get("food","Vegetarian"),
        "Room_Capacity": profile.get("room_capacity",2),
        "Sleep": profile.get("sleep",5), "Cleanliness": profile.get("cleanliness",5),
        "Social": profile.get("social",5), "Noise": profile.get("noise",5),
    }
    try:
        df = pd.read_csv(CSV_FILE)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
    except Exception:
        pass

def authenticate(users, email, password):
    if email not in users:
        return False, "Email not found."
    if users[email]["password_hash"] != hash_pw(password):
        return False, "Incorrect password."
    return True, users[email]["profile"]


# ─────────────────────────────────────────────
# ML BACKEND
# ─────────────────────────────────────────────
@st.cache_data
def load_and_train():
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        names = [f"Student {i}" for i in range(101, 301)]
        df = pd.DataFrame({
            "ID": range(1000,1200), "Name": names,
            "Gender": np.random.choice(["Male","Female"],200),
            "Major": np.random.choice(MAJORS,200),
            "Contact": [f"+91 9{np.random.randint(100000000,999999999)}" for _ in range(200)],
            "Area": np.random.choice(ALL_AREAS,200),
            "Monthly_Rent": np.random.randint(3000,20000,200),
            "Rent_Label": np.random.choice(RENT_ORDER,200),
            "Food_Preference": np.random.choice(FOOD_OPTS,200),
            "Room_Capacity": np.random.choice([1,2,3],200),
            "Sleep": np.random.randint(1,11,200), "Cleanliness": np.random.randint(1,11,200),
            "Social": np.random.randint(1,11,200), "Noise": np.random.randint(1,11,200),
        })

    defaults = {"Gender":"Unknown","Area":"Koramangala","Monthly_Rent":6000,
                "Rent_Label":"Rs.5K-8K","Food_Preference":"Vegetarian","Room_Capacity":2}
    for col, val in defaults.items():
        if col not in df.columns: df[col] = val

    features = df[["Sleep","Cleanliness","Social","Noise"]]
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df["Cluster"] = kmeans.fit_predict(features)
    centers = df.groupby("Cluster")[["Sleep","Social"]].mean()
    cmap = {}
    for cid, row in centers.iterrows():
        if   row["Sleep"]>5.5 and row["Social"]>5.5: cmap[cid]="🎉 Party Animal"
        elif row["Sleep"]<5.5 and row["Social"]<5.5: cmap[cid]="📚 The Scholar"
        elif row["Sleep"]>5.5 and row["Social"]<5.5: cmap[cid]="🦉 Night Owl"
        else:                                          cmap[cid]="🏅 The Athlete"
    df["Cluster_Name"] = df["Cluster"].map(cmap)
    return df, kmeans, cmap


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [("logged_in",False),("user_email",None),("user_profile",None),
              ("auth_tab","login"),("search_done",False),("lifestyle_set",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

users = load_users()


# ═════════════════════════════════════════════
# AUTH PAGE
# ═════════════════════════════════════════════
def show_auth():
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown("""
        <div class="auth-logo-wrap fade-in">
            <span class="auth-logo-icon">🏠</span>
            <h1 class="hero-title">Roommate <span>Matchmaker</span></h1>
            <p class="hero-sub">Smart hostel roommate compatibility.</p>
        </div>""", unsafe_allow_html=True)

        tabs = st.tabs(["  Sign In  ", "  Create Account  "])

        # ── LOGIN TAB ──
        with tabs[0]:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("""
                <p style="font-size:.82rem;color:var(--ink-3);margin:0 0 16px;font-weight:500;">
                  Welcome back — sign in to your account.
                </p>""", unsafe_allow_html=True)
                email = st.text_input("Email Address", key="li_email", placeholder="you@college.edu")
                pw    = st.text_input("Password", type="password", key="li_pw", placeholder="••••••••")
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                if st.button("Sign In →", key="btn_login", use_container_width=True):
                    if not email or not pw:
                        st.error("Please fill in all fields.")
                    else:
                        ok, result = authenticate(users, email, pw)
                        if ok:
                            st.session_state.logged_in    = True
                            st.session_state.user_email   = email
                            st.session_state.user_profile = result
                            st.session_state.lifestyle_set = users[email].get("lifestyle_set", False)
                            st.rerun()
                        else:
                            st.error(result)
                st.markdown("""
                <p style="text-align:center;margin-top:14px;font-size:.8rem;color:var(--ink-4);">
                  Don't have an account? Switch to <b style="color:var(--ink-2);">Create Account</b> above.
                </p>""", unsafe_allow_html=True)

        # ── REGISTER TAB ──
        with tabs[1]:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("""
                <p style="font-size:.82rem;color:var(--ink-3);margin:0 0 16px;font-weight:500;">
                  Create your account — profile details are set up after login.
                </p>""", unsafe_allow_html=True)

                r1, r2 = st.columns(2)
                with r1: reg_name  = st.text_input("Full Name *", key="reg_name",  placeholder="Aarav Sharma")
                with r2: reg_email = st.text_input("Email *",     key="reg_email", placeholder="aarav@college.edu")

                r3, r4 = st.columns(2)
                with r3: reg_pw  = st.text_input("Password *",         type="password", key="reg_pw",  placeholder="Min 6 chars")
                with r4: reg_pw2 = st.text_input("Confirm Password *", type="password", key="reg_pw2", placeholder="Repeat password")

                reg_contact = st.text_input("Phone Number", key="reg_contact", placeholder="+91 9XXXXXXXXX")

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("Create Account →", key="btn_register", use_container_width=True):
                    errs = []
                    if not reg_name:
                        errs.append("Name is required.")
                    if not reg_email:
                        errs.append("Email is required.")
                    elif not is_valid_email(reg_email):
                        errs.append("Enter a valid email address (e.g. user@domain.com).")
                    if not reg_pw:
                        errs.append("Password is required.")
                    elif not is_valid_password(reg_pw):
                        errs.append("Password must be at least 6 characters and contain both letters and numbers.")
                    if reg_pw and reg_pw2 and reg_pw != reg_pw2:
                        errs.append("Passwords do not match.")
                    if errs:
                        for e in errs: st.error(e)
                    else:
                        profile = {
                            "name": reg_name, "contact": reg_contact,
                            "gender": "Other", "major": "CSE",
                            "area": "Koramangala", "food": "Vegetarian",
                            "room_capacity": 2,
                            "monthly_rent": 7000, "rent_label": "Rs.5K-8K",
                            "sleep": 5, "cleanliness": 5, "social": 5, "noise": 5,
                        }
                        fresh = load_users()
                        ok, msg = register_user(fresh, reg_email, reg_pw, profile)
                        if ok:
                            st.session_state.logged_in    = True
                            st.session_state.user_email   = reg_email
                            st.session_state.user_profile = profile
                            st.session_state.lifestyle_set = False
                            st.success("✅ Account created! Complete your profile on the dashboard.")
                            st.rerun()
                        else:
                            st.error(msg)

                st.markdown("""
                <p style="text-align:center;margin-top:14px;font-size:.8rem;color:var(--ink-4);">
                  Already have an account? Switch to <b style="color:var(--ink-2);">Sign In</b> above.
                </p>""", unsafe_allow_html=True)

        st.markdown("""
        <p style="text-align:center;margin-top:24px;font-size:.74rem;color:var(--ink-5);
                  letter-spacing:.03em;">
          Powered by K-Means Clustering &amp; Cosine Similarity
        </p>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# LIFESTYLE SETUP  (shown once after registration)
# ═════════════════════════════════════════════
def show_lifestyle_setup():
    p = st.session_state.user_profile or {}
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown(f"""
        <div class="fade-in profile-setup-banner">
            <div style="font-size:1.6rem;margin-bottom:4px;">🎉 Welcome, {p.get('name','there')}!</div>
            <div style="opacity:.85;font-size:.9rem;">
                One last step — complete your profile so we can find your perfect roommate.
            </div>
        </div>""", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### 👤 About You")
            a1, a2 = st.columns(2)
            with a1:
                setup_gender = st.selectbox("Gender *", ["Male","Female","Other"],
                                            index=["Male","Female","Other"].index(p.get("gender","Other")),
                                            key="setup_gender")
            with a2:
                setup_major = st.selectbox("Major / Branch *", MAJORS,
                                           index=MAJORS.index(p.get("major","CSE")) if p.get("major","CSE") in MAJORS else 0,
                                           key="setup_major")

            st.markdown("#### 🏠 Housing Preferences")
            b1, b2 = st.columns(2)
            with b1:
                setup_area = st.selectbox("Preferred Area *", ALL_AREAS,
                                          index=ALL_AREAS.index(p.get("area","Koramangala")) if p.get("area","Koramangala") in ALL_AREAS else 0,
                                          key="setup_area")
            with b2:
                setup_food = st.selectbox("Food Preference *", FOOD_OPTS,
                                          index=FOOD_OPTS.index(p.get("food","Vegetarian")) if p.get("food","Vegetarian") in FOOD_OPTS else 0,
                                          key="setup_food")

            b3, b4 = st.columns(2)
            with b3:
                rent_val = st.slider("Monthly Rent Budget (₹) *", 3000, 20000,
                                     int(p.get("monthly_rent", 7000)), 500, key="setup_rent")
            with b4:
                room_cap = st.select_slider("Max Roommates in Room", options=[1,2,3],
                                            value=int(p.get("room_capacity", 2)), key="setup_cap")

            st.markdown("#### 🎭 Lifestyle Preferences")
            l1, l2 = st.columns(2)
            with l1:
                s_sleep  = st.slider("🌙 Sleep Schedule",  1, 10, int(p.get("sleep",5)), key="setup_sleep",
                                     help="1 = Early Riser · 10 = Night Owl")
                s_social = st.slider("🎭 Social Battery",  1, 10, int(p.get("social",5)), key="setup_social",
                                     help="1 = Introvert · 10 = Very Social")
            with l2:
                s_clean  = st.slider("✨ Cleanliness",      1, 10, int(p.get("cleanliness",7)), key="setup_clean",
                                     help="1 = Relaxed · 10 = Very Neat")
                s_noise  = st.slider("🔊 Noise Tolerance",  1, 10, int(p.get("noise",5)), key="setup_noise",
                                     help="1 = Needs Quiet · 10 = Tolerates Loud")

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Save Profile & Find Matches →", key="btn_setup", use_container_width=True):
                lifestyle = {
                    "gender": setup_gender, "major": setup_major,
                    "area": setup_area, "food": setup_food,
                    "monthly_rent": rent_val,
                    "rent_label": rent_label_from_amount(rent_val),
                    "room_capacity": room_cap,
                    "sleep": s_sleep, "cleanliness": s_clean,
                    "social": s_social, "noise": s_noise,
                }
                fresh = load_users()
                update_lifestyle(fresh, st.session_state.user_email, lifestyle)
                st.session_state.user_profile.update(lifestyle)
                st.session_state.lifestyle_set = True
                st.rerun()

        if st.button("⬅ Sign Out", key="btn_logout_setup"):
            for k in ["logged_in","user_email","user_profile","search_done","lifestyle_set"]:
                st.session_state[k] = False if k in ("logged_in","search_done","lifestyle_set") else None
            st.rerun()


# ═════════════════════════════════════════════
# HOSTELS MODULE
# ═════════════════════════════════════════════
def show_hostels():
    st.markdown('<div class="section-header">🏨 Hostel Search — Bengaluru</div>', unsafe_allow_html=True)
    st.caption("Browse verified hostels near your college. Click 📍 to open in Google Maps.")

    # ── FILTER ROW ──
    fc1, fc2, fc3, fc4, fc5 = st.columns([2,1.5,1.5,1.5,1.5])
    with fc1:
        search_q = st.text_input("🔍 Search by name or area", placeholder="e.g. Koramangala or Stanza",
                                 key="h_search", label_visibility="collapsed")
    with fc2:
        sort_opt = st.selectbox("Sort by", ["⭐ Top Rated","📍 Nearest","💰 Lowest Price","💬 Most Reviewed"],
                                key="h_sort", label_visibility="collapsed")
    with fc3:
        area_opt = st.selectbox("Area", ["All Areas"] + ALL_AREAS, key="h_area", label_visibility="collapsed")
    with fc4:
        gender_opt = st.selectbox("Gender", ["All","Co-ed","Female Only","Male Only"],
                                  key="h_gender", label_visibility="collapsed")
    with fc5:
        max_price = st.select_slider("Max Price/mo", options=[5000,8000,10000,12000,15000,20000],
                                     value=20000, key="h_price", label_visibility="collapsed",
                                     format_func=lambda x: f"₹{x//1000}K")

    # ── AMENITY FILTER ──
    amenity_opts = ["WiFi","AC","Meals","Gym","Laundry","CCTV","Study Room","Housekeeping"]
    sel_amenities = st.multiselect("Filter by amenities", amenity_opts, default=[],
                                   key="h_amenities", placeholder="Any amenity")

    # ── APPLY FILTERS ──
    filtered = HOSTELS.copy()

    if search_q.strip():
        q = search_q.strip().lower()
        filtered = [h for h in filtered if q in h["name"].lower() or q in h["area"].lower()]

    if area_opt != "All Areas":
        filtered = [h for h in filtered if h["area"] == area_opt]

    if gender_opt != "All":
        filtered = [h for h in filtered if h["gender"] == gender_opt]

    filtered = [h for h in filtered if h["price_min"] <= max_price]

    if sel_amenities:
        filtered = [h for h in filtered if all(a in h["tags"] for a in sel_amenities)]

    # ── SORT ──
    if   "Top Rated"      in sort_opt: filtered.sort(key=lambda h: h["rating"], reverse=True)
    elif "Nearest"        in sort_opt: filtered.sort(key=lambda h: h["distance_km"])
    elif "Lowest Price"   in sort_opt: filtered.sort(key=lambda h: h["price_min"])
    elif "Most Reviewed"  in sort_opt: filtered.sort(key=lambda h: h["reviews"], reverse=True)

    # ── RESULT COUNT ──
    st.markdown(f"""
    <div style="background:#F1F5F9;border-radius:10px;padding:10px 16px;margin:12px 0;
                font-size:.82rem;color:#475569;border:1px solid #E2E8F0;">
        🏨 Showing <b>{len(filtered)}</b> hostel{"s" if len(filtered)!=1 else ""} matching your filters
        {"— try removing some filters to see more." if len(filtered)<3 else ""}
    </div>""", unsafe_allow_html=True)

    if not filtered:
        st.warning("No hostels match your current filters. Try adjusting the area or price.")
        return

    # ── RENDER CARDS (2 per row) ──
    for i in range(0, len(filtered), 2):
        row_hostels = filtered[i:i+2]
        cols = st.columns(2)
        for j, h in enumerate(row_hostels):
            stars_full  = int(h["rating"])
            stars_half  = 1 if (h["rating"] - stars_full) >= 0.5 else 0
            stars_empty = 5 - stars_full - stars_half
            stars_html  = "★"*stars_full + ("½" if stars_half else "") + "☆"*stars_empty

            tags_html = " ".join([f'<span class="htag">{t}</span>' for t in h["tags"]])

            with cols[j]:
                photos     = h.get("photos", [])
                ph_labels  = h.get("photo_labels", ["","",""])

                # Build photo strip HTML
                photo_items = "".join([
                    f'<div class="photo-strip-item">'
                    f'  <img src="{url}" alt="{ph_labels[pi] if pi < len(ph_labels) else ""}" loading="lazy">'
                    f'  <div class="photo-strip-label">{ph_labels[pi] if pi < len(ph_labels) else ""}</div>'
                    f'</div>'
                    for pi, url in enumerate(photos[:3])
                ])
                photo_strip_html = (
                    f'<div class="photo-strip">{photo_items}</div>'
                    if photo_items else ""
                )

                st.markdown(f"""
                <div class="hostel-card">
                  {photo_strip_html}
                  <!-- HEADER -->
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">
                    <div>
                      <div style="font-size:1.8rem;margin-bottom:4px;">{h['emoji']}</div>
                      <h3 style="margin:0;font-size:1.05rem;font-weight:800;color:#111;line-height:1.2;">
                        {h['name']}
                      </h3>
                      <div style="font-size:.78rem;color:#888;margin-top:3px;">📍 {h['address']}</div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;margin-left:12px;">
                      <span style="background:{h['highlight_color']};color:#fff;border-radius:20px;
                                   padding:3px 10px;font-size:.7rem;font-weight:700;">
                        {h['highlight']}
                      </span>
                    </div>
                  </div>

                  <!-- RATING ROW -->
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                    <span class="star-row">{stars_html}</span>
                    <span style="font-weight:700;color:#111;">{h['rating']}</span>
                    <span style="color:#aaa;font-size:.8rem;">({h['reviews']} reviews)</span>
                    <span style="background:#F0FDF4;color:#15803D;border-radius:6px;
                                 padding:2px 8px;font-size:.72rem;font-weight:700;margin-left:auto;">
                      📍 {h['distance_km']} km away
                    </span>
                  </div>

                  <!-- PRICE + GENDER -->
                  <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center;">
                    <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;
                                padding:6px 12px;">
                      <span style="font-size:.65rem;color:#92400E;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1px;">Price</span>
                      <div style="font-size:.95rem;font-weight:800;color:#C2410C;">
                        {h['price_range']}
                      </div>
                    </div>
                    <div style="background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;
                                padding:6px 12px;">
                      <span style="font-size:.65rem;color:#0C4A6E;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1px;">Type</span>
                      <div style="font-size:.85rem;font-weight:700;color:#0369A1;">
                        {h['gender']}
                      </div>
                    </div>
                    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                                padding:6px 12px;">
                      <span style="font-size:.65rem;color:#14532D;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1px;">Food</span>
                      <div style="font-size:.85rem;font-weight:700;color:#15803D;">
                        {h['food']}
                      </div>
                    </div>
                  </div>

                  <!-- AMENITY TAGS -->
                  <div style="margin-bottom:14px;line-height:1.8;">{tags_html}</div>

                  <!-- MAPS LINK -->
                  <a href="{h['maps_url']}" target="_blank" class="maps-btn">
                    🗺️ Open in Google Maps
                  </a>
                  <span style="font-size:.72rem;color:#aaa;margin-left:10px;">
                    Search nearest • directions • street view
                  </span>
                </div>
                """, unsafe_allow_html=True)

    # ── TIP ──
    st.markdown("""
    <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;
                padding:14px 18px;margin-top:10px;font-size:.82rem;color:#92400E;">
        💡 <b>Tip:</b> Click <b>Open in Google Maps</b> on any hostel card to get real-time
        directions, street view, nearby facilities, and user photos directly in Google Maps.
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# MAIN DASHBOARD
# ═════════════════════════════════════════════
def show_dashboard():
    df, kmeans_model, cluster_map = load_and_train()
    p = st.session_state.user_profile or {}

    # ── SIDEBAR ──
    with st.sidebar:
        # Dark sidebar shell
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background: #1A1A2E !important;
            border-right: 1px solid #2D2D44 !important;
        }
        [data-testid="stSidebar"] * { color: #E0E0E0 !important; }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] > div > p {
            color: #AAAACC !important;
            font-size: 0.7rem !important;
            font-weight: 700 !important;
            letter-spacing: .12em !important;
            text-transform: uppercase !important;
        }
        [data-testid="stSidebar"] .stSlider > div[data-baseweb="slider"] > div > div { background: #E8432D !important; }
        [data-testid="stSidebar"] .stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"] {
            background: #E8432D !important; box-shadow: 0 0 0 4px rgba(232,67,45,.25) !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
            background: #2D2D44 !important;
            border: 1.5px solid #3D3D5C !important;
            border-radius: 8px !important;
            color: #E0E0E0 !important;
        }
        [data-testid="stSidebar"] div.stButton > button {
            background: #E8432D !important;
            color: #fff !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] div.stButton > button:hover { background: #C0392B !important; }
        .sb-section-header {
            font-size: .7rem !important;
            font-weight: 800 !important;
            letter-spacing: .14em !important;
            text-transform: uppercase !important;
            color: #AAAACC !important;
            margin: 14px 0 10px !important;
            display: flex; align-items: center; gap: 6px;
        }
        .sb-user-pill {
            background: #2D2D44;
            border: 1px solid #3D3D5C;
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 16px;
        }
        .sb-user-label { font-size:.62rem; letter-spacing:.1em; text-transform:uppercase; color:#E8432D !important; font-weight:700; margin-bottom:2px; }
        .sb-user-name  { font-weight:800; color:#FFFFFF !important; font-size:.95rem; }
        .sb-user-email { font-size:.72rem; color:#AAAACC !important; }
        .sb-divider { border: none; border-top: 1px solid #2D2D44; margin: 14px 0; }
        </style>
        """, unsafe_allow_html=True)

        # Logo
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;padding-bottom:10px;
                    border-bottom:1px solid #2D2D44;">
            <span style="font-size:1.5rem;">🏠</span>
            <span style="font-size:1.05rem;font-weight:800;color:#FFFFFF;">Roommate Matchmaker</span>
        </div>
        """, unsafe_allow_html=True)

        # User pill
        st.markdown(f"""
        <div class="sb-user-pill">
            <div class="sb-user-label">Signed in as</div>
            <div class="sb-user-name">{p.get('name','User')}</div>
            <div class="sb-user-email">{st.session_state.user_email}</div>
        </div>""", unsafe_allow_html=True)

        # ── SECTION 1: MY PREFERENCES ──
        st.markdown('<div class="sb-section-header">⚙️ My Preferences</div>', unsafe_allow_html=True)
        s_sleep  = st.slider("🌙 Sleep Schedule",  1, 10, int(p.get("sleep",5)),  key="sl_sleep")
        s_clean  = st.slider("✨ Cleanliness",      1, 10, int(p.get("cleanliness",7)), key="sl_clean")
        s_social = st.slider("🎭 Social Battery",   1, 10, int(p.get("social",5)), key="sl_social")
        s_noise  = st.slider("🔊 Noise Tolerance",  1, 10, int(p.get("noise",5)),  key="sl_noise")

        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

        # ── SECTION 2: FILTERS ──
        st.markdown('<div class="sb-section-header">🔍 Filters</div>', unsafe_allow_html=True)

        gender_options = ["Any","Male","Female","Other"]
        default_gender = p.get("gender","Any") if p.get("gender","Any") in gender_options else "Any"
        gender_pref = st.selectbox("👥 Roommate Gender", gender_options,
                                   index=gender_options.index(default_gender), key="flt_gender")

        food_options = ["Any"] + FOOD_OPTS
        default_food = p.get("food","Any") if p.get("food","Any") in food_options else "Any"
        food_pref = st.selectbox("🍽️ Food Preference", food_options,
                                 index=food_options.index(default_food), key="flt_food")

        room_cap = st.slider("🛏️ Room Capacity (Persons)", 1, 3,
                             int(p.get("room_capacity",2)), key="flt_cap")

        area_options = ["Any"] + ALL_AREAS
        default_area = p.get("area","Any") if p.get("area","Any") in area_options else "Any"
        area_sel = st.selectbox("📍 Preferred Areas", area_options,
                                index=area_options.index(default_area), key="flt_area")
        area_pref = [area_sel] if area_sel != "Any" else []

        rent_options = ["Any"] + RENT_ORDER
        default_rent = p.get("rent_label","Any") if p.get("rent_label","Any") in rent_options else "Any"
        rent_sel = st.selectbox("💰 Monthly Budget", rent_options,
                                index=rent_options.index(default_rent), key="flt_rent")
        rent_pref = [rent_sel] if rent_sel != "Any" else []

        top_n = st.slider("🏆 Show Top Matches", 3, 10, 3, key="flt_top")

        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

        # ── ACTION BUTTONS ──
        def do_search(): st.session_state.search_done = True
        st.button("✦ Find My Roommates", on_click=do_search, key="btn_find")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Update", key="btn_update_prefs"):
                st.session_state.lifestyle_set = False
                st.rerun()
        with col_b:
            if st.button("🚪 Sign Out", key="btn_signout"):
                for k in ["logged_in","user_email","user_profile","search_done","lifestyle_set"]:
                    st.session_state[k] = False if k in ("logged_in","search_done","lifestyle_set") else None
                st.rerun()

        # Live stats chip
        st.markdown(f"""
        <div style="margin-top:14px;padding:10px 12px;background:#2D2D44;
                    border-radius:10px;border:1px solid #3D3D5C;text-align:center;">
            <div style="font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
                        color:#AAAACC;margin-bottom:4px;font-weight:700;">Live Database</div>
            <div style="font-size:1.4rem;font-weight:800;color:#FFFFFF;letter-spacing:-.03em;">{len(df)}</div>
            <div style="font-size:.7rem;color:#AAAACC;">Registered Students</div>
        </div>""", unsafe_allow_html=True)

    # ── WELCOME BANNER ──
    st.markdown(f"""
    <div class="welcome-banner">
        <div>
            <div style="font-size:.75rem;opacity:.7;text-transform:uppercase;letter-spacing:1px;">Welcome back</div>
            <div style="font-size:1.2rem;font-weight:700;">{p.get('name','User')} 👋</div>
        </div>
        <div style="opacity:.7;font-size:.82rem;">{p.get('major','')} · {p.get('area','')}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <h1 class="hero-title">Roommate <span>Matchmaker</span></h1>
        <p class="hero-sub">Intelligent hostel allocation powered by Machine Learning.</p>
    </div>""", unsafe_allow_html=True)

    # ── MAIN TABS ──
    tab1, tab2 = st.tabs(["🤝  Roommate Finder", "🏨  Hostels"])

    # ──────────────────────────────────────────
    # TAB 1: ROOMMATE FINDER
    # ──────────────────────────────────────────
    with tab1:
        if not st.session_state.search_done:
            st.markdown("""
            <div style="text-align:center;padding:1.5rem 1rem 2rem;color:#888;">
                <div style="font-size:2.8rem;margin-bottom:10px;">🔍</div>
                <div style="font-size:1.3rem;font-weight:800;color:#111;margin-bottom:8px;">
                    Set your preferences and click Find My Roommates
                </div>
                <div style="font-size:.9rem;">
                    Adjust your lifestyle sliders in the sidebar and click Find My Roommates.
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-header">📊 Student Database Overview</div>', unsafe_allow_html=True)
            ov1, ov2 = st.columns(2)
            with ov1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**📍 Area Distribution**")
                _av = df["Area"].value_counts()
                fig = px.bar(pd.DataFrame({"Area":_av.index,"Count":_av.values}),
                             x="Count", y="Area", orientation="h",
                             color_discrete_sequence=["#E8432D"])
                fig.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   yaxis=dict(categoryorder="total ascending"))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with ov2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**🍽️ Food Preferences**")
                fd = df["Food_Preference"].value_counts()
                fig2 = px.pie(values=fd.values, names=fd.index, hole=.5,
                              color_discrete_sequence=["#E8432D","#0F1117","#6366F1"])
                fig2.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0),
                                    paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">🎓 Student Database Preview</div>', unsafe_allow_html=True)
            preview_cols = ["Name","Gender","Major","Area","Food_Preference",
                            "Room_Capacity","Rent_Label","Sleep","Cleanliness","Social","Noise"]
            st.dataframe(df[[c for c in preview_cols if c in df.columns]].head(8),
                         use_container_width=True, hide_index=True)
            _show_results = False
        else:
            _show_results = True

        # ── RESULTS ──
        if _show_results:
          user_vector  = [[s_sleep, s_clean, s_social, s_noise]]
          pred_cluster = kmeans_model.predict(user_vector)[0]
          user_tribe   = cluster_map.get(pred_cluster, "General")
          fdf          = df[df["Cluster"] == pred_cluster].copy()

          filter_chips = []
          if gender_pref and gender_pref not in ("Any","Unknown","Other"):
              fdf = fdf[fdf["Gender"]==gender_pref]; filter_chips.append(f"👥 {gender_pref}")
          if food_pref and food_pref != "Any":
              fdf = fdf[fdf["Food_Preference"]==food_pref]; filter_chips.append(f"🍽️ {food_pref}")
          if room_cap:
              fdf = fdf[fdf["Room_Capacity"]>=room_cap]; filter_chips.append(f"🛏️ ≥{room_cap}-person room")
          if area_pref:
              fdf = fdf[fdf["Area"].isin(area_pref)]; filter_chips.append(f"📍 {', '.join(area_pref)}")
          if rent_pref:
              fdf = fdf[fdf["Rent_Label"].isin(rent_pref)]; filter_chips.append(f"💰 {', '.join(rent_pref)}")

          if filter_chips:
              chips_html = "".join([f'<span class="filter-chip">{c}</span>' for c in filter_chips])
              st.markdown(f'<div class="filter-bar"><span style="color:#C0392B;font-size:.72rem;font-weight:700;'
                          f'text-transform:uppercase;letter-spacing:1px;">Active Filters:</span> {chips_html}</div>',
                          unsafe_allow_html=True)

          # Exclude the currently logged-in user from results
          current_name = (p.get("name","") or "").strip().lower()
          if current_name:
              fdf = fdf[fdf["Name"].str.strip().str.lower() != current_name]

          if len(fdf) == 0:
              st.warning("😔 No matches found with current filters. Try expanding them.")
              _show_results = False

        if _show_results:
            sim_scores = cosine_similarity(user_vector, fdf[["Sleep","Cleanliness","Social","Noise"]].values)[0]
            fdf = fdf.copy(); fdf["Match_Score"] = sim_scores
            results = fdf.sort_values("Match_Score", ascending=False).head(top_n)
            best = results.iloc[0]

            # METRICS
            m1,m2,m3,m4,m5 = st.columns(5)
            for col, lbl, val, sub in zip(
                [m1,m2,m3,m4,m5],
                ["DATABASE","YOUR TRIBE","CANDIDATES","ROOM CAP","TOP MATCH"],
                [len(df), user_tribe, len(fdf), f"{room_cap}P", f"{int(best['Match_Score']*100)}%"],
                ["Active Students","AI Cluster","After Filters","Preference","Compatibility"]
            ):
                color = "#FF4B4B" if lbl=="TOP MATCH" else "#111"
                size  = "1.3rem"  if lbl=="YOUR TRIBE" else "2rem"
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{lbl}</div>
                        <div class="metric-value" style="color:{color};font-size:{size};">{val}</div>
                        <div class="metric-sub">{sub}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # CHARTS ROW 1
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**🎯 Personality Overlap — You vs Best Match**")
                cats = ["Sleep","Cleanliness","Social","Noise"]
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(
                    r=[s_sleep,s_clean,s_social,s_noise], theta=cats,
                    fill="toself", name=p.get("name","You"),
                    line_color="#111827", fillcolor="rgba(17,24,39,.15)"))
                fig_r.add_trace(go.Scatterpolar(
                    r=[best["Sleep"],best["Cleanliness"],best["Social"],best["Noise"]],
                    theta=cats, fill="toself", name=best["Name"],
                    line_color="#FF4B4B", fillcolor="rgba(255,75,75,.15)"))
                fig_r.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,10])),
                                     showlegend=True, margin=dict(l=40,r=40,t=30,b=20),
                                     height=300, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_r, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(f"**🗺️ You vs '{user_tribe}' Tribe**")
                # Use full df as background so all clusters are visible
                cluster_colors = ["#FF4B4B","#6366F1","#34C759","#FF9F0A","#0EA5E9","#EC4899"]
                unique_clusters = sorted(df["Cluster_Name"].dropna().unique().tolist())
                color_map = {c: cluster_colors[i % len(cluster_colors)] for i, c in enumerate(unique_clusters)}
                fig_s = go.Figure()
                # Background: all students, faded
                for cname, grp in df.groupby("Cluster_Name"):
                    c_color = color_map.get(cname, "#AAAAAA")
                    is_user_tribe = (cname == user_tribe)
                    fig_s.add_trace(go.Scatter(
                        x=grp["Sleep"], y=grp["Social"],
                        mode="markers",
                        name=cname,
                        marker=dict(color=c_color, size=7 if is_user_tribe else 5,
                                    opacity=0.75 if is_user_tribe else 0.25,
                                    line=dict(width=0)),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "Area: %{customdata[1]}<br>"
                            "Rent: %{customdata[2]}<br>"
                            "Food: %{customdata[3]}<extra>" + cname + "</extra>"
                        ),
                        customdata=grp[["Name","Area","Rent_Label","Food_Preference"]].values,
                        showlegend=True,
                    ))
                # Highlight filtered matches
                if len(fdf) > 0:
                    fig_s.add_trace(go.Scatter(
                        x=fdf["Sleep"], y=fdf["Social"],
                        mode="markers",
                        name="Your Matches",
                        marker=dict(color="#FF4B4B", size=10, opacity=1,
                                    line=dict(color="#FFFFFF", width=1.5)),
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "Area: %{customdata[1]}<br>"
                            "Rent: %{customdata[2]}<br>"
                            "Food: %{customdata[3]}<extra>Match</extra>"
                        ),
                        customdata=fdf[["Name","Area","Rent_Label","Food_Preference"]].values,
                        showlegend=True,
                    ))
                # User star marker
                fig_s.add_trace(go.Scatter(
                    x=[s_sleep], y=[s_social], mode="markers+text",
                    text=[p.get("name","You")], textposition="top center",
                    marker=dict(symbol="star", size=22, color="#111827",
                                line=dict(color="#FF4B4B", width=2)),
                    name="YOU", showlegend=True,
                    hovertemplate="<b>You</b><br>Sleep: %{x}<br>Social: %{y}<extra></extra>"))
                fig_s.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20), height=300,
                    showlegend=True,
                    legend=dict(font=dict(size=10), orientation="h",
                                yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(title="Sleep Score", range=[0, 10],
                               showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                    yaxis=dict(title="Social Score", range=[0, 10],
                               showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                )
                st.plotly_chart(fig_s, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # CHARTS ROW 2
            c3, c4 = st.columns(2)
            with c3:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**🍽️ Food Preference Distribution (Filtered)**")
                fp = fdf["Food_Preference"].value_counts()
                fig_f = px.pie(values=fp.values, names=fp.index, hole=.5,
                               color_discrete_sequence=["#FF4B4B","#111827","#34C759"])
                fig_f.update_layout(height=220, margin=dict(l=0,r=0,t=0,b=0),
                                      paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_f, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c4:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**🛏️ Room Capacity Breakdown (Filtered)**")
                _rc = fdf["Room_Capacity"].value_counts().sort_index()
                total_rc = _rc.sum()
                for cap_val, cap_count in _rc.items():
                    pct = int(cap_count / total_rc * 100) if total_rc > 0 else 0
                    label = f"{cap_val}-Person Room"
                    bar_color = ["#E8432D","#1565C0","#2E7D32"][min(cap_val-1, 2)]
                    st.markdown(f"""
                    <div style="margin-bottom:12px;">
                        <div style="display:flex;justify-content:space-between;
                                    font-size:.82rem;font-weight:600;color:#374151;margin-bottom:4px;">
                            <span>{label}</span>
                            <span style="color:#6B7280;">{cap_count} students · {pct}%</span>
                        </div>
                        <div style="background:#F3F4F6;border-radius:6px;height:8px;overflow:hidden;">
                            <div style="background:{bar_color};width:{pct}%;height:100%;
                                        border-radius:6px;transition:width .4s ease;"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ROOMMATE CARDS
            st.markdown(f'<div class="section-header">🔥 Top {top_n} Recommended Roommates</div>',
                        unsafe_allow_html=True)

            def render_cards(rows, ncols=3):
                cols = st.columns(ncols)
                for i, (idx, row) in enumerate(rows):
                    score     = int(row["Match_Score"]*100)
                    badge_cls = "badge-green" if score>=90 else "badge-blue" if score>=75 else "badge-orange"
                    bar_color = "#2E7D32" if score>=90 else "#1565C0" if score>=75 else "#E65100"
                    g_icon    = "👨" if row.get("Gender")=="Male" else "👩" if row.get("Gender")=="Female" else "🧑"
                    food_icon = {"Vegetarian":"🥦","Non-Vegetarian":"🍗","Eggetarian":"🥚"}.get(
                                    row.get("Food_Preference",""),"🍽️")
                    cap = int(row.get("Room_Capacity",2))
                    with cols[i % ncols]:
                        stat_boxes = "".join([
                            f'<div style="background:#F8F9FA;border-radius:10px;padding:9px;text-align:center;">'
                            f'<div style="font-weight:700;font-size:1rem;color:#111;">{int(row[k])}/10</div>'
                            f'<div style="font-size:.62rem;color:#aaa;text-transform:uppercase;letter-spacing:1px;">{k}</div>'
                            f'</div>'
                            for k in ["Sleep","Social","Cleanliness","Noise"]
                        ])
                        st.markdown(f"""
                        <div class="apple-card" style="padding:20px;">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                                <div>
                                    <div style="font-size:.65rem;color:#999;font-weight:600;text-transform:uppercase;
                                                letter-spacing:1px;margin-bottom:4px;">#{i+1} Match</div>
                                    <h3 style="margin:0;font-size:1.1rem;font-weight:700;color:#111;">
                                        {g_icon} {row['Name']}
                                    </h3>
                                </div>
                                <span class="badge {badge_cls}">{score}%</span>
                            </div>
                            <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;">
                                <span class="tag">🎓 {row['Major']}</span>
                                <span class="tag">📍 {row.get('Area','N/A')}</span>
                                <span class="tag">{food_icon} {row.get('Food_Preference','')}</span>
                                <span class="tag">🛏️ {cap}-Person</span>
                                <span class="tag">💰 {row.get('Rent_Label','')}</span>
                                <span class="tag">{row['Cluster_Name']}</span>
                            </div>
                            <div style="font-size:.8rem;color:#888;margin-bottom:12px;">📞 {row['Contact']}</div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
                                {stat_boxes}
                            </div>
                            <div style="background:#F8F9FA;border-radius:10px;padding:10px;text-align:center;">
                                <div style="font-size:.7rem;color:#aaa;margin-bottom:6px;">Compatibility Score</div>
                                <div style="background:#EFEFEF;border-radius:4px;height:5px;overflow:hidden;">
                                    <div style="background:{bar_color};width:{score}%;height:100%;border-radius:4px;"></div>
                                </div>
                                <div style="font-weight:700;color:{bar_color};margin-top:6px;font-size:.95rem;">
                                    {score}% Compatible
                                </div>
                            </div>
                        </div>""", unsafe_allow_html=True)

            render_cards(list(results.iterrows()), ncols=min(top_n, 3))

            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

            st.markdown('<div class="section-header">📋 Filtered Candidates</div>', unsafe_allow_html=True)
            with st.expander("📋 View All Filtered Candidates", expanded=False, icon=None):
                show_cols = ["Name","Gender","Major","Area","Food_Preference","Room_Capacity",
                             "Rent_Label","Cluster_Name","Sleep","Cleanliness","Social","Noise","Match_Score"]
                show = fdf[[c for c in show_cols if c in fdf.columns]].copy()
                show["Match_Score"] = (show["Match_Score"]*100).round(1).astype(str)+"%"
                show = show.sort_values("Match_Score", ascending=False)
                st.dataframe(show, use_container_width=True, hide_index=True)

            st.markdown('<div class="section-header">👤 Registered Profile</div>', unsafe_allow_html=True)
            with st.expander("👤 My Registered Profile", expanded=False, icon=None):
                gender_icon = "👨" if p.get("gender") == "Male" else "👩" if p.get("gender") == "Female" else "🧑"
                food_icon   = {"Vegetarian":"🥦","Non-Vegetarian":"🍗","Eggetarian":"🥚"}.get(p.get("food",""),"🍽️")
                profile_rows = [
                    ("👤", "Name",          p.get("name","—")),
                    ("📞", "Contact",       p.get("contact","—")),
                    (gender_icon, "Gender", p.get("gender","—")),
                    ("🎓", "Major",         p.get("major","—")),
                    ("📍", "Area",          p.get("area","—")),
                    (food_icon, "Food",     p.get("food","—")),
                    ("🛏️", "Room Capacity", f"{p.get('room_capacity','—')}-Person"),
                    ("💰", "Monthly Rent",  f"₹{p.get('monthly_rent','—'):,}" if isinstance(p.get("monthly_rent"), (int,float)) else p.get("monthly_rent","—")),
                    ("🏷️", "Rent Label",   p.get("rent_label","—")),
                    ("🌙", "Sleep",         f"{p.get('sleep','—')} / 10"),
                    ("✨", "Cleanliness",   f"{p.get('cleanliness','—')} / 10"),
                    ("🎭", "Social",        f"{p.get('social','—')} / 10"),
                    ("🔊", "Noise",         f"{p.get('noise','—')} / 10"),
                ]
                rows_html = "".join([
                    f"""<div style="display:flex;align-items:center;gap:14px;padding:10px 14px;
                                    border-radius:10px;background:{'#F9FAFB' if i%2==0 else '#FFFFFF'};
                                    border:1px solid #F0F0F0;">
                          <span style="font-size:1.1rem;width:24px;text-align:center;">{icon}</span>
                          <span style="font-size:.78rem;font-weight:700;color:#6B7280;text-transform:uppercase;
                                       letter-spacing:.08em;width:110px;flex-shrink:0;">{label}</span>
                          <span style="font-size:.9rem;font-weight:600;color:#111827;">{value}</span>
                        </div>"""
                    for i,(icon,label,value) in enumerate(profile_rows)
                ])
                st.markdown(f"""
                <div style="border:1.5px solid #E5E7EB;border-radius:16px;overflow:hidden;
                            box-shadow:0 2px 12px rgba(0,0,0,.06);">
                  <div style="background:linear-gradient(135deg,#0F1117 0%,#374151 100%);
                              padding:16px 20px;display:flex;align-items:center;gap:12px;">
                    <div style="width:44px;height:44px;border-radius:50%;background:#E8432D;
                                display:flex;align-items:center;justify-content:center;font-size:1.3rem;">
                      {gender_icon}
                    </div>
                    <div>
                      <div style="font-size:1.1rem;font-weight:800;color:#FFFFFF;">{p.get('name','').title()}</div>
                      <div style="font-size:.78rem;color:#9CA3AF;margin-top:2px;">{p.get('major','—')} · {p.get('area','—')}</div>
                    </div>
                  </div>
                  <div style="display:flex;flex-direction:column;gap:2px;padding:8px;">
                    {rows_html}
                  </div>
                </div>""", unsafe_allow_html=True)

    # ──────────────────────────────────────────
    # TAB 2: HOSTELS
    # ──────────────────────────────────────────
    with tab2:
        show_hostels()


# ═════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════
if st.session_state.logged_in:
    if not st.session_state.lifestyle_set:
        show_lifestyle_setup()
    else:
        show_dashboard()
else:
    show_auth()
