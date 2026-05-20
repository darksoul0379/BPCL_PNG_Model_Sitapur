import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
from scipy.optimize import curve_fit
from premium_theme import apply_plotly_theme, MRU_COLORS_PREMIUM, PRIORITY_COLOR_PREMIUM

# ── Bass Diffusion helpers ─────────────────────────────────────────────────────────
def bass_cumulative(t, M, p, q):
    """Cumulative Bass adoption: N(t) = M * (1 - e^(-(p+q)*t)) / (1 + (q/p)*e^(-(p+q)*t))"""
    exp = np.exp(-(p + q) * t)
    return M * (1 - exp) / (1 + (q / p) * exp)

def fit_bass(dates_sorted, total_market):
    """Fit Bass model. Returns (p, q, M, fitted_curve, forecast_curve) or None on failure."""
    if len(dates_sorted) < 6:
        return None
    t0 = dates_sorted.min()
    t  = (dates_sorted - t0).dt.days.values.astype(float)
    cum = np.arange(1, len(t) + 1, dtype=float)
    try:
        p0 = [total_market, 0.01, 0.3]
        bounds = ([total_market * 0.5, 1e-5, 1e-5], [total_market * 3, 1.0, 2.0])
        popt, _ = curve_fit(bass_cumulative, t, cum, p0=p0, bounds=bounds, maxfev=8000)
        M, p, q = popt
        t_fore  = np.linspace(0, t[-1] * 2, 200)
        fitted  = bass_cumulative(t, M, p, q)
        forecast= bass_cumulative(t_fore, M, p, q)
        return p, q, M, t, cum, fitted, t_fore, forecast, t0
    except Exception:
        return None

# ── Effort-Impact Priority Matrix (early-stage adoption) ──────────────────────────
def priority_label(uncovered, momentum):
    """uncovered = absolute gap, momentum = conversions last 30 days."""
    high_gap = uncovered >= 20          # adjustable threshold
    high_mom = momentum >= 3            # ≥3 conversions in last 30 days
    if high_gap and high_mom:   return "🚀 Quick Win"
    if high_gap and not high_mom: return "💎 High Value"
    if not high_gap and high_mom: return "⚡ Maintain"
    return "🔁 Review"

PRIORITY_COLOR = {
    "🚀 Quick Win":  "#2ECC71",
    "💎 High Value": "#F39C12",
    "⚡ Maintain":   "#00B4D8",
    "🔁 Review":     "#95A5A6",
}


