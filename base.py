import streamlit as st
import pandas as pd
import plotly.express as px
import math
import streamlit.components.v1 as components
from premium_theme import (
    inject_premium_theme, render_sidebar_brand, render_page_header,
    apply_plotly_theme, MRU_COLORS_PREMIUM, CHARGED_COLOR_PREMIUM
)

st.set_page_config(
    page_title="Sitapur PNG — Field Intelligence",
    layout="wide",
    page_icon="🔵",
    initial_sidebar_state="expanded",
)
inject_premium_theme()

# ── Floating sidebar toggle pill ──
components.html("""
<script>
(function(){
    const pdoc = window.parent.document;
    if (pdoc.getElementById('sb-toggle-injected')) return;

    const style = pdoc.createElement('style');
    style.textContent = `
        #sb-toggle-injected {
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            z-index: 999999;
            width: 20px;
            height: 72px;
            background: linear-gradient(180deg,
                transparent 0%, rgba(0,212,255,0.3) 50%, transparent 100%);
            border: none;
            border-right: 2px solid rgba(0,212,255,0.55);
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            transition: width 180ms ease, background 180ms ease;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
        }
        #sb-toggle-injected:hover {
            width: 28px;
            background: linear-gradient(180deg,
                transparent 0%, rgba(0,212,255,0.5) 50%, transparent 100%);
            border-right: 2px solid rgba(0,212,255,0.9);
            box-shadow: 3px 0 18px rgba(0,212,255,0.3);
        }
        #sb-toggle-injected svg {
            width: 10px; height: 10px;
            transition: transform 300ms ease;
        }
        #sb-toggle-injected.closed svg { transform: rotate(180deg); }
        [data-testid="stSidebar"] {
            transition: transform 280ms cubic-bezier(0.16,1,0.3,1) !important;
        }
    `;
    pdoc.head.appendChild(style);

    const btn = pdoc.createElement('button');
    btn.id = 'sb-toggle-injected';
    btn.className = 'open';
    btn.title = 'Toggle sidebar';
    btn.innerHTML = `<svg viewBox="0 0 10 16" xmlns="http://www.w3.org/2000/svg">
        <polyline points="7,2 2,8 7,14" stroke="rgba(0,212,255,0.9)"
            stroke-width="2" fill="none" stroke-linecap="round"/></svg>`;
    pdoc.body.appendChild(btn);

    let open = true;
    const D = 280;

    function getSbWidth() {
        const sb = pdoc.querySelector('[data-testid="stSidebar"]');
        return sb ? sb.getBoundingClientRect().width : 0;
    }

    btn.addEventListener('click', () => {
        open = !open;
        btn.className = open ? 'open' : 'closed';
        const sidebar = pdoc.querySelector('[data-testid="stSidebar"]');
        const appView = pdoc.querySelector('[data-testid="stAppViewContainer"]');
        if (!open) {
            if (sidebar) {
                sidebar.style.transform = 'translateX(-100%)';
                sidebar.style.pointerEvents = 'none';
                sidebar.style.position = 'fixed';
                sidebar.style.top = '0';
                sidebar.style.left = '0';
            }
            if (appView) {
                appView.style.transition = 'grid-template-columns '+D+'ms cubic-bezier(0.16,1,0.3,1)';
                appView.style.setProperty('grid-template-columns', '0px 1fr', 'important');
            }
            btn.style.transition = 'left '+D+'ms cubic-bezier(0.16,1,0.3,1), width 180ms ease, background 180ms ease';
            btn.style.left = '0px';
        } else {
            if (sidebar) {
                sidebar.style.transition = 'transform '+D+'ms cubic-bezier(0.16,1,0.3,1)';
                sidebar.style.transform = 'translateX(0)';
                sidebar.style.pointerEvents = 'auto';
                sidebar.style.position = '';
            }
            if (appView) {
                appView.style.transition = 'grid-template-columns '+D+'ms cubic-bezier(0.16,1,0.3,1)';
                appView.style.removeProperty('grid-template-columns');
            }
            setTimeout(() => {
                btn.style.transition = 'left '+D+'ms cubic-bezier(0.16,1,0.3,1), width 180ms ease, background 180ms ease';
                btn.style.left = (getSbWidth() - 10) + 'px';
            }, D);
        }
    });

    function init() {
        const w = getSbWidth();
        if (w > 0) { btn.style.transition = 'none'; btn.style.left = (w - 10) + 'px'; }
        else setTimeout(init, 100);
    }
    setTimeout(init, 600);
})();
</script>
""", height=0)

