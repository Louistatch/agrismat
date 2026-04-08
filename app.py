import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from api.sol import get_soil, TEXTURE_PARAMS
from api.pluie import get_climate
from api.geo import get_location_info
from models.irrigation import compute_monthly_needs
from utils.kc_values import KC_VALUES, IRRIGATION_SYSTEMS, MOIS, JOURS_MOIS

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agri-Smart · Irrigation Expert System",
    layout="wide",
    page_icon=None,
    initial_sidebar_state="expanded",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
C = {
    "bg":        "#f8fafc",
    "surface":   "#ffffff",
    "border":    "#e2e8f0",
    "border_lt": "#f1f5f9",
    "primary":   "#166534",
    "primary_lt":"#dcfce7",
    "accent":    "#16a34a",
    "warn":      "#b45309",
    "warn_lt":   "#fef3c7",
    "blue":      "#1d4ed8",
    "blue_lt":   "#dbeafe",
    "muted":     "#64748b",
    "subtle":    "#94a3b8",
    "text":      "#0f172a",
    "text_md":   "#334155",
    "chart":     ["#166534","#16a34a","#1d4ed8","#b45309","#7c3aed","#0e7490","#be185d"],
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
}}

/* ── Sidebar dark ── */
section[data-testid="stSidebar"] > div:first-child {{
    background-color: #0f172a;
    padding-top: 0;
}}
/* Tous les textes sidebar en clair */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {{
    color: #cbd5e1;
}}
/* Inputs sidebar : fond sombre, texte clair */
section[data-testid="stSidebar"] input {{
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border-color: #334155 !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: #1e293b !important;
    border-color: #334155 !important;
    color: #f1f5f9 !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] span {{
    color: #f1f5f9 !important;
}}
/* Dropdown options */
[data-baseweb="popover"] [role="option"] {{
    background-color: #1e293b;
    color: #f1f5f9;
}}
[data-baseweb="popover"] [role="option"]:hover {{
    background-color: #166534;
}}
/* Multiselect tags */
section[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: #166534 !important;
    color: #fff !important;
}}

/* ── Topbar ── */
.topbar {{
    display: flex; align-items: flex-start; justify-content: space-between;
    padding: 20px 0 14px; border-bottom: 1px solid {C['border']};
    margin-bottom: 24px;
}}
.topbar-left {{ display: flex; align-items: center; gap: 14px; }}
.topbar-mark {{
    width: 32px; height: 32px; border-radius: 5px;
    background: {C['primary']}; flex-shrink: 0;
}}
.topbar-name {{ font-size: 17px; font-weight: 700; color: {C['text']}; letter-spacing: -0.3px; }}
.topbar-sub  {{ font-size: 12px; color: {C['subtle']}; margin-top: 2px; }}
.topbar-meta {{ font-size: 11px; color: {C['subtle']}; text-align: right; line-height: 1.7; }}

/* ── Section divider ── */
.sec {{
    display: flex; align-items: baseline; gap: 12px;
    margin: 28px 0 14px; padding-bottom: 8px;
    border-bottom: 1px solid {C['border']};
}}
.sec-title {{
    font-size: 11px; font-weight: 700; color: {C['text']};
    text-transform: uppercase; letter-spacing: 0.08em;
}}
.sec-badge {{
    font-size: 10px; font-weight: 600; color: {C['accent']};
    background: {C['primary_lt']}; padding: 1px 7px;
    border-radius: 3px; margin-left: auto;
}}

/* ── Data cells ── */
.dcell {{
    background: {C['border_lt']}; border-radius: 6px;
    padding: 10px 12px; text-align: center;
    border: 1px solid {C['border']};
}}
.dcell-label {{
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: {C['subtle']};
}}
.dcell-value {{
    font-size: 16px; font-weight: 600; color: {C['text']}; margin-top: 3px;
}}

/* ── KPI cards ── */
.kpi {{
    background: {C['surface']}; border: 1px solid {C['border']};
    border-radius: 8px; padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}}
