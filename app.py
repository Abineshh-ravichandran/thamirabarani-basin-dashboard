import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# --- 1. GLOBAL UI CONFIG (Mobile + Desktop Optimized) ---
st.set_page_config(page_title="Basin Analytics", layout="wide")

# Custom CSS for Global Responsiveness
st.markdown("""
    <style>
    /* Force white background and clean text */
    .stApp { background-color: #ffffff; color: #0f172a; }
    
    /* Responsive Metric Cards */
    [data-testid="stMetric"] {
        background-color: #f8fafc;
        border-radius: 12px;
        padding: 15px !important;
        border: 1px solid #e2e8f0;
    }

    /* MOBILE-SPECIFIC CSS: Stacks columns vertically on screens smaller than 800px */
    @media (max-width: 800px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 calc(100% - 1rem) !important;
            min-width: 100% !important;
        }
    }
    
    /* Professional Section Header */
    .section-header {
        background: #1e3a8a;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATASET (FINALIZED) ---
@st.cache_data
def get_data():
    data = {
        'S_No': ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"],
        'Station': ["Pechiparai Source", "Kaliyal", "Thirparappu", "Moovattumugham", "Thickurichy", 
                    "Vayakalloor Junction", "Parakanni Check Dam", "Thengapattanam", "Ponmanai", "Surulacode"],
        'Type': ["Main"]*8 + ["Branch"]*2,
        'Lat': [8.4496, 8.3997, 8.3923, 8.3418, 8.3147, 8.2616, 8.2529, 8.2384, 8.3480, 8.3610],
        'Lon': [77.3073, 77.2586, 77.2577, 77.2526, 77.2441, 77.1623, 77.1625, 77.1698, 77.330, 77.350],
        'Gamma': [0.12, 0.22, 0.35, 0.61, 0.44, 2.40, 0.95, 3.82, 0.38, 0.16],
        'Mineral': ["Granite/Gneiss", "Alluvial", "Feldspar", "Quartz", "Sedimentary", "Monazite Sand", "Ilmenite", "Thorium-rich Sand", "Clay/Loam", "Laterite"]
    }
    return pd.DataFrame(data)

df = get_data()

# --- 3. HEADER & CONTROLS ---
st.markdown('<div class="section-header"><h2>🛡️ Thamirabarani Basin Dashboard</h2></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📍 Navigation")
    view_mode = st.radio("Path Selection", ["Full Basin", "Primary Path", "Secondary Branch"])
    occ_factor = st.slider("Occupancy Factor", 0.1, 1.0, 0.2)

# Filtering logic (S1 included in both branches)
if view_mode == "Primary Path":
    filtered_df = df[df['Type'] == "Main"]
elif view_mode == "Secondary Branch":
    filtered_df = pd.concat([df.iloc[[0]], df[df['Type'] == "Branch"]])
else:
    filtered_df = df

# --- 4. TOP ROW (KPIs) ---
k1, k2, k3 = st.columns(3)
k1.metric("Station", filtered_df['Station'].iloc[-1])
k2.metric("Peak Gamma", f"{filtered_df['Gamma'].max()} µSv/h")
avg_elcr = (filtered_df['Gamma'].mean() * 8.76 * occ_factor * 0.7 * 0.05 * 70 / 1000)
k3.metric("Avg ELCR", f"{avg_elcr:.5f}")

st.divider()

# --- 5. INTERACTIVE MAP & DETAILS (Stacked on Mobile) ---
col_map, col_details = st.columns([1.6, 1])

with col_map:
    st.subheader("📍 Verified Hydrological Map")
    m = folium.Map(location=[8.35, 77.26], zoom_start=11, tiles="CartoDB positron")
    
    # Paths
    folium.PolyLine(df[df['Type'] == "Main"][['Lat', 'Lon']].values.tolist(), color="#1a5276", weight=5).add_to(m)
    branch_pts = [[df.iloc[0]['Lat'], df.iloc[0]['Lon']], [df.iloc[8]['Lat'], df.iloc[8]['Lon']], [df.iloc[9]['Lat'], df.iloc[9]['Lon']]]
    folium.PolyLine(branch_pts, color="#229954", weight=5, dash_array='5, 5').add_to(m)

    for i, r in filtered_df.iterrows():
        color = "green" if r['Type'] == "Branch" else "blue"
        folium.Marker([r['Lat'], r['Lon']], popup=r['Station'], icon=folium.Icon(color=color, icon="tint")).add_to(m)

    # use_container_width ensures the map fits the mobile screen
    output = st_folium(m, height=450, width="100%", use_container_width=True)

with col_details:
    st.subheader("📝 Site Info")
    if output.get("last_object_clicked_popup"):
        site = df[df['Station'] == output["last_object_clicked_popup"]].iloc[0]
        st.info(f"**{site['Station']}**")
        st.write(f"🌐 **Coords:** {site['Lat']}, {site['Lon']}")
        st.write(f"☢️ **Gamma:** {site['Gamma']} µSv/h")
        st.write(f"🪨 **Mineral:** {site['Mineral']}")
    else:
        st.write("Tap a map pin to see soil and radiation details.")

# --- 6. ANALYSIS SECTION ---
st.markdown('<div class="section-header"><h2>📊 Analytical Plots</h2></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Gradient", "Risk Scatter"])
with tab1:
    fig_bar = px.bar(filtered_df, x='Station', y='Gamma', color='Gamma', template="plotly_white")
    st.plotly_chart(fig_bar, use_container_width=True)
with tab2:
    filtered_df['AED'] = (filtered_df['Gamma'] * 8.76 * occ_factor * 0.7)
    fig_scat = px.scatter(filtered_df, x='Gamma', y='AED', color='Station', template="plotly_white")
    st.plotly_chart(fig_scat, use_container_width=True)