render_page_header(
    "Sitapur PNG",
    "Field Intelligence Dashboard · BPCL · Real-time connection & adoption tracking"
)

# AREAS: (MRU, Main_Area, Subarea, Lat, Lon, Radius_m)
AREAS = [
    ("MRU-1", "Naipalapur",   "Adarsh Nagar",       27.570658, 80.705658, 500),
    ("MRU-1", "Naipalapur",   "Anand Nagar",         27.565406, 80.698234, 500),
    ("MRU-1", "Naipalapur",   "Bhawanpurva",         27.563448, 80.699677, 500),
    ("MRU-1", "Naipalapur",   "Naipalapur",          27.569612, 80.707943, 500),
    ("MRU-1", "Naipalapur",   "Rampurva",            27.571666, 80.711863, 450),
    ("MRU-1", "Naipalapur",   "Rasoolganj",          27.565058, 80.685057, 450),
    ("MRU-1", "Naipalapur",   "Sheeshmahal",         27.566405, 80.704909, 750),
    ("MRU-1", "Naipalapur",   "Tedva Chilaula",      27.583000, 80.714000, 450),
    ("MRU-2", "Panchampurva", "Panchampurva",        27.574500, 80.697745, 450),
    ("MRU-2", "Panchampurva", "Guru Nanak Colony",   27.568539, 80.694437, 380),
    ("MRU-2", "Panchampurva", "Gwal Mandi",          27.569887, 80.695104, 380),
    ("MRU-2", "Panchampurva", "Subhash Nagar",       27.565498, 80.696172, 380),
    ("MRU-5", "Lohar Bagh",   "Agha Colony",         27.567920, 80.669094, 380),
    ("MRU-5", "Lohar Bagh",   "Arya Nagar",          27.561750, 80.684590, 400),
    ("MRU-5", "Lohar Bagh",   "Awas Vikas Block A",  27.556362, 80.695399, 380),
    ("MRU-5", "Lohar Bagh",   "Awas Vikas Block C",  27.557036, 80.694145, 380),
    ("MRU-5", "Lohar Bagh",   "Baijnath Colony",     27.565760, 80.662577, 380),
    ("MRU-5", "Lohar Bagh",   "Chitra Colony",       27.534327, 80.678973, 900),
    ("MRU-5", "Lohar Bagh",   "Civil Lines",         27.565208, 80.677026, 450),
    ("MRU-5", "Lohar Bagh",   "Ghuramau Bangla",     27.561129, 80.679560, 380),
    ("MRU-5", "Lohar Bagh",   "Kathalibagh",         27.563448, 80.680601, 380),
    ("MRU-5", "Lohar Bagh",   "Lohar Bagh",          27.564353, 80.680572, 380),
    ("MRU-5", "Lohar Bagh",   "Prem Nagar",          27.563113, 80.669788, 500),
    ("MRU-5", "Lohar Bagh",   "Sanjay Nagar",        27.559508, 80.678829, 450),
    ("MRU-6", "Roti Godam",   "Shivpuri",            27.551579, 80.694123, 750),
    ("MRU-6", "Roti Godam",   "Awas Vikas Block B",  27.557036, 80.694145, 380),
    ("MRU-6", "Roti Godam",   "Brampuri",            27.555267, 80.673801, 380),
    ("MRU-6", "Roti Godam",   "Gangdhar Nagar",      27.568016, 80.678952, 750),
    ("MRU-6", "Roti Godam",   "Lal Kurti",           27.543446, 80.677859, 900),
    ("MRU-6", "Roti Godam",   "Naimishpuram",        27.542000, 80.686000, 700),
    ("MRU-6", "Roti Godam",   "Roti Godam",          27.557300, 80.670058, 380),
    ("MRU-6", "Roti Godam",   "Sudamapuri",          27.556831, 80.672347, 380),
    ("MRU-6", "Roti Godam",   "Sultanpur",           27.557300, 80.670058, 380),
    ("MRU-6", "Roti Godam",   "Vanasiya",            27.549004, 80.683000, 700),
    ("MRU-7", "Husain Ganj",  "Azad Nagar",          27.564767, 80.694089, 500),
    ("MRU-7", "Husain Ganj",  "Budh Nagar",          27.547775, 80.709661, 380),
    ("MRU-7", "Husain Ganj",  "Bijwal Khud",         27.531405, 80.715110, 1200),
    ("MRU-7", "Husain Ganj",  "Ginni Devi",          27.543827, 80.714863, 380),
    ("MRU-7", "Husain Ganj",  "Sultanpur",           27.542446, 80.712929, 550),
    ("MRU-7", "Husain Ganj",  "Jangal Kuti",         27.560290, 80.680703, 450),
]

