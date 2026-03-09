import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.figure_factory as ff

# --- 1. GLOBAL UI CONFIG ---
st.set_page_config(page_title="Basin Radiological Analytics", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #0f172a; }
    /* Animated Metric Cards */
    [data-testid="stMetric"] {
        background-color: #f8fafc;
        border-radius: 15px;
        padding: 20px !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        transition: transform 0.3s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-5px); }
    /* Dashboard Headers */
    .section-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. FINALIZED DATASET ---
@st.cache_data
def get_verified_data():
    # Pechiparai (S1) is shared as the head for both paths
    data = {
        'S_No': ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"],
        'Station': ["Pechiparai Source", "Kaliyal", "Thirparappu", "Moovattumugham", "Thickurichy",
                    "Vayakalloor Junction", "Parakanni Check Dam", "Thengapattanam", "Ponmanai", "Surulacode"],
        'Type': ["Main"] * 8 + ["Branch"] * 2,
        'Lat': [8.4496, 8.3997, 8.3923, 8.3418, 8.3147, 8.2616, 8.2529, 8.2384, 8.3480, 8.3610],
        'Lon': [77.3073, 77.2586, 77.2577, 77.2526, 77.2441, 77.1623, 77.1625, 77.1698, 77.330, 77.350],
        'Gamma': [0.12, 0.22, 0.35, 0.61, 0.44, 2.40, 0.95, 3.82, 0.38, 0.16],
        'Mineral': ["Granite/Gneiss", "Alluvial", "Feldspar", "Quartz", "Sedimentary", "Monazite Sand", "Ilmenite",
                    "Thorium-rich Sand", "Clay/Loam", "Laterite"]
    }
    return pd.DataFrame(data)


df = get_verified_data()

# --- 3. HEADER SECTION ---
st.markdown('<div class="section-header"><h1>🛡️ Thamirabarani Basin Dashboard</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📍 Control Panel")
    view_mode = st.radio("Navigation", ["Full Basin", "Primary Path", "Secondary Branch"])
    occ_factor = st.slider("Occupancy Factor", 0.1, 1.0, 0.2)

# Branch Logic: Ensure Pechiparai (S1) shows in all views
if view_mode == "Primary Path":
    filtered_df = df[df['Type'] == "Main"]
elif view_mode == "Secondary Branch":
    # Include S1 + S9 + S10
    filtered_df = pd.concat([df.iloc[[0]], df[df['Type'] == "Branch"]])
else:
    filtered_df = df

# --- 4. MAP INTERACTIVITY ---
col_map, col_details = st.columns([1.5, 1])

with col_map:
    st.subheader("📍 Interactive Hydrological Map")
    m = folium.Map(location=[8.35, 77.26], zoom_start=11, tiles="CartoDB positron")

    # Static Paths
    folium.PolyLine(df[df['Type'] == "Main"][['Lat', 'Lon']].values.tolist(), color="#1a5276", weight=5).add_to(m)
    branch_pts = [[df.iloc[0]['Lat'], df.iloc[0]['Lon']], [df.iloc[8]['Lat'], df.iloc[8]['Lon']],
                  [df.iloc[9]['Lat'], df.iloc[9]['Lon']]]
    folium.PolyLine(branch_pts, color="#229954", weight=5, dash_array='5, 5').add_to(m)

    for i, r in filtered_df.iterrows():
        color = "green" if r['Type'] == "Branch" else "blue"
        folium.Marker([r['Lat'], r['Lon']], popup=r['Station'], icon=folium.Icon(color=color, icon="tint")).add_to(m)

    output = st_folium(m, width="100%", height=500)

with col_details:
    st.subheader("📝 Site Specifics")
    # Capture Map Click
    if output.get("last_object_clicked_popup"):
        clicked_name = output["last_object_clicked_popup"]
        site_data = df[df['Station'] == clicked_name].iloc[0]

        st.success(f"**Station Selected: {site_data['Station']}**")
        st.write(f"🌐 **Coordinates:** {site_data['Lat']}, {site_data['Lon']}")
        st.write(f"☢️ **Gamma Level:** {site_data['Gamma']} µSv/h")
        st.write(f"🪨 **Soil/Mineral:** {site_data['Mineral']}")

        # Risk Metric for Selected Point
        aed_val = (site_data['Gamma'] * 8.76 * occ_factor * 0.7)
        st.metric("Annual Dose (AED)", f"{aed_val:.4f} mSv/y")
    else:
        st.info("Click a pin on the map to view coordinates, gamma levels, and soil data.")

# --- 5. VISUALIZATION HEADER ---
st.markdown('<div class="section-header"><h2>📊 Spatial Correlation & Visual Analysis</h2></div>',
            unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔥 Radiation Heatmap", "📈 Exposure Gradient", "📉 Risk Scatter"])

with tab1:
    # Heatmap Correlation Plotly
    fig_heat = px.density_mapbox(df, lat='Lat', lon='Lon', z='Gamma', radius=30,
                                 mapbox_style="carto-positron", title="Gamma Intensity Heatmap")
    st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    fig_bar = px.bar(filtered_df, x='Station', y='Gamma', color='Gamma', color_continuous_scale='Bluered')
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    filtered_df['AED'] = (filtered_df['Gamma'] * 8.76 * occ_factor * 0.7)
    fig_risk = px.scatter(filtered_df, x='Gamma', y='AED', size='Gamma', color='Station',
                          title="Gamma vs. AED Correlation")
    st.plotly_chart(fig_risk, use_container_width=True)

# --- 6. ANALYSIS HEADER ---
st.markdown('<div class="section-header"><h2>🧬 Comprehensive Risk Analysis</h2></div>', unsafe_allow_html=True)

# Risk Facts and Metrics
c1, c2, c3 = st.columns(3)
with c1:
    st.write("### ☢️ Exposure Risk")
    st.write("- **Low Risk:** < 0.2 µSv/h")
    st.write("- **Moderate Risk:** 0.2 - 1.0 µSv/h")
    st.write("- **High Risk:** > 1.0 µSv/h (Coastal Areas)")
with c2:
    st.write("### 🏥 Health Implications")
    avg_elcr = (filtered_df['Gamma'].mean() * 8.76 * occ_factor * 0.7 * 0.05 * 70 / 1000)
    st.metric("Avg Lifetime Risk (ELCR)", f"{avg_elcr:.5f}")
    st.caption("Standard safety limit: 0.00029")
with c3:
    st.write("### 🪨 Mineral Impact")
    st.write("Higher gamma levels at **Thengapattanam** are correlated with heavy mineral monazite deposits.")

st.divider()
st.caption("Developed for CSE Project | Thamirabarani Basin Environmental Study 2026")