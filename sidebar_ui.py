"""
sidebar_ui.py
=============
Sidebar rendering for the Sitapur PNG dashboard.
"""

import pandas as pd
import streamlit as st

from premium_theme import render_sidebar_brand


def _section_label(text: str, color: str = "gradient") -> str:
    if color == "gradient":
        style = (
            "background:linear-gradient(90deg,#00d4ff,#7c4dff);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
            "background-clip:text;filter:drop-shadow(0 0 4px rgba(0,212,255,0.35));"
        )
    else:
        style = f"color:{color};"
    return (
        f'<div style="font-size:0.6rem;font-weight:800;letter-spacing:0.18em;'
        f'text-transform:uppercase;{style}'
        f'margin:1.4rem 0 0.35rem;padding-left:2px;display:block">{text}</div>'
    )


def apply_area_filter(df: pd.DataFrame, allowed_areas: set, allowed_mrus: set) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if allowed_mrus is not None:
        out = out[out["MRU"].isin(allowed_mrus)]
    if allowed_areas is not None:
        out = out[out["Main_Area"].isin(allowed_areas)]
    return out.copy()


def render_sidebar(df_conn: pd.DataFrame, df_master: pd.DataFrame) -> dict:
    render_sidebar_brand()
    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    all_mrus = sorted([m for m in df_conn["MRU"].dropna().astype(str).unique().tolist() if m])
    area_by_mru = (
        df_conn[["MRU", "Main_Area"]]
        .dropna()
        .astype(str)
        .apply(lambda s: s.str.strip())
    )
    area_by_mru = area_by_mru[(area_by_mru["MRU"] != "") & (area_by_mru["Main_Area"] != "")]

    st.sidebar.markdown('<div id="sb-section-overview">', unsafe_allow_html=True)
    st.sidebar.markdown(_section_label("📍 Filters"), unsafe_allow_html=True)

    selected_mrus = st.sidebar.multiselect(
        "Select MRU(s)",
        options=all_mrus,
        default=all_mrus,
        key="sb_sel_mrus_new",
    )
    prev_mrus = st.session_state.get("_prev_sb_sel_mrus_new", all_mrus)
    mru_selection_changed = selected_mrus != prev_mrus
    st.session_state["_prev_sb_sel_mrus_new"] = list(selected_mrus)

    if selected_mrus:
        area_options = sorted(
            area_by_mru.loc[area_by_mru["MRU"].isin(selected_mrus), "Main_Area"].unique().tolist()
        )
    else:
        area_options = []

    prev_selected_areas = st.session_state.get("sb_sel_areas_new")
    if mru_selection_changed:
        st.session_state["sb_sel_areas_new"] = area_options
        valid_selected_areas = area_options
    else:
        valid_selected_areas = [a for a in (prev_selected_areas or []) if a in area_options]

    selected_areas = st.sidebar.multiselect(
        "Select Area(s)",
        options=area_options,
        default=valid_selected_areas,
        key="sb_sel_areas_new",
    )

    # ── Charged date range filter (Overview) ──────────────────────────────────
    # Always initialise so the return dict always contains these keys
    charged_date_d0: None = None
    charged_date_d1: None = None
    if not df_master.empty and "Conversion Date" in df_master.columns:
        _cm = df_master.copy()
        _cm["Conversion Date"] = pd.to_datetime(_cm["Conversion Date"], errors="coerce")
        _cmin = _cm["Conversion Date"].min()
        _cmax = _cm["Conversion Date"].max()
        if pd.notna(_cmin) and pd.notna(_cmax):
            _cmin_date = _cmin.date()
            _cmax_date = _cmax.date()
            _stored_c = st.session_state.get("sb_charged_date_range")
            if isinstance(_stored_c, (list, tuple)) and len(_stored_c) == 2:
                if _stored_c[0] < _cmin_date or _stored_c[1] > _cmax_date or _stored_c[0] > _stored_c[1]:
                    st.session_state.pop("sb_charged_date_range", None)
            st.sidebar.markdown(_section_label("⚡ Charged Date Range"), unsafe_allow_html=True)
            _cdr = st.sidebar.date_input(
                "Charged Conversion Range",
                value=(_cmin_date, _cmax_date),
                min_value=_cmin_date,
                max_value=_cmax_date,
                key="sb_charged_date_range",
                label_visibility="collapsed",
            )
            if isinstance(_cdr, (list, tuple)) and len(_cdr) == 2:
                charged_date_d0, charged_date_d1 = _cdr[0], _cdr[1]

    st.sidebar.markdown("---")
    st.sidebar.markdown(_section_label("🎨 Dot Logic", color="#44445a"), unsafe_allow_html=True)
    grey_uncharged = st.sidebar.toggle("Grey Uncharged Areas", value=False, key="sb_grey_uncharged")
    show_charged = st.sidebar.toggle("Show Charged", value=False, key="sb_show_charged")

    st.sidebar.markdown("---")
    st.sidebar.markdown(_section_label("🗺️ Map Style", color="#44445a"), unsafe_allow_html=True)
    map_style: str = st.sidebar.selectbox(
        "🗺️ Map Style",
        ["google-satellite", "google-road", "google-terrain", "carto-darkmatter"],
        index=1,
        label_visibility="collapsed",
        key="sb_map_style",
        format_func=lambda x: {
            "google-satellite": "🛰️ Satellite (Google)",
            "google-road": "🗺️ Road (Google)",
            "google-terrain": "⛰️ Terrain (Google)",
            "carto-darkmatter": "🌑 Dark Matter",
        }[x],
    )

    date_d0 = date_d1 = None
    df_master_f = apply_area_filter(df_master, set(selected_areas), set(selected_mrus))
    if not df_master_f.empty and "Conversion Date" in df_master_f.columns:
        df_master_f["Conversion Date"] = pd.to_datetime(df_master_f["Conversion Date"], errors="coerce")
        _min_d = df_master_f["Conversion Date"].min()
        _max_d = df_master_f["Conversion Date"].max()
        if pd.notna(_min_d) and pd.notna(_max_d):
            _min_date = _min_d.date()
            _max_date = _max_d.date()
            # Clear stale session state if stored range is outside the real data range
            _stored = st.session_state.get("sb_date_range")
            if isinstance(_stored, (list, tuple)) and len(_stored) == 2:
                if _stored[0] < _min_date or _stored[1] > _max_date or _stored[0] > _stored[1]:
                    st.session_state.pop("sb_date_range", None)
            _dr = st.sidebar.date_input(
                "Date Range",
                value=(_min_date, _max_date),
                min_value=_min_date,
                max_value=_max_date,
                key="sb_date_range",
            )
            if isinstance(_dr, (list, tuple)) and len(_dr) == 2:
                date_d0, date_d1 = _dr[0], _dr[1]
                df_master_f = df_master_f[
                    (df_master_f["Conversion Date"].dt.date >= date_d0) &
                    (df_master_f["Conversion Date"].dt.date <= date_d1)
                ].copy()

    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div id="sb-section-map">', unsafe_allow_html=True)
    st.sidebar.markdown(_section_label("📊 Analysis Layers"), unsafe_allow_html=True)
    map_mode: str = st.sidebar.selectbox(
        "Map Layer",
        ["heatmap_connections", "heatmap_charged", "adoption_bubbles", "priority_bubbles", "time_animation"],
        label_visibility="collapsed",
        key="sb_map_mode",
        format_func=lambda x: {
            "heatmap_connections": "🔵 All Connections",
            "heatmap_charged": "🟢 Charged Only",
            "adoption_bubbles": "🟠 Adoption Bubbles",
            "priority_bubbles": "🎯 Priority Bubbles",
            "time_animation": "⏱️ Animated Spread",
        }[x],
    )

    heatmap_tile = st.sidebar.selectbox(
        "Base Map",
        ["road", "satellite", "terrain", "dark"],
        label_visibility="collapsed",
        key="sb_heatmap_tile",
        format_func=lambda x: {
            "satellite": "🛰️ Satellite",
            "road": "🗺️ Road",
            "terrain": "⛰️ Terrain",
            "dark": "🌑 Dark",
        }[x],
    )

    anim_mrus = selected_mrus if selected_mrus else all_mrus
    show_charged_overlay = show_charged
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    return {
        "filter_mode": "All",
        "allowed_mrus": set(selected_mrus),
        "allowed_areas": set(selected_areas),
        "grey_uncharged": grey_uncharged,
        "show_charged": show_charged,
        "map_style": map_style,
        "date_d0": date_d0,
        "date_d1": date_d1,
        "charged_date_d0": charged_date_d0,
        "charged_date_d1": charged_date_d1,
        "df_master_f": df_master_f,
        "map_mode": map_mode,
        "heatmap_tile": heatmap_tile,
        "anim_mrus": anim_mrus,
        "show_charged_overlay": show_charged_overlay,
    }