SITAPUR_BBOX = {
    "lat_min": 27.525, "lat_max": 27.600,
    "lon_min": 80.655, "lon_max": 80.730,
}

MRU_COLORS    = MRU_COLORS_PREMIUM
CHARGED_COLOR = CHARGED_COLOR_PREMIUM

ALL_MRUS     = sorted(set(a[0] for a in AREAS))
ALL_SUBAREAS = sorted(set(a[2] for a in AREAS))
MRU_TO_SUBS  = {}
for mru, main, sub, *_ in AREAS:
    MRU_TO_SUBS.setdefault(mru, []).append(sub)

# ── HELPERS ──────────────────────────────────────────────────────────────────────
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data
def build_classifier():
    return [(mru, main, sub, lat, lon, rad) for mru, main, sub, lat, lon, rad in AREAS]


CLASSIFIER = build_classifier()


def classify_point(lat, lon):
    best_dist = float('inf')
    best = ('Unassigned', '', 'Unassigned')
    for mru, main, sub, alat, alon, radius in CLASSIFIER:
        d = haversine_m(lat, lon, alat, alon)
        if d < radius and d < best_dist:
            best_dist = d
            best = (mru, main, sub)
    return best


def in_sitapur(lat, lon):
    return (
        SITAPUR_BBOX["lat_min"] <= lat <= SITAPUR_BBOX["lat_max"] and
        SITAPUR_BBOX["lon_min"] <= lon <= SITAPUR_BBOX["lon_max"]
    )


# ── ERROR COORDINATE FILTER ─────────────────────────────────────────────────────
ERROR_ZONES = [
    (27.5892, 80.6844, 400),
    (27.5467, 80.6600, 400),
    (27.5822, 80.7245, 400),
]


def not_error_coord(lat, lon):
    for elat, elon, erad in ERROR_ZONES:
        if haversine_m(lat, lon, elat, elon) < erad:
            return False
    return True