def run_analysis(df_conn, df_master, _dc2=None):
    df_c = df_conn[df_conn["MRU"] != "Unassigned"].copy()
    df_m = df_master[df_master["MRU"] != "Unassigned"].copy()
    df_m["Conversion Date"] = pd.to_datetime(df_m["Conversion Date"], errors="coerce")

    ALL_MRUS = sorted(df_c["MRU"].unique())

    # ── Area summary ──
    conn_by = df_c.groupby(["MRU","Main_Area","Subarea"]).size().reset_index(name="total_conn")
    chrg_by = df_m.groupby("Subarea").size().reset_index(name="charged")
    area_df = conn_by.merge(chrg_by, on="Subarea", how="left")
    area_df["charged"]   = area_df["charged"].fillna(0).astype(int)
    area_df["adoption"]  = (area_df["charged"] / area_df["total_conn"] * 100).round(1)
    area_df["uncovered"] = area_df["total_conn"] - area_df["charged"]
    centroids = df_c.groupby("Subarea")[["Latitude","Longitude"]].median().reset_index()
    area_df   = area_df.merge(centroids, on="Subarea", how="left")

    # momentum: absolute conversions in last 30 days per subarea
    df_td = df_m.dropna(subset=["Conversion Date"]).copy()
    now   = df_td["Conversion Date"].max()
    r30   = df_td[df_td["Conversion Date"] >= now - timedelta(days=30)].groupby("Subarea").size()
    mom   = r30.reset_index()
    mom.columns = ["Subarea", "momentum"]
    area_df = area_df.merge(mom, on="Subarea", how="left")
    area_df["momentum"] = area_df["momentum"].fillna(0).astype(int)
    area_df["Priority"] = area_df.apply(
        lambda r: priority_label(r["uncovered"], r["momentum"]), axis=1
    )

    med = dict(lat=df_c["Latitude"].median(), lon=df_c["Longitude"].median())

    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:2rem 0 0.5rem">
        <div style="width:6px;height:6px;border-radius:50%;background:#0071e3"></div>
        <span style="font-size:0.6875rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#6e6e73">Area Intelligence</span>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SIDEBAR CONTROLS
    # ════════════════════════════════════════════════════════
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Analysis Layers")

    map_mode = st.sidebar.selectbox(
        "🗺️ Map Layer",
        ["dots_by_mru","heatmap_connections","heatmap_charged",
         "adoption_bubbles","priority_bubbles","time_animation"],
        format_func=lambda x: {
            "dots_by_mru":         "🟡 Dots — colour by MRU",
            "heatmap_connections": "🔵 Heatmap — all connections",
            "heatmap_charged":     "🟢 Heatmap — charged only",
            "adoption_bubbles":    "🟠 Bubbles — adoption % per subarea",
            "priority_bubbles":    "🎯 Bubbles — effort-impact priority",
            "time_animation":      "⏱️ Animated — adoption spread over time",
        }[x],
    )

    # map style for heatmaps
    if map_mode in ("heatmap_connections", "heatmap_charged"):
        heatmap_tile = st.sidebar.selectbox(
            "🛰️ Heatmap Base Map",
            ["satellite", "road", "terrain", "dark"],
            index=0,
            format_func=lambda x: {
                "satellite": "🛰️ Satellite (Google)",
                "road":      "🗺️ Road (Google)",
                "terrain":   "⛰️ Terrain (Google)",
                "dark":      "🌑 Dark Matter (Carto)",
            }[x],
            key="heatmap_tile"
        )
        HEATMAP_TILE_URLS = {
            "satellite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            "road":      "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            "terrain":   "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        }
        heatmap_mapbox_style = "carto-darkmatter" if heatmap_tile == "dark" else "white-bg"
        heatmap_tile_layer   = [] if heatmap_tile == "dark" else [
            {"sourcetype": "raster", "sourceattribution": "Google",
             "source": [HEATMAP_TILE_URLS[heatmap_tile]], "below": "traces"}
        ]
    else:
        heatmap_mapbox_style = "white-bg"
        heatmap_tile_layer   = []

    # MRU filter for animation
    if map_mode == "time_animation":
        anim_mrus = st.sidebar.multiselect(
            "🏗️ MRUs to animate",
            options=ALL_MRUS, default=ALL_MRUS,
            key="anim_mrus"
        )
    else:
        anim_mrus = ALL_MRUS

    # date slicer
    df_time_all = df_m.dropna(subset=["Conversion Date"])
    min_date = df_time_all["Conversion Date"].min()
    max_date = df_time_all["Conversion Date"].max()
    if pd.notna(min_date) and pd.notna(max_date):
        _date_col = _dc2 if _dc2 is not None else st.sidebar
        date_range = _date_col.date_input(
            "📅 Charged Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(), max_value=max_date.date(),
            key="analysis_date"
        )
        d0, d1 = (date_range[0], date_range[1]) if isinstance(date_range,(list,tuple)) and len(date_range)==2 \
                 else (min_date.date(), max_date.date())
    else:
        d0, d1 = None, None

    df_m_dated = df_m[
        (df_m["Conversion Date"].dt.date >= d0) &
        (df_m["Conversion Date"].dt.date <= d1)
    ] if d0 and d1 else df_m.copy()

    # overlay toggles
    st.sidebar.markdown("**➕ Overlays**")
    show_charged_overlay = st.sidebar.toggle("⚡ Charged dots",  value=False, key="ov_charged")
    show_uncov_overlay   = st.sidebar.toggle("🟥 Uncovered dots", value=False, key="ov_uncov")

    # recompute area with date filter
    chrg_d = df_m_dated.groupby("Subarea").size().reset_index(name="charged_d")
    area_d = conn_by.merge(chrg_d, on="Subarea", how="left")
    area_d["charged_d"]   = area_d["charged_d"].fillna(0).astype(int)
    area_d["adoption_d"]  = (area_d["charged_d"] / area_d["total_conn"] * 100).round(1)
    area_d["uncovered_d"] = area_d["total_conn"] - area_d["charged_d"]
    area_d = area_d.merge(centroids, on="Subarea", how="left")
    area_d = area_d.merge(mom, on="Subarea", how="left")
    area_d["momentum"] = area_d["momentum"].fillna(0).astype(int)
    area_d["Priority"] = area_d.apply(
        lambda r: priority_label(r["uncovered_d"], r["momentum"]), axis=1
    )

    MRU_COLORS = MRU_COLORS_PREMIUM

    # ════════════════════════════════════════════════════════
    # BUILD MAP
    # ════════════════════════════════════════════════════════
    if map_mode == "dots_by_mru":
        afig = px.scatter_mapbox(
            df_c, lat="Latitude", lon="Longitude",
            hover_name="NAME", color="MRU",
            color_discrete_map=MRU_COLORS,
            hover_data={"MRU":True,"Subarea":True,"Latitude":":.6f","Longitude":":.6f"},
            zoom=13, center=med, mapbox_style="white-bg",
            height=700, title="All Connections — by MRU",
        )
        afig.update_traces(marker=dict(size=5, opacity=0.85))
        afig.update_layout(mapbox={
            "style": "white-bg", "zoom": 13, "center": med,
            "layers": [{"sourcetype": "raster", "sourceattribution": "Google",
                "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"],
                "below": "traces"}]
        })

    elif map_mode == "heatmap_connections":
        afig = px.density_mapbox(
            df_c, lat="Latitude", lon="Longitude",
            radius=22, zoom=13, center=med,
            mapbox_style=heatmap_mapbox_style,
            color_continuous_scale=[
                [0.00, "rgba(0,0,0,0)"],
                [0.12, "#050d2e"],
                [0.30, "#0a3a8a"],
                [0.50, "#0057b8"],
                [0.70, "#00aaff"],
                [0.88, "#00e5ff"],
                [1.00, "#ffffff"],
            ],
            opacity=0.65,
            height=700, title="Heatmap — All Connections",
        )
        afig.update_layout(
            mapbox={
                "style": heatmap_mapbox_style, "zoom": 13, "center": med,
                "layers": heatmap_tile_layer
            },
            coloraxis_colorbar=dict(
                title=dict(text="Density", font=dict(color="#8888aa", size=11)),
                tickfont=dict(color="#8888aa", size=10),
                bgcolor="rgba(14,14,26,0.88)",
                bordercolor="rgba(0,212,255,0.25)",
                borderwidth=1, len=0.55, thickness=12, x=0.98,
            )
        )
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:0.45rem 0.85rem;
        background:rgba(14,14,26,0.75);border:1px solid rgba(0,212,255,0.15);
        border-radius:8px;margin-top:0.5rem;font-size:0.72rem;color:#8888aa;font-family:Inter,sans-serif">
        <span style="color:#44445a">Low</span>
        <div style="height:7px;width:140px;border-radius:4px;flex-shrink:0;
        background:linear-gradient(90deg,#050d2e,#0a3a8a,#0057b8,#00aaff,#00e5ff,#fff)"></div>
        <span style="color:#44445a">High</span>
        <span style="margin-left:auto;color:#333354;font-size:0.68rem">Connection density per tile</span>
        </div>""", unsafe_allow_html=True)

    elif map_mode == "heatmap_charged":
        afig = px.density_mapbox(
            df_m_dated, lat="Latitude", lon="Longitude",
            radius=22, zoom=13, center=med,
            mapbox_style=heatmap_mapbox_style,
            color_continuous_scale=[
                [0.00, "rgba(0,0,0,0)"],
                [0.12, "#041a0e"],
                [0.30, "#0a5228"],
                [0.50, "#0a8040"],
                [0.70, "#00b368"],
                [0.88, "#30d158"],
                [1.00, "#aaffcc"],
            ],
            opacity=0.65,
            height=700, title=f"Heatmap — Charged ({d0} → {d1})",
        )
        afig.update_layout(
            mapbox={
                "style": heatmap_mapbox_style, "zoom": 13, "center": med,
                "layers": heatmap_tile_layer
            },
            coloraxis_colorbar=dict(
                title=dict(text="Charged", font=dict(color="#8888aa", size=11)),
                tickfont=dict(color="#8888aa", size=10),
                bgcolor="rgba(14,14,26,0.88)",
                bordercolor="rgba(0,229,160,0.25)",
                borderwidth=1, len=0.55, thickness=12, x=0.98,
            )
        )
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:0.45rem 0.85rem;
        background:rgba(14,14,26,0.75);border:1px solid rgba(0,229,160,0.15);
        border-radius:8px;margin-top:0.5rem;font-size:0.72rem;color:#8888aa;font-family:Inter,sans-serif">
        <span style="color:#44445a">Low</span>
        <div style="height:7px;width:140px;border-radius:4px;flex-shrink:0;
        background:linear-gradient(90deg,#041a0e,#0a5228,#0a8040,#00b368,#30d158,#aaffcc)"></div>
        <span style="color:#44445a">High</span>
        <span style="margin-left:auto;color:#333354;font-size:0.68rem">Charged conversion density</span>
        </div>""", unsafe_allow_html=True)

    elif map_mode == "adoption_bubbles":
        plot_a = area_d.dropna(subset=["Latitude","Longitude"]).copy()
        plot_a["size_val"] = plot_a["adoption_d"].clip(lower=1)
        afig = px.scatter_mapbox(
            plot_a, lat="Latitude", lon="Longitude",
            size="size_val", color="adoption_d",
            hover_name="Subarea",
            hover_data={"MRU":True,"Main_Area":True,"total_conn":True,
                        "charged_d":True,"adoption_d":True,"uncovered_d":True,
                        "Priority":True,"size_val":False},
            color_continuous_scale=[[0,"#ff453a"],[0.5,"#ff9f0a"],[1,"#30d158"]], range_color=[0,100],
            size_max=50, zoom=12, center=med,
            mapbox_style="white-bg", height=700,
            labels={"adoption_d":"Adoption %","charged_d":"Charged","uncovered_d":"Uncovered"},
            title=f"Adoption % by Subarea ({d0} → {d1})",
        )
        afig.update_layout(mapbox={
            "style": "white-bg", "zoom": 12, "center": med,
            "layers": [{"sourcetype": "raster", "sourceattribution": "Google",
                "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"],
                "below": "traces"}]
        })

    elif map_mode == "priority_bubbles":
        plot_b = area_d.dropna(subset=["Latitude","Longitude"]).copy()
        plot_b["size_val"] = plot_b["uncovered_d"].clip(lower=1)
        afig = px.scatter_mapbox(
            plot_b, lat="Latitude", lon="Longitude",
            size="size_val", color="Priority",
            hover_name="Subarea",
            hover_data={"MRU":True,"adoption_d":True,"momentum":True,
                        "total_conn":True,"uncovered_d":True,"size_val":False},
            color_discrete_map=PRIORITY_COLOR_PREMIUM,
            size_max=55, zoom=12, center=med,
            mapbox_style="white-bg", height=700,
            labels={"adoption_d":"Adoption %","momentum":"30d conversions",
                    "uncovered_d":"Uncovered"},
            title="Effort-Impact Priority by Subarea",
        )
        afig.update_layout(mapbox={
            "style": "white-bg", "zoom": 12, "center": med,
            "layers": [{"sourcetype": "raster", "sourceattribution": "Google",
                "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"],
                "below": "traces"}]
        })

    elif map_mode == "time_animation":
        df_anim = df_m.dropna(subset=["Conversion Date"]).copy()
        df_anim = df_anim[df_anim["MRU"].isin(anim_mrus)]
        if df_anim.empty:
            afig = go.Figure()
            st.warning("No data for selected MRUs.")
        else:
            # assign week label (Mon of that week)
            df_anim["week_start"] = df_anim["Conversion Date"].dt.to_period("W").apply(
                lambda r: r.start_time
            )
            df_anim["week_label"] = df_anim["week_start"].dt.strftime("W/E %d %b %Y")
            all_weeks = sorted(df_anim["week_start"].unique())

            # build cumulative frames: each week = all rows up to & including that week
            frames_list = []
            for wk in all_weeks:
                chunk = df_anim[df_anim["week_start"] <= wk].copy()
                chunk["frame_week"] = wk.strftime("W/E %d %b %Y")
                frames_list.append(chunk)
            df_cum = pd.concat(frames_list, ignore_index=True)

            afig = px.scatter_mapbox(
                df_cum,
                lat="Latitude", lon="Longitude",
                hover_name="Customer Name",
                hover_data={"MRU":True,"Subarea":True,"week_label":True,
                            "frame_week":False,"week_start":False},
                color_discrete_sequence=["#00C853"],
                animation_frame="frame_week",
                zoom=12, center=med,
                mapbox_style="open-street-map", height=680,
                title=f"Adoption Spread (Cumulative, Weekly) — {', '.join(anim_mrus)}",
            )
            afig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 600
            afig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
            afig.update_traces(marker=dict(size=5, opacity=0.85))
    else:
        afig = go.Figure()

    # overlays
    if show_charged_overlay and map_mode not in ("heatmap_connections","heatmap_charged","time_animation"):
        ov1 = px.scatter_mapbox(df_m_dated, lat="Latitude", lon="Longitude",
                                hover_name="Customer Name",
                                color_discrete_sequence=["#39FF14"])
        tr = ov1.data[0]
        tr.marker.size=6; tr.marker.opacity=0.9
        tr.name="⚡ Charged"; tr.showlegend=True
        afig.add_trace(tr)

    if show_uncov_overlay and map_mode not in ("heatmap_connections","heatmap_charged","time_animation"):
        charged_meters = set(df_m["Meter Number"].astype(str).str.strip())
        df_uncov = df_c[~df_c["METER NO"].isin(charged_meters)].copy()
        if not df_uncov.empty:
            ov2 = px.scatter_mapbox(df_uncov, lat="Latitude", lon="Longitude",
                                    hover_name="NAME",
                                    hover_data={"MRU":True,"Subarea":True,"METER NO":True},
                                    color_discrete_sequence=["#FF4444"])
            tr2 = ov2.data[0]
            tr2.marker.size=4; tr2.marker.opacity=0.7
            tr2.name="🟥 Uncovered"; tr2.showlegend=True
            afig.add_trace(tr2)

    apply_plotly_theme(afig, height=680)
    afig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="rgba(0,0,0,0.08)", borderwidth=1,
            font=dict(size=11, color="#1d1d1f"), x=0.01, y=0.99
        )
    )
    st.plotly_chart(afig, use_container_width=True, config={"scrollZoom":True})

    # ── INLINE SCORECARD ──
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin:1.5rem 0 0.75rem">
        <div style="width:6px;height:6px;border-radius:50%;background:#0071e3"></div>
        <span style="font-size:0.6875rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#6e6e73">Subarea Scorecard</span>
    </div>
    """, unsafe_allow_html=True)
    sc_cols = st.columns([2,1,1,1,1,1,1,2])
    for h, c in zip(["Subarea","MRU","Total","Charged","Adoption %","Uncovered","30d Conv","Priority"], sc_cols):
        c.markdown(f"<span style='font-size:0.6875rem;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#6e6e73'>{h}</span>", unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:rgba(255,255,255,0.07);margin:4px 0 8px'></div>", unsafe_allow_html=True)

    def _num_badge(val, color="#00d4ff"):
        bg = color.replace(")",",0.13)").replace("rgb","rgba") if color.startswith("rgb") else \
             color + "22" if color.startswith("#") and len(color)==7 else "rgba(0,212,255,0.13)"
        return (f"<span style='background:{bg};color:{color};border:1px solid {color}33;"
                f"border-radius:6px;padding:2px 10px;font-size:0.8rem;font-weight:700;"
                f"font-family:monospace;letter-spacing:0.01em'>{val}</span>")

    for _, row in area_d.sort_values("adoption_d", ascending=False).iterrows():
        cols = st.columns([2,1,1,1,1,1,1,2])
        cols[0].markdown(f"<span style='color:#f0f0ff;font-weight:500'>{row['Subarea']}</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span style='color:#8888aa;font-size:0.8rem'>{row['MRU']}</span>", unsafe_allow_html=True)
        cols[2].markdown(_num_badge(int(row["total_conn"]), "#00d4ff"), unsafe_allow_html=True)
        cols[3].markdown(_num_badge(int(row["charged_d"]), "#30d158"), unsafe_allow_html=True)
        adp = row["adoption_d"]
        color = "#30d158" if adp >= 50 else "#ff9f0a" if adp >= 20 else "#ff453a"
        cols[4].markdown(f"<span style='color:{color};font-weight:700;font-size:0.875rem'>{adp:.1f}%</span>",
                         unsafe_allow_html=True)
        cols[5].markdown(_num_badge(int(row["uncovered_d"]), "#ff9f0a"), unsafe_allow_html=True)
        m = int(row["momentum"])
        mc = "#30d158" if m >= 3 else "#ff453a"
        cols[6].markdown(_num_badge(m, mc), unsafe_allow_html=True)
        pc = PRIORITY_COLOR_PREMIUM.get(row["Priority"], "#aeaeb2")
        cols[7].markdown(f"<span style='background:{pc}22;color:{pc};border:1px solid {pc}44;"
                         f"border-radius:6px;padding:3px 8px;font-size:0.75rem;font-weight:600;"
                         f"letter-spacing:0.01em'>{row['Priority']}</span>",
                         unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # TABS
    # ════════════════════════════════════════════════════════
    st.markdown("<div style='height:1px;background:rgba(0,0,0,0.08);margin:1.5rem 0'></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📈 Trends", "📉 Bass Diffusion", "⏱️ Time-to-50%"])

    # ── TAB 1: TRENDS ──
    with t1:
        # ── Controls row ──
        ctrl_l, ctrl_r = st.columns([1, 1])
        with ctrl_l:
            gran = st.radio("Granularity", ["Daily","Weekly","Monthly"], horizontal=True)
        tcol = {"Daily":"Conversion Date","Weekly":"week","Monthly":"month"}[gran]
        df_td2 = df_td.copy()
        df_td2["week"]  = df_td2["Conversion Date"].dt.to_period("W").apply(lambda r: r.start_time)
        df_td2["month"] = df_td2["Conversion Date"].dt.to_period("M").apply(lambda r: r.start_time)
        with ctrl_r:
            def_s = sorted(df_td2["Subarea"].unique())[:5]
            sel_s = st.multiselect("Subareas", sorted(df_td2["Subarea"].unique()), default=def_s)

        # ── Row 1: Cumulative Charged | Weekly Velocity ──
        ca, cb = st.columns(2)
        with ca:
            daily_a = df_td2[df_td2["Subarea"].isin(sel_s)].groupby([tcol,"Subarea"]).size().reset_index(name="n")
            daily_a = daily_a.sort_values(tcol)
            daily_a["cum"] = daily_a.groupby("Subarea")["n"].cumsum()
            fig_l = px.line(daily_a, x=tcol, y="cum", color="Subarea",
                            labels={tcol:"Date","cum":"Total Charged"})
            apply_plotly_theme(fig_l, title="Cumulative Charged", height=320)
            fig_l.update_layout(
                hovermode="x unified",
                legend=dict(bgcolor="rgba(24,24,48,0.92)", bordercolor="rgba(255,255,255,0.08)",
                            borderwidth=1, font=dict(size=11, color="#8888aa"), x=0.01, y=0.99),
                hoverlabel=dict(bgcolor="#1e1e38", bordercolor="rgba(0,212,255,0.3)",
                                font=dict(family="Inter, sans-serif", size=11, color="#f0f0ff")),
            )
            st.plotly_chart(fig_l, use_container_width=True)
        with cb:
            df_td2b = df_m.dropna(subset=["Conversion Date"]).copy()
            df_td2b["week"] = df_td2b["Conversion Date"].dt.to_period("W").apply(lambda r: r.start_time)
            wm = df_td2b.groupby(["week","MRU"]).size().reset_index(name="count")
            fig_wm = px.density_heatmap(wm, x="week", y="MRU", z="count",
                                         color_continuous_scale=[[0,"#0e0e1a"],[0.5,"#0071e3"],[1,"#00d4ff"]])
            apply_plotly_theme(fig_wm, title="Weekly Velocity per MRU", height=320)
            fig_wm.update_xaxes(tickangle=45)
            st.plotly_chart(fig_wm, use_container_width=True)

        # ── Row 2: Day-of-Week | Month-on-Month ──
        ca2, cb2 = st.columns(2)
        with ca2:
            dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            df_dow = df_m.dropna(subset=["Conversion Date"]).copy()
            df_dow["dow"] = df_dow["Conversion Date"].dt.day_name()
            dow_c = df_dow.groupby("dow").size().reindex(dow_order).reset_index(name="count")
            fig_dow = px.bar(dow_c, x="dow", y="count", color="count",
                             color_continuous_scale=[[0,"#0e0e1a"],[0.5,"#0071e3"],[1,"#00d4ff"]])
            apply_plotly_theme(fig_dow, title="Day-of-Week Conversions", height=320)
            st.plotly_chart(fig_dow, use_container_width=True)
        with cb2:
            df_mon = df_m.dropna(subset=["Conversion Date"]).copy()
            df_mon["month"] = df_mon["Conversion Date"].dt.to_period("M").apply(lambda r: r.start_time)
            monthly = df_mon.groupby("month").size().reset_index(name="count")
            monthly["mom"] = monthly["count"].pct_change() * 100
            fig_mom = px.bar(monthly, x="month", y="mom", color="mom",
                             color_continuous_scale=[[0,"#ff453a"],[0.5,"#ff9f0a"],[1,"#30d158"]])
            fig_mom.add_hline(y=0, line_color="rgba(255,255,255,0.1)", line_width=1)
            apply_plotly_theme(fig_mom, title="Month-on-Month Growth %", height=320)
            st.plotly_chart(fig_mom, use_container_width=True)

    # ── TAB 2: BASS DIFFUSION ──
    with t2:
        st.markdown("""
        <div style='margin-bottom:0.25rem'>
            <span style='font-size:0.875rem;font-weight:600;color:#f0f0ff;letter-spacing:-0.02em'>Bass Diffusion Model</span>
            <span style='font-size:0.75rem;color:#44445a;margin-left:8px'>p (innovation) &middot; q (imitation) per Subarea</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Fits a Bass S-curve to historical conversions. p = self-driven adoption rate, q = word-of-mouth rate. Higher q/p → growth driven by neighbours.")

        bass_sel = st.multiselect(
            "Select subareas to model",
            options=sorted(df_m["Subarea"].dropna().unique()),
            default=sorted(df_m["Subarea"].dropna().unique())[:4]
        )

        bass_results = []
        fig_bass = go.Figure()
        _bass_colors = ["#00d4ff","#e040fb","#00e5a0","#ffb340","#a57fff","#ff4d6a","#00e5cc","#ff8c66"]

        for i, sub in enumerate(bass_sel):
            grp = df_m[df_m["Subarea"] == sub].dropna(subset=["Conversion Date"]).sort_values("Conversion Date")
            total = area_df.loc[area_df["Subarea"]==sub, "total_conn"]
            if total.empty or len(grp) < 6:
                continue
            total = total.values[0]
            result = fit_bass(grp["Conversion Date"], total)
            if result is None:
                continue
            p, q, M, t_obs, cum_obs, fitted, t_fore, forecast, t0 = result
            col = _bass_colors[i % len(_bass_colors)]

            dates_obs  = [t0 + timedelta(days=int(x)) for x in t_obs]
            dates_fore = [t0 + timedelta(days=int(x)) for x in t_fore]

            fig_bass.add_trace(go.Scatter(
                x=dates_obs, y=cum_obs,
                mode="markers", name=f"{sub} (actual)",
                marker=dict(color=col, size=5, opacity=0.5)
            ))
            fig_bass.add_trace(go.Scatter(
                x=dates_obs, y=fitted,
                mode="lines", name=f"{sub} (fit)",
                line=dict(color=col, width=2)
            ))
            fig_bass.add_trace(go.Scatter(
                x=dates_fore, y=forecast,
                mode="lines", name=f"{sub} (forecast)",
                line=dict(color=col, width=1.5, dash="dot")
            ))

            bass_results.append({
                "Subarea": sub,
                "MRU": area_df.loc[area_df["Subarea"]==sub, "MRU"].values[0],
                "Market Size (M)": int(M),
                "p (innovation)": round(p, 5),
                "q (imitation)": round(q, 4),
                "q/p ratio": round(q/p, 2),
                "Driver": "Word-of-mouth 🗣️" if q/p > 3 else "Self-motivated 💡" if q/p < 1.5 else "Mixed ⚖️",
                "Adoption Now %": area_df.loc[area_df["Subarea"]==sub, "adoption"].values[0],
            })

        apply_plotly_theme(fig_bass, title="Bass Diffusion: Actual vs Fitted vs Forecast", height=420)
        fig_bass.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Cumulative Charged")
        st.plotly_chart(fig_bass, use_container_width=True)

        if bass_results:
            br_df = pd.DataFrame(bass_results).sort_values("q/p ratio", ascending=False)
            st.dataframe(
                br_df.style.format({"p (innovation)":"{:.5f}","q (imitation)":"{:.4f}",
                                     "q/p ratio":"{:.2f}","Adoption Now %":"{:.1f}%"}),
                use_container_width=True
            )
            st.markdown(
                "<div style='background:rgba(0,212,255,0.04);border-radius:14px;padding:1rem 1.25rem;"
                "margin-top:0.75rem;border:1px solid rgba(0,212,255,0.14)>"+
                "<p style='font-size:0.625rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#44445a;margin:0 0 8px'>How to read this</p>"
                "<p style='font-size:0.8125rem;color:#8888aa;margin:0;line-height:1.9'>"
                "&bull; <strong style='color:#00d4ff'>High q/p</strong> &mdash; neighbour-driven. Seed one household and the rest follow.<br>"
                "&bull; <strong style='color:#00d4ff'>Low q/p</strong> &mdash; self-driven. Direct outreach needed.<br>"
                "&bull; <strong style='color:#00d4ff'>M</strong> &mdash; addressable connections estimate. Compare with actual total.</p></div>",
                unsafe_allow_html=True
            )
        else:
            st.info("Select subareas with at least 6 data points to fit the Bass model.")

    # ── TAB 3: TIME TO 50% ──
    with t3:
        forecasts = []
        df_t3 = df_m.dropna(subset=["Conversion Date","Subarea"]).sort_values("Conversion Date")
        for sub, grp in df_t3.groupby("Subarea"):
            row = area_df[area_df["Subarea"] == sub]
            if row.empty: continue
            total = row["total_conn"].values[0]
            pct_now = len(grp) / total * 100 if total > 0 else 0
            cutoff  = grp["Conversion Date"].max() - timedelta(days=60)
            recent  = grp[grp["Conversion Date"] >= cutoff]
            days_sp = max((recent["Conversion Date"].max() - recent["Conversion Date"].min()).days, 1)
            rate    = len(recent) / days_sp
            remaining = max(total * 0.5 - len(grp), 0)
            if rate > 0 and pct_now < 50:
                d50 = remaining / rate
                eta_str = (pd.Timestamp.today() + timedelta(days=d50)).strftime("%b %Y")
            elif pct_now >= 50:
                d50 = 0; eta_str = "✅ Done"
            else:
                d50 = np.nan; eta_str = "⚠️ Low data"
            pri_val = area_df.loc[area_df["Subarea"]==sub, "Priority"].values
            forecasts.append({
                "Subarea": sub,
                "MRU": row["MRU"].values[0],
                "Total": total, "Charged": len(grp),
                "Adoption %": round(pct_now,1),
                "Rate/Day": round(rate,2),
                "Days to 50%": round(d50) if not (isinstance(d50,float) and np.isnan(d50)) else "N/A",
                "ETA 50%": eta_str,
                "Priority": pri_val[0] if len(pri_val) else "",
            })

        fc = pd.DataFrame(forecasts).sort_values("Adoption %", ascending=False)
        m2,m3 = st.columns(2)
        m2.metric("🚀 Hit 50% in <90d", f"{len(fc[pd.to_numeric(fc['Days to 50%'],errors='coerce').fillna(999)<=90])} areas")
        m3.metric("🔴 Below 20%",       f"{len(fc[fc['Adoption %']<20])} areas")

        fc_plot = fc[
            pd.to_numeric(fc["Days to 50%"],errors="coerce").notna() &
            (fc["Days to 50%"] != 0) &
            (fc["Adoption %"] < 50)
        ].copy()
        fc_plot["Days to 50%"] = pd.to_numeric(fc_plot["Days to 50%"])
        if not fc_plot.empty:
            fig_eta = px.bar(
                fc_plot.sort_values("Days to 50%"),
                x="Days to 50%", y="Subarea", color="MRU",
                color_discrete_map=MRU_COLORS,
                orientation="h",
            )
            fig_eta.add_vline(x=90, line_dash="dash",
                              line_color="rgba(255,159,10,0.7)", line_width=1.5,
                              annotation_text="90-day target",
                              annotation_font=dict(size=11, color="#ff9f0a"))
            apply_plotly_theme(fig_eta, title="Estimated Days to Reach 50% Adoption", height=560)
            fig_eta.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(24,24,48,0.90)",
                    bordercolor="rgba(255,255,255,0.08)",
                    borderwidth=1,
                    font=dict(size=11, color="#8888aa"),
                ),
                margin=dict(b=80),
            )
            st.plotly_chart(fig_eta, use_container_width=True)
        st.dataframe(fc.style.format({"Adoption %":"{:.1f}%"}), use_container_width=True)