.kpi-label {{
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.09em; color: {C['subtle']}; margin-bottom: 8px;
}}
.kpi-value {{ font-size: 26px; font-weight: 700; line-height: 1; margin-bottom: 4px; }}
.kpi-sub   {{ font-size: 11px; color: {C['subtle']}; }}

/* ── Source tag ── */
.stag {{
    display: inline-block; font-size: 9px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.07em;
    padding: 2px 7px; border-radius: 3px; margin-bottom: 10px;
    background: {C['border_lt']}; color: {C['muted']};
    border: 1px solid {C['border']};
}}

/* ── Sidebar section label ── */
.slabel {{
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #475569;
    padding: 12px 0 4px; display: block;
}}

/* ── Button override ── */
.stButton > button {{
    background: {C['primary']} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 5px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 8px 14px !important;
    letter-spacing: 0.02em !important;
    transition: background 0.1s !important;
}}
.stButton > button:hover {{ background: #14532d !important; }}

/* ── Metric widget ── */
div[data-testid="stMetric"] {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 7px;
    padding: 12px 14px;
}}
div[data-testid="stMetricLabel"] > div {{
    font-size: 11px !important;
    color: {C['subtle']} !important;
    font-weight: 500 !important;
}}
div[data-testid="stMetricValue"] > div {{
    font-size: 22px !important;
    font-weight: 700 !important;
    color: {C['text']} !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {{
    font-size: 12px; font-weight: 500;
    color: {C['subtle']}; padding: 8px 14px;
}}
.stTabs [aria-selected="true"] {{
    color: {C['primary']} !important;
    font-weight: 600 !important;
    border-bottom: 2px solid {C['primary']} !important;
}}

/* ── Dataframe ── */
.stDataFrame {{ border-radius: 7px; border: 1px solid {C['border']} !important; }}

/* ── Spinner ── */
div[data-testid="stSpinner"] > div {{ color: {C['primary']} !important; }}

/* ── Remove Streamlit default padding top ── */
.block-container {{ padding-top: 1rem !important; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def sec(title, badge=None):
    b = f'<span class="sec-badge">{badge}</span>' if badge else ""
    st.markdown(f'<div class="sec"><span class="sec-title">{title}</span>{b}</div>',
                unsafe_allow_html=True)

def dcell(label, value):
    return (f'<div class="dcell">'
            f'<div class="dcell-label">{label}</div>'
            f'<div class="dcell-value">{value}</div>'
            f'</div>')

def kpi(col, label, value, sub, color):
    col.markdown(
        f'<div class="kpi">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

def stag(text):
    st.markdown(f'<span class="stag">{text}</span>', unsafe_allow_html=True)

def chart_base(fig, height=300):
    fig.update_layout(
        height=height,
        margin=dict(t=12, b=40, l=4, r=4),
        template="plotly_white",
        font=dict(family="Inter, system-ui, sans-serif", size=11, color=C["text_md"]),
        plot_bgcolor=C["surface"],
        paper_bgcolor=C["surface"],
        legend=dict(orientation="h", y=-0.35, x=0, font=dict(size=11)),
        xaxis=dict(tickangle=-35, gridcolor=C["border_lt"], linecolor=C["border"],
                   tickfont=dict(size=10)),
        yaxis=dict(gridcolor=C["border_lt"], linecolor=C["border"],
                   tickfont=dict(size=10)),
    )
    return fig

# ── Session state ─────────────────────────────────────────────────────────────
for _k, _v in [("soil_data", None), ("climate_data", None),
               ("loaded_lat", 9.55), ("loaded_lon", 1.19),
               ("loaded_texture", "Limoneux")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:18px 0 10px">
      <div style="font-size:15px;font-weight:700;color:#f1f5f9;letter-spacing:-0.2px">Agri-Smart</div>
      <div style="font-size:10px;color:#475569;margin-top:2px;text-transform:uppercase;letter-spacing:0.06em">Irrigation Expert System</div>
    </div>
    <hr style="border:none;border-top:1px solid #1e293b;margin:0 0 12px">
    """, unsafe_allow_html=True)

    st.markdown('<span class="slabel">Localisation</span>', unsafe_allow_html=True)

    # ── Géolocalisation par IP (côté serveur, sans permission navigateur) ─
    from api.geo import get_ip_location

    geo_btn = st.button("Detecter ma position", use_container_width=True, key="geo_btn")
    if geo_btn:
        with st.spinner("Localisation en cours..."):
            ip_loc = get_ip_location()
        if ip_loc:
            st.session_state["loaded_lat"] = round(ip_loc["lat"], 4)
            st.session_state["loaded_lon"] = round(ip_loc["lon"], 4)
            st.session_state["soil_data"]  = None
            city_str = ip_loc.get("city", "")
            st.markdown(
                f'<div style="font-size:10px;color:#22c55e;margin-top:2px">'
                f'Position detectee · {city_str} · {ip_loc["lat"]:.4f}N, {ip_loc["lon"]:.4f}E</div>',
                unsafe_allow_html=True
            )
            st.rerun()
        else:
            st.markdown(
                '<div style="font-size:10px;color:#f87171;margin-top:2px">'
                'Localisation indisponible. Saisissez les coordonnees manuellement.</div>',
                unsafe_allow_html=True
            )

    c1, c2 = st.columns(2)
    lat = c1.number_input("Lat", value=st.session_state["loaded_lat"], format="%.4f", step=0.01)
    lon = c2.number_input("Lon", value=st.session_state["loaded_lon"], format="%.4f", step=0.01)

    st.markdown('<span class="slabel">Type de sol</span>', unsafe_allow_html=True)
    texture = st.selectbox(
        "Texture", list(TEXTURE_PARAMS.keys()),
        index=list(TEXTURE_PARAMS.keys()).index(st.session_state["loaded_texture"]),
        label_visibility="collapsed",
        help="ROSETTA v3 (USDA-ARS) calcule FC, WP, RU et RFU via van Genuchten."
    )
    st.markdown(
        '<div style="font-size:10px;color:#475569;margin-top:-4px;margin-bottom:2px">'
        'ROSETTA v3 · USDA-ARS · van Genuchten</div>',
        unsafe_allow_html=True
    )

    st.markdown('<span class="slabel">Système d\'irrigation</span>', unsafe_allow_html=True)
    system_name = st.selectbox("Système", list(IRRIGATION_SYSTEMS.keys()), index=1,
                                label_visibility="collapsed")
    eff = IRRIGATION_SYSTEMS[system_name]["efficiency"]
    st.markdown(
        f'<div style="font-size:10px;color:#475569;margin-top:-4px">Efficience : {int(eff*100)}%</div>',
        unsafe_allow_html=True
    )

    st.markdown('<span class="slabel">Cultures</span>', unsafe_allow_html=True)
    selected_crops = st.multiselect("Cultures", list(KC_VALUES.keys()),
                                     default=["Tomate", "Oignon"],
                                     label_visibility="collapsed")
    crop_areas = {}
    for crop in selected_crops:
        crop_areas[crop] = st.number_input(
            f"{crop} (ha)", value=1.0, min_value=0.1, step=0.5,
            key=f"ha_{crop}", format="%.1f"
        )

    load_btn = st.button("Actualiser", use_container_width=True, type="primary")

    st.markdown(
        '<hr style="border:none;border-top:1px solid #1e293b;margin:16px 0 10px">'
        '<div style="font-size:9px;color:#334155;text-align:center;line-height:1.8">'
        'NASA POWER Climatology · ROSETTA USDA-ARS<br>'
        'Données libres · FAO-56 Penman-Monteith</div>',
        unsafe_allow_html=True
    )

# ── Data loading ──────────────────────────────────────────────────────────────
topbar_slot = st.empty()

@st.cache_data(ttl=3600,  show_spinner=False)
def load_climate(lat, lon):    return get_climate(lat, lon)

@st.cache_data(ttl=86400, show_spinner=False)
def load_soil(texture):        return get_soil(texture)

@st.cache_data(ttl=3600,  show_spinner=False)
def load_location(lat, lon):   return get_location_info(lat, lon)

needs_reload = (
    st.session_state["soil_data"] is None or load_btn
    or lat != st.session_state["loaded_lat"]
    or lon != st.session_state["loaded_lon"]
    or texture != st.session_state["loaded_texture"]
)

if needs_reload:
    with st.spinner("Chargement…"):
        soil_data    = load_soil(texture)
        climate_data = load_climate(lat, lon)
        loc_info     = load_location(lat, lon)
    st.session_state.update({
        "soil_data": soil_data, "climate_data": climate_data,
        "loc_info": loc_info, "loaded_lat": lat, "loaded_lon": lon,
        "loaded_texture": texture,
    })

soil_data    = st.session_state["soil_data"]
climate_data = st.session_state["climate_data"]
loc_info     = st.session_state.get("loc_info", {"display": f"{lat:.4f}N {lon:.4f}E", "altitude": None})

# Topbar
alt = f"  ·  {loc_info['altitude']:.0f} m alt." if loc_info.get("altitude") else ""
loc_display = loc_info.get("display", f"{lat:.4f}N, {lon:.4f}E")
topbar_slot.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-mark"></div>
    <div>
      <div class="topbar-name">Agri-Smart</div>
      <div class="topbar-sub">{loc_display}{alt}</div>
    </div>
  </div>
  <div class="topbar-meta">
    {soil_data['texture']} · RU {soil_data['RU']} mm/m<br>
    {climate_data['source']}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sol & Climat ──────────────────────────────────────────────────────────────
sec("Profil pédologique & climatique", badge=f"{lat:.3f}N · {lon:.3f}E")

col_soil, col_clim = st.columns([11, 9], gap="large")

with col_soil:
    stag(soil_data["source"])
    g1 = (f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:8px">'
          f'{dcell("Texture", soil_data["texture"])}'
          f'{dcell("RU mm/m", soil_data["RU"])}'
          f'{dcell("RFU mm/m", soil_data["RFU"])}'
          f'</div>'
          f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">'
          f'{dcell("Argile", str(soil_data["clay_pct"])+"%")}'
          f'{dcell("Sable",  str(soil_data["sand_pct"])+"%")}'
          f'{dcell("Limon",  str(soil_data["silt_pct"])+"%")}'
          f'</div>')
    st.markdown(g1, unsafe_allow_html=True)
    st.caption(
        f"FC {soil_data['fc_pct']}%  ·  WP {soil_data['wp_pct']}%  ·  "
        f"Densité apparente {soil_data['bdod']} g/cm³"
    )

with col_clim:
    stag(climate_data["source"])
    cc1, cc2 = st.columns(2)
    cc1.metric("Précipitations annuelles", f"{climate_data['total_precip']:.0f} mm")
    cc2.metric("Température moyenne", f"{climate_data['avg_temp']:.1f} °C")

    _idx    = [3,4,5,6,7,8,9,10,11,0,1,2]
    etp_avr = [climate_data["etp_mensuelle"][i]   for i in _idx]
    plu_avr = [climate_data["pluie_mensuelle"][i] for i in _idx]
    etm_avr = [e * j for e, j in zip(etp_avr, JOURS_MOIS)]

    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(x=MOIS, y=plu_avr, name="Précipitations (mm)",
                           marker=dict(color=C["blue"], opacity=0.5)))
    fig_c.add_trace(go.Scatter(x=MOIS, y=etm_avr, name="ETP mensuelle (mm)",
                               mode="lines+markers",
                               line=dict(color=C["warn"], width=2),
                               marker=dict(size=4)))
    fig_c = chart_base(fig_c, height=195)
    fig_c.update_layout(margin=dict(t=6, b=52, l=4, r=4))
    st.plotly_chart(fig_c)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not selected_crops:
    st.markdown(
        f'<div style="background:{C["border_lt"]};border:1px dashed {C["border"]};'
        f'border-radius:8px;padding:40px;text-align:center;margin-top:24px">'
        f'<div style="font-size:14px;font-weight:600;color:{C["text_md"]}">Aucune culture sélectionnée</div>'
        f'<div style="font-size:12px;color:{C["subtle"]};margin-top:6px">'
        f'Sélectionnez au moins une culture dans le panneau latéral.</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.stop()

# ── Calculs ───────────────────────────────────────────────────────────────────
all_dfs = {
    crop: compute_monthly_needs(crop, crop_areas[crop], soil_data, system_name, climate_data)
    for crop in selected_crops
}
total_saison = sum(df["volume_total"].sum() for df in all_dfs.values())
total_ha     = sum(crop_areas.values())
mois_pic, vol_pic = max(
    ((m, sum(df.loc[df["mois"] == m, "volume_total"].values[0] for df in all_dfs.values()))
     for m in MOIS), key=lambda x: x[1]
)
debit_pompe = (vol_pic / 30 / 12) * 0.277

# ── KPIs ──────────────────────────────────────────────────────────────────────
sec("Indicateurs de saison", badge=f"{len(selected_crops)} culture{'s' if len(selected_crops)>1 else ''}")

k1, k2, k3, k4 = st.columns(4, gap="small")
kpi(k1, "Volume total saison",
    f"{total_saison:,.0f} m³", f"{total_ha:.1f} ha · {system_name}", C["primary"])
kpi(k2, "Mois de pointe",
    mois_pic, f"{vol_pic:,.0f} m³  ·  pic de demande", C["warn"])
kpi(k3, "Débit pompe estimé",
    f"{debit_pompe:.2f} L/s", "Pompage 12 h/j · mois de pointe", C["blue"])
kpi(k4, "Moyenne mensuelle",
    f"{total_saison/12:,.0f} m³",
    f"Efficience {int(eff*100)}%  ·  {system_name}", C["text_md"])

# ── Tableau besoins ───────────────────────────────────────────────────────────
sec("Besoins en eau par culture", badge="m³/ha/mois · FAO-56")

rows_table = []
for crop, df in all_dfs.items():
    row = {"Culture": crop}
    for _, r in df.iterrows():
        row[r["mois"]] = r["volume_ha"]
    row["Total/ha (m³)"]   = round(df["volume_ha"].sum(), 1)
    row["Superficie (ha)"] = crop_areas[crop]
    row["Total (m³)"]      = round(df["volume_total"].sum(), 1)
    rows_table.append(row)

pivot_df = pd.DataFrame(rows_table).set_index("Culture")
total_row = {"Superficie (ha)": sum(crop_areas.values())}
for m in MOIS:
    total_row[m] = round(pivot_df[m].sum(), 1) if m in pivot_df.columns else 0
total_row["Total/ha (m³)"] = round(pivot_df["Total/ha (m³)"].mean(), 1)
total_row["Total (m³)"]    = round(pivot_df["Total (m³)"].sum(), 1)
pivot_df.loc["TOTAL"] = total_row
pivot_df = pivot_df[MOIS + ["Total/ha (m³)", "Superficie (ha)", "Total (m³)"]]

month_cols = [c for c in pivot_df.columns if c in MOIS]
st.dataframe(
    pivot_df.style
        .format("{:.1f}")
        .bar(subset=month_cols, color=["#dcfce7", "#166534"], axis=None)
        .set_properties(subset=pd.IndexSlice[["TOTAL"], :],
                        **{"font-weight": "600", "background-color": "#f0fdf4",
                           "color": C["primary"]})
        .set_properties(**{"font-size": "12px"}),
    height=min(90 + 38 * len(pivot_df), 520),
)

# ── Graphiques ────────────────────────────────────────────────────────────────
sec("Analyse visuelle")

gc1, gc2 = st.columns(2, gap="medium")

with gc1:
    st.markdown(
        f'<div style="font-size:11px;font-weight:600;color:{C["text_md"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px">'
        f'Besoins mensuels par culture (m³/ha)</div>',
        unsafe_allow_html=True
    )
    chart_data = [
        {"Mois": r["mois"], "Culture": crop, "m³/ha": r["volume_ha"]}
        for crop, df in all_dfs.items() for _, r in df.iterrows()
    ]
    fig_bar = px.bar(pd.DataFrame(chart_data), x="Mois", y="m³/ha", color="Culture",
                     category_orders={"Mois": MOIS}, barmode="group",
                     color_discrete_sequence=C["chart"])
    fig_bar = chart_base(fig_bar, height=300)
    fig_bar.update_traces(marker_line_width=0)
    st.plotly_chart(fig_bar)

with gc2:
    st.markdown(
        f'<div style="font-size:11px;font-weight:600;color:{C["text_md"]};'
        f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px">'
        f'Coefficients culturaux Kc — FAO-56</div>',
        unsafe_allow_html=True
    )
    kc_data = [
        {"Mois": m, "Culture": crop, "Kc": KC_VALUES[crop]["kc"][i]}
        for crop in selected_crops for i, m in enumerate(MOIS)
    ]
    fig_kc = px.line(pd.DataFrame(kc_data), x="Mois", y="Kc", color="Culture",
                     category_orders={"Mois": MOIS}, markers=True,
                     color_discrete_sequence=C["chart"])
    fig_kc = chart_base(fig_kc, height=300)
    fig_kc.update_traces(line_width=2, marker_size=5)
    fig_kc.add_hline(y=1.0, line_dash="dot", line_color=C["subtle"],
                     annotation_text="Kc = 1.0", annotation_font_size=10,
                     annotation_position="bottom right")
    st.plotly_chart(fig_kc)

# ── Bilan hydrique détaillé ───────────────────────────────────────────────────
sec("Bilan hydrique détaillé")

tabs = st.tabs([f"  {crop}  " for crop in selected_crops])
for tab, crop in zip(tabs, selected_crops):
    with tab:
        df = all_dfs[crop]
        mk1, mk2, mk3, mk4 = st.columns(4)
        mk1.metric("Volume total",    f"{df['volume_total'].sum():,.0f} m³", f"{crop_areas[crop]} ha")
        mk2.metric("Besoin net max",  f"{df['besoin_net'].max():.0f} mm",
                   df.loc[df['besoin_net'].idxmax(), 'mois'])
        mk3.metric("Kc moyen",        f"{df['kc'].mean():.2f}")
        mk4.metric("ETP moyenne",     f"{df['etp'].mean():.2f} mm/j")

        detail = df[["mois","nb_jours","etp","kc","z","etm",
                      "pluie","peff","rfu","besoin_net","besoin_brut",
                      "volume_ha","volume_total"]].copy()
        detail.columns = [
            "Mois","Jours","ETP (mm/j)","Kc","Z (m)","ETM (mm)",
            "Pluie (mm)","Peff (mm)","RFU (mm)",
            "Besoin net (mm)","Besoin brut (mm)","Vol. (m³/ha)","Vol. total (m³)"
        ]
        detail = detail.set_index("Mois")
        sums = detail.sum(numeric_only=True)
        sums["ETP (mm/j)"] = round(df["etp"].mean(), 2)
        sums["Kc"]         = round(df["kc"].mean(), 2)
        sums["Z (m)"]      = round(df["z"].mean(), 2)
        detail.loc["TOTAL"] = sums

        st.dataframe(
            detail.style
                  .format("{:.2f}")
                  .bar(subset=["Vol. (m³/ha)"],    color=["#dcfce7","#166534"])
                  .bar(subset=["Besoin net (mm)"],  color=["#fef3c7","#b45309"])
                  .set_properties(subset=pd.IndexSlice[["TOTAL"], :],
                                  **{"font-weight":"600","background-color":"#f0fdf4",
                                     "color":C["primary"]})
                  .set_properties(**{"font-size":"12px"}),
            height=530,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="margin-top:48px;padding:16px 0 8px;border-top:1px solid {C["border"]};'
    f'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">'
    f'<div style="font-size:11px;color:{C["subtle"]}">'
    f'Agri-Smart · FAO-56 Penman-Monteith · ROSETTA v3 USDA-ARS · NASA POWER Climatology'
    f'</div>'
    f'<div style="font-size:11px;color:{C["subtle"]}">'
    f'{soil_data["texture"]} · RU {soil_data["RU"]} mm/m · '
    f'{lat:.4f}N, {lon:.4f}E'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True
)