# ── DATA LOADERS ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_connection_data():
    df = pd.read_excel('Connection-Data.xlsx', sheet_name='Connection Data')
    df.columns = df.columns.str.strip()
    df['Latitude']  = pd.to_numeric(df['Latitude'],  errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    df['NAME']     = df['NAME'].fillna('Unknown').astype(str).str.strip()
    df['METER NO'] = df['METER NO'].fillna('').astype(str).str.strip()
    df['MOB NO']   = df['MOB NO'].fillna('').astype(str).str.strip()
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df[df.apply(lambda r: in_sitapur(r['Latitude'], r['Longitude']), axis=1)].copy()
    df = df[df.apply(lambda r: not_error_coord(r['Latitude'], r['Longitude']), axis=1)].copy()
    classified = df.apply(
        lambda r: pd.Series(classify_point(r['Latitude'], r['Longitude'])),
        axis=1
    )
    classified.columns = ['MRU', 'Main_Area', 'Subarea']
    return pd.concat([df, classified], axis=1)


@st.cache_data
def load_master_data():
    df = pd.read_excel('Master-Data.xlsx', sheet_name='Charged Data')
    df.columns = df.columns.str.strip()
    df['Latitude']        = pd.to_numeric(df['Latitude'],  errors='coerce')
    df['Longitude']       = pd.to_numeric(df['Longitude'], errors='coerce')
    df['Customer Name']   = df['Customer Name'].fillna('Unknown').astype(str).str.strip()
    df['Meter Number']    = df['Meter Number'].fillna('').astype(str).str.strip()
    df['Mobile NUMBER']   = df['Mobile NUMBER'].fillna('').astype(str).str.strip()
    df['Conversion Date'] = pd.to_datetime(df['Conversion Date'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df[df.apply(lambda r: in_sitapur(r['Latitude'], r['Longitude']), axis=1)].copy()
    df = df[df.apply(lambda r: not_error_coord(r['Latitude'], r['Longitude']), axis=1)].copy()
    classified = df.apply(
        lambda r: pd.Series(classify_point(r['Latitude'], r['Longitude'])),
        axis=1
    )
    classified.columns = ['MRU', 'Main_Area', 'Subarea']
    return pd.concat([df, classified], axis=1)


df_conn   = load_connection_data()
df_master = load_master_data()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────────
render_sidebar_brand()

# ── MAP STYLE ──
map_style = st.sidebar.selectbox(
    "🗺️ Map Style",
    ["google-satellite", "google-road", "google-terrain", "carto-darkmatter"],
    index=0,
    format_func=lambda x: {
        "google-satellite": "🛰️ Satellite (Google)",
        "google-road":      "🗺️ Road (Google)",
        "google-terrain":   "⛰️ Terrain (Google)",
        "carto-darkmatter": "🌑 Dark Matter",
    }[x]
)

# ── FILTER HIERARCHY ──
st.sidebar.markdown("""
<div style="font-size:0.6rem;font-weight:800;letter-spacing:0.18em;text-transform:uppercase;
background:linear-gradient(90deg,#00d4ff,#7c4dff);-webkit-background-clip:text;
-webkit-text-fill-color:transparent;background-clip:text;
filter:drop-shadow(0 0 4px rgba(0,212,255,0.35));margin:1.4rem 0 0.35rem;padding-left:2px;display:block">
📍 Filter Territory</div>
""", unsafe_allow_html=True)

filter_mode = st.sidebar.radio(
    "🏘️ Filter Level",
    ["All", "By MRU", "By Area", "By Subarea"],
    horizontal=False,
)

ALL_MAIN_AREAS = sorted(set(a[1] for a in AREAS))
allowed_subs = set(ALL_SUBAREAS) | {"Unassigned"}
allowed_mrus = set(ALL_MRUS) | {"Unassigned"}

if filter_mode == "By MRU":
    st.sidebar.caption("🔵 MRU")
    selected_mrus = st.sidebar.multiselect(
        "Select MRU(s)", options=ALL_MRUS, default=ALL_MRUS,
        format_func=lambda m: f"{m} — {next(a[1] for a in AREAS if a[0] == m)}"
    )
    allowed_subs = set()
    for m in selected_mrus:
        allowed_subs.update(MRU_TO_SUBS.get(m, []))
    allowed_mrus = set(selected_mrus)

elif filter_mode == "By Area":
    st.sidebar.caption("📍 Main Area")
    selected_areas = st.sidebar.multiselect(
        "Select Area(s)", options=ALL_MAIN_AREAS, default=ALL_MAIN_AREAS
    )
    allowed_subs = set(a[2] for a in AREAS if a[1] in selected_areas)
    allowed_mrus = set(a[0] for a in AREAS if a[1] in selected_areas)

elif filter_mode == "By Subarea":
    st.sidebar.caption("▸ MRU (parent)")
    parent_mrus = st.sidebar.multiselect(
        "Select MRU(s)", options=ALL_MRUS, default=ALL_MRUS,
        key="parent_mru_cascade"
    )
    cascade_subs = sorted(set(a[2] for a in AREAS if a[0] in parent_mrus))
    st.sidebar.caption("▸▸ Subarea")
    selected_subs = st.sidebar.multiselect(
        "Select Subarea(s)", options=cascade_subs, default=cascade_subs
    )
    allowed_subs = set(selected_subs)
    allowed_mrus = set(a[0] for a in AREAS if a[2] in allowed_subs)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size:0.6rem;font-weight:800;letter-spacing:0.18em;text-transform:uppercase;
color:#44445a;margin:0.2rem 0 0.35rem;padding-left:2px;display:block">
⚡ Charged Overlay</div>
""", unsafe_allow_html=True)
show_master = st.sidebar.toggle("Show Charged Data", value=True, key="show_master_tog")


def apply_area_filter(df, mode, allowed_subs, allowed_mrus):
    if mode == "All":
        return df
    return df[df['MRU'].isin(allowed_mrus) & df['Subarea'].isin(allowed_subs)]


df_conn_f   = apply_area_filter(df_conn, filter_mode, allowed_subs, allowed_mrus)
df_master_f = pd.DataFrame()

_dc2 = None
if show_master and not df_master.empty:
    df_m = apply_area_filter(df_master, filter_mode, allowed_subs, allowed_mrus)
    min_date = df_master['Conversion Date'].min()
    max_date = df_master['Conversion Date'].max()
    if pd.notna(min_date) and pd.notna(max_date):
        _dc1, _dc2 = st.sidebar.columns(2)
        date_range = _dc1.date_input(
            "📅 Conv. Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            df_master_f = df_m[
                (df_m['Conversion Date'].dt.date >= date_range[0]) &
                (df_m['Conversion Date'].dt.date <= date_range[1])
            ]
        else:
            df_master_f = df_m
    else:
        df_master_f = df_m

# ── KPI CARDS ──────────────────────────────────────────────────────────────────────
_total        = len(df_conn_f)
_charged      = len(df_master_f)
_unassigned   = len(df_conn_f[df_conn_f['MRU'] == 'Unassigned'])
_uncovered    = _total - _charged
_adoption_pct = f"{_charged / _total * 100:.1f}%" if _total > 0 else "—"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🔌 Total Connections", f"{_total:,}")
c2.metric("⚡ Charged",           f"{_charged:,}", delta=f"+{_charged:,}" if _charged > 0 else None)
c3.metric("📈 Adoption Rate",     _adoption_pct)
c4.metric("🎯 Uncovered",         f"{_uncovered:,}", delta=f"-{_uncovered:,}" if _uncovered > 0 else None, delta_color="inverse")
c5.metric("📍 Unassigned",        f"{_unassigned:,}")

with st.expander("📊 KPIs by MRU & Area — click to expand", expanded=False):
    _mru_stats = []
    for _mru in sorted(df_conn_f["MRU"].unique()):
        if _mru == "Unassigned":
            continue
        _tc = len(df_conn_f[df_conn_f["MRU"] == _mru])
        _ch = len(df_master_f[df_master_f["MRU"] == _mru]) if not df_master_f.empty else 0
        _area = next((a[1] for a in AREAS if a[0] == _mru), "—")
        _mru_stats.append({
            "MRU": _mru, "Area": _area,
            "Connections": _tc, "Charged": _ch,
            "Adoption %": f"{_ch/_tc*100:.1f}%" if _tc > 0 else "—",
            "Uncovered": _tc - _ch
        })
    if _mru_stats:
        st.dataframe(pd.DataFrame(_mru_stats).set_index("MRU"), use_container_width=True)

# ── MAP ──────────────────────────────────────────────────────────────────────────
google_tiles = {
    "google-satellite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    "google-road":      "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "google-terrain":   "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    "white-bg":         "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
}
base_style = "white-bg" if map_style in google_tiles else map_style

all_lats = list(df_conn_f['Latitude'])
all_lons = list(df_conn_f['Longitude'])
if not df_master_f.empty:
    all_lats += list(df_master_f['Latitude'])
    all_lons += list(df_master_f['Longitude'])

center_lat = pd.Series(all_lats).median() if all_lats else 27.560
center_lon = pd.Series(all_lons).median() if all_lons else 80.690

fig = px.scatter_mapbox(
    df_conn_f,
    lat='Latitude', lon='Longitude',
    hover_name='NAME',
    hover_data={
        'METER NO': True, 'MOB NO': True,
        'MRU': True, 'Subarea': True,
        'Latitude': ':.6f', 'Longitude': ':.6f',
    },
    color='MRU',
    color_discrete_map=MRU_COLORS,
    zoom=13,
    center={"lat": center_lat, "lon": center_lon},
    mapbox_style=base_style,
    height=700,
    title=f"PNG Houses — {len(df_conn_f):,} connections · {len(df_master_f):,} charged"
)
fig.update_traces(marker=dict(size=4, opacity=0.85))

if show_master and not df_master_f.empty:
    df_master_f = df_master_f.copy()
    df_master_f['Conv Date'] = (
        df_master_f['Conversion Date'].dt.strftime('%Y-%m-%d').fillna('N/A')
    )
    scatter_m = px.scatter_mapbox(
        df_master_f,
        lat='Latitude', lon='Longitude',
        hover_name='Customer Name',
        hover_data={
            'Meter Number': True, 'Mobile NUMBER': True,
            'MRU': True, 'Subarea': True,
            'Conv Date': True,
            'Latitude': ':.6f', 'Longitude': ':.6f',
        },
        color_discrete_sequence=[CHARGED_COLOR],
    )
    t = scatter_m.data[0]
    t.marker.size    = 7
    t.marker.opacity = 0.95
    t.name           = "⚡ Charged"
    t.showlegend     = True
    fig.add_trace(t)

if map_style in google_tiles:
    fig.update_layout(
        mapbox={
            "style":  "white-bg", "zoom": 13,
            "center": {"lat": center_lat, "lon": center_lon},
            "layers": [{
                "sourcetype": "raster",
                "sourceattribution": "Google",
                "source": [google_tiles[map_style]],
                "below": "traces"
            }]
        }
    )

apply_plotly_theme(fig, height=700)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    legend=dict(
        title=dict(text="MRU / STATUS", font=dict(size=9, color="#44445a", family="Inter, sans-serif")),
        bgcolor="rgba(24,24,48,0.92)",
        bordercolor="rgba(255,255,255,0.07)",
        borderwidth=1,
        font=dict(size=11, color="#8888aa", family="Inter, sans-serif"),
        x=0.01, y=0.99,
    )
)

st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# ── ANALYSIS MODULE ───────────────────────────────────────────────────────────────────
from analysis import run_analysis
run_analysis(df_conn, df_master, _dc2)
