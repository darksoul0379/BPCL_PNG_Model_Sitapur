"""
bot_tab.py
==========
PNG Assistant bot tab for the Sitapur PNG dashboard.

This module contains all UI and logic for the "🤖 PNG Assistant" tab.
It provides four interactive modes accessible via menu buttons:

  Summary Mode   — MRU / area / subarea slicers with KPI cards,
                   MRU-level tables, per-MRU subarea breakdowns, and charts.

  Data Mode      — Territory + date filter, monthly conversion chart,
                   breakdown table, searchable charged connections list,
                   and CSV download.

  Analysis Mode  — Subarea connection ranking (top/bottom) + scatter view,
                   OR Bass Diffusion model fitting with rankings and legend.

  Search Mode    — Real-time full-text search across all connection records.

Public function
---------------
render_bot_tab(df_conn, df_master)
    Render the entire bot tab. Call inside `with bot_tab:` in main.py.
    Manages its own mode via st.session_state["bot_mode"].

Internal helpers are prefixed with _ and are not intended for external use.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import timedelta
from scipy.optimize import curve_fit



# ── Bubble HTML helpers ──────────────────────────────────────────────────────────

def _bot_bubble(text: str) -> None:
    """Render a styled bot speech bubble using the .bot-bubble CSS class."""
    st.markdown(
        f'<div class="bot-bubble">🤖&nbsp;&nbsp;{text}</div>',
        unsafe_allow_html=True,
    )


def _user_bubble(text: str) -> None:
    """Render a styled user speech bubble using the .user-bubble CSS class."""
    st.markdown(
        f'<div class="user-bubble">{text}&nbsp;&nbsp;👤</div>',
        unsafe_allow_html=True,
    )


def _section_header(text: str) -> None:
    """Render a cyan uppercase section header using the .bot-section-header CSS class."""
    st.markdown(
        f'<div class="bot-section-header">{text}</div>',
        unsafe_allow_html=True,
    )


def _dark_layout(fig):
    """
    Apply a minimal transparent dark background to a Plotly figure in-place.

    Used for bot-tab charts to avoid importing apply_plotly_theme() here.
    Returns the modified figure for chaining.
    """
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8",
    )
    return fig


# ── Data helpers ─────────────────────────────────────────────────────────────────



def _derive_geo_lists(df_conn: pd.DataFrame):
    pairs = (
        df_conn[["MRU", "Main_Area", "Subarea"]]
        .dropna()
        .astype(str)
        .apply(lambda s: s.str.strip())
    )
    pairs = pairs[(pairs["MRU"] != "") & (pairs["Main_Area"] != "") & (pairs["Subarea"] != "")]
    all_mrus = sorted(pairs["MRU"].unique().tolist())
    mru_to_areas = {
        mru: sorted(pairs.loc[pairs["MRU"] == mru, "Main_Area"].unique().tolist())
        for mru in all_mrus
    }
    area_to_subareas = {
        area: sorted(pairs.loc[pairs["Main_Area"] == area, "Subarea"].unique().tolist())
        for area in sorted(pairs["Main_Area"].unique().tolist())
    }
    subarea_to_mru = (
        pairs.drop_duplicates(subset=["Subarea"]).set_index("Subarea")["MRU"].to_dict()
    )
    return all_mrus, mru_to_areas, area_to_subareas, subarea_to_mru

def _conv_rate(n_conv: int, n_conn: int) -> float:
    """
    Return conversion rate as a float percentage (0.0–100.0).
    Returns 0.0 safely when n_conn is zero.
    """
    return round(n_conv / n_conn * 100, 2) if n_conn else 0.0


def _bot_summary_table(
    fc: pd.DataFrame,
    fv: pd.DataFrame,
    grp: str = "Subarea",
) -> pd.DataFrame:
    """
    Build a grouped summary DataFrame aggregating connection and conversion counts.

    Parameters
    ----------
    fc  : Filtered connections DataFrame.
    fv  : Filtered conversions DataFrame.
    grp : Column to group by — "MRU" or "Subarea".

    Returns
    -------
    DataFrame with columns: <grp>, Total_Connections, Charged, Conv_%,
    and optionally Total_GI, Inlet_GI, Outlet_GI when the GI columns exist.
    Sorted by Total_Connections descending.
    """
    gi_col  = "TOTAL GI"        if "TOTAL GI"        in fc.columns else None
    in_col  = "METER INLET GI"  if "METER INLET GI"  in fc.columns else None
    out_col = "METER OUTLET GI" if "METER OUTLET GI" in fc.columns else None

    agg_dict: dict = {"METER NO": "count"}
    rename:   dict = {"METER NO": "Total_Connections"}
    if gi_col:  agg_dict[gi_col]  = "sum"; rename[gi_col]  = "Total_GI"
    if in_col:  agg_dict[in_col]  = "sum"; rename[in_col]  = "Inlet_GI"
    if out_col: agg_dict[out_col] = "sum"; rename[out_col] = "Outlet_GI"

    gc = fc.groupby(grp).agg(agg_dict).reset_index().rename(columns=rename)

    id_col = "Meter Number" if "Meter Number" in fv.columns else (
        fv.columns[0] if not fv.empty else None
    )
    if id_col and not fv.empty:
        gv = fv.groupby(grp).agg(Charged=(id_col, "count")).reset_index()
    else:
        gv = pd.DataFrame(columns=[grp, "Charged"])

    m = gc.merge(gv, on=grp, how="left")
    m["Charged"] = m["Charged"].fillna(0).astype(int)
    m["Conv_%"]  = m.apply(lambda r: _conv_rate(r["Charged"], r["Total_Connections"]), axis=1)

    for c in ["Total_GI", "Inlet_GI", "Outlet_GI"]:
        if c in m.columns:
            m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0).round(2)

    return m.sort_values("Total_Connections", ascending=False).reset_index(drop=True)


def _bot_apply_filters(
    df_conn: pd.DataFrame,
    df_master: pd.DataFrame,
    bot_mrus: list,
    bot_subs: list,
) -> tuple:
    """
    Filter connections and conversions DataFrames to the selected MRUs / subareas.

    Excludes "Unassigned" rows from both frames before applying the filter.
    bot_subs is optional — pass an empty list [] to skip subarea filtering.

    Returns
    -------
    (fc, fv) — filtered copies of df_conn and df_master.
    """
    fc = df_conn[df_conn["MRU"] != "Unassigned"].copy()
    fv = (
        df_master[df_master["MRU"] != "Unassigned"].copy()
        if not df_master.empty
        else pd.DataFrame()
    )
    if bot_mrus:
        fc = fc[fc["MRU"].isin(bot_mrus)]
        if not fv.empty:
            fv = fv[fv["MRU"].isin(bot_mrus)]
    if bot_subs:
        fc = fc[fc["Subarea"].isin(bot_subs)]
        if not fv.empty:
            fv = fv[fv["Subarea"].isin(bot_subs)]
    return fc, fv


def _bot_kpi_row(fc: pd.DataFrame, fv: pd.DataFrame) -> None:
    """
    Render a row of 5 KPI cards (Connections, Charged, Conv. Rate, Inlet GI, Outlet GI).
    Uses the .bot-kpi-card CSS class defined in main.py's global styles.
    """
    total   = len(fc)
    charged = len(fv)
    rate    = f"{charged/total*100:.1f}%" if total else "—"
    inlet   = (
        fc["METER INLET GI"].apply(pd.to_numeric, errors="coerce").sum()
        if "METER INLET GI" in fc.columns else 0
    )
    outlet  = (
        fc["METER OUTLET GI"].apply(pd.to_numeric, errors="coerce").sum()
        if "METER OUTLET GI" in fc.columns else 0
    )
    cols = st.columns(5)
    for col, (icon, label, val) in zip(cols, [
        ("🏠", "Connections", f"{total:,}"),
        ("⚡", "Charged",     f"{charged:,}"),
        ("📈", "Conv. Rate",  rate),
        ("🔵", "Inlet GI",    f"{inlet:,.1f}"),
        ("🟢", "Outlet GI",   f"{outlet:,.1f}"),
    ]):
        col.markdown(
            f'<div class="bot-kpi-card">'
            f'<div style="font-size:1.3rem">{icon}</div>'
            f'<div class="bot-kpi-value">{val}</div>'
            f'<div class="bot-kpi-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Bass diffusion helpers ────────────────────────────────────────────────────────

def _bass_cumulative(t, M, p, q):
    """
    Bass cumulative adoption curve.
    N(t) = M * (1 - e^(-(p+q)*t)) / (1 + (q/p) * e^(-(p+q)*t))
    """
    exp = np.exp(-(p + q) * t)
    return M * (1 - exp) / (1 + (q / p) * exp)


def _fit_bass_bot(dates_sorted: pd.Series, total_market: int):
    """
    Fit the Bass diffusion model to a sorted Conversion Date series.

    Parameters
    ----------
    dates_sorted  : pd.Series of datetime values, pre-sorted ascending.
    total_market  : Total number of connections in the subarea (market ceiling).

    Returns
    -------
    (p, q, M) floats on success, or None if fewer than 6 data points or
    scipy.optimize.curve_fit fails to converge.
    """
    if len(dates_sorted) < 6:
        return None
    t0  = dates_sorted.min()
    t   = (dates_sorted - t0).dt.days.values.astype(float)
    cum = np.arange(1, len(t) + 1, dtype=float)
    try:
        p0     = [total_market, 0.01, 0.3]
        bounds = ([total_market * 0.5, 1e-5, 1e-5], [total_market * 3, 1.0, 2.0])
        popt, _ = curve_fit(_bass_cumulative, t, cum, p0=p0, bounds=bounds, maxfev=8000)
        M, p, q = popt
        return p, q, M
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════════

def render_bot_tab(df_conn: pd.DataFrame, df_master: pd.DataFrame) -> None:
    """
    Render the full PNG Assistant bot tab.

    Parameters
    ----------
    df_conn   : Full (unfiltered) connections DataFrame from load_connection_data().
    df_master : Full (unfiltered) conversions DataFrame from load_master_data().

    The tab manages its own display mode via st.session_state["bot_mode"]:
      "menu"    → welcome screen with 4 mode buttons
      "summary" → summary mode
      "charged" → data mode
      "ranking" → analysis mode
      "search"  → search mode
    """
    # ── Session state defaults ────────────────────────────────────────────────────
    if "bot_mode" not in st.session_state:
        st.session_state.bot_mode = "menu"
    if "bot_chat" not in st.session_state:
        st.session_state.bot_chat = []

    # ── Render chat history ───────────────────────────────────────────────────────
    for msg in st.session_state.bot_chat:
        if msg["role"] == "bot":
            _bot_bubble(msg["text"])
        else:
            _user_bubble(msg["text"])

    # ── Dispatch to the appropriate mode renderer ─────────────────────────────────
    mode = st.session_state.bot_mode
    if mode == "menu":
        _render_menu()
    elif mode == "summary":
        _render_summary(df_conn, df_master)
    elif mode == "charged":
        _render_charged(df_conn, df_master)
    elif mode == "ranking":
        _render_ranking(df_conn, df_master)
    elif mode == "search":
        _render_search(df_conn, df_master)


# ── Sub-renderers ─────────────────────────────────────────────────────────────────

def _render_menu() -> None:
    """Render the welcome menu with 4 mode-selection buttons."""
    _bot_bubble(
        "👋 Hello! I'm your <b>PNG Field Assistant</b>.<br>"
        "Choose a task from the menu and let me do it."
    )
    st.markdown("<br>", unsafe_allow_html=True)
    mc1, mc2, mc3, mc4 = st.columns(4)
    for col, label, mode in [
        (mc1, "📊 Summary Mode",  "summary"),
        (mc2, "📋 Data Mode",     "charged"),
        (mc3, "📈 Analysis Mode", "ranking"),
        (mc4, "🔍 Search Mode",   "search"),
    ]:
        with col:
            if st.button(label, key=f"bot_menu_{mode}", use_container_width=True):
                st.session_state.bot_chat.append({"role": "user", "text": label})
                st.session_state.bot_mode = mode
                st.rerun()
    st.markdown('<p class="menu-hint">👆 Tap a button to begin.</p>', unsafe_allow_html=True)


def _render_summary(df_conn: pd.DataFrame, df_master: pd.DataFrame) -> None:
    """Summary Mode: MRU + area + subarea slicers → KPI cards + tables + charts."""
    _bot_bubble("📊 <b>Summary Mode</b> — use the filters below to narrow your scope.")
    _section_header("📍 Scope")

    sf1, sf2, sf3 = st.columns(3)
    all_mrus, mru_to_areas, area_to_subareas, subarea_to_mru = _derive_geo_lists(df_conn)
    sum_mrus  = sf1.multiselect("MRU", options=all_mrus, default=all_mrus, key="sum_mru") or all_mrus
    avail_a   = sorted({area for mru in sum_mrus for area in mru_to_areas.get(mru, [])})
    sum_areas = sf2.multiselect("Main Area", options=avail_a,                            default=avail_a,         key="sum_area") or avail_a
    avail_s   = sorted({sub for area in sum_areas for sub in area_to_subareas.get(area, [])})
    sum_subs  = sf3.multiselect("Subarea",   options=avail_s,                            default=avail_s,         key="sum_sub")  or avail_s

    sum_fc, sum_fv = _bot_apply_filters(df_conn, df_master, sum_mrus, sum_subs)

    st.markdown("<br>", unsafe_allow_html=True)
    _bot_kpi_row(sum_fc, sum_fv)
    st.markdown("<br>", unsafe_allow_html=True)

    # MRU-level summary table with a total row
    _section_header("By MRU")
    mru_sum = _bot_summary_table(sum_fc, sum_fv, grp="MRU")
    tot_row: dict = {"MRU": "TOTAL"}
    for col in ["Total_Connections", "Charged", "Total_GI", "Inlet_GI", "Outlet_GI"]:
        if col in mru_sum.columns:
            tot_row[col] = mru_sum[col].sum()
    tot_row["Conv_%"] = _conv_rate(tot_row.get("Charged", 0), tot_row.get("Total_Connections", 0))
    disp_mru = pd.concat([mru_sum, pd.DataFrame([tot_row])], ignore_index=True)

    fmt: dict = {"Conv_%": "{:.2f}%"}
    for c in ["Total_GI", "Inlet_GI", "Outlet_GI"]:
        if c in disp_mru.columns:
            fmt[c] = "{:,.2f}"

    st.dataframe(
        disp_mru.style.format(fmt).apply(
            lambda r: [
                "background-color:rgba(0,212,255,0.08);font-weight:bold"
                if r.name == len(disp_mru) - 1 else ""
                for _ in r
            ], axis=1,
        ),
        use_container_width=True, hide_index=True,
    )

    fig_mru = px.bar(
        mru_sum, x="MRU", y=["Total_Connections", "Charged"],
        barmode="group", title="Connections vs Charged by MRU",
        color_discrete_sequence=["#00d4ff", "#7c4dff"],
        labels={"value": "Count", "variable": "Type"},
    )
    st.plotly_chart(_dark_layout(fig_mru), use_container_width=True)

    # Per-MRU subarea breakdown
    for mru in sorted(sum_mrus):
        fc_m = sum_fc[sum_fc["MRU"] == mru]
        fv_m = sum_fv[sum_fv["MRU"] == mru] if not sum_fv.empty else pd.DataFrame()
        if fc_m.empty:
            continue
        _section_header(f"🏙️ {mru} — Subarea Breakdown")
        sub_s = _bot_summary_table(fc_m, fv_m, grp="Subarea")
        tot2: dict = {"Subarea": f"{mru} TOTAL"}
        for col in ["Total_Connections", "Charged", "Total_GI", "Inlet_GI", "Outlet_GI"]:
            if col in sub_s.columns:
                tot2[col] = sub_s[col].sum()
        tot2["Conv_%"] = _conv_rate(tot2.get("Charged", 0), tot2.get("Total_Connections", 0))
        disp2 = pd.concat([sub_s, pd.DataFrame([tot2])], ignore_index=True)
        st.dataframe(
            disp2.style.format(fmt).apply(
                lambda r: [
                    "background-color:rgba(0,212,255,0.08);font-weight:bold"
                    if r.name == len(disp2) - 1 else ""
                    for _ in r
                ], axis=1,
            ),
            use_container_width=True, hide_index=True,
        )
        sc1, sc2 = st.columns(2)
        with sc1:
            fig_pie = px.pie(
                sub_s, names="Subarea", values="Total_Connections",
                title=f"{mru} — Share of Connections", hole=0.4,
            )
            fig_pie.update_traces(textposition="inside", textinfo="label+percent")
            fig_pie.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                                  paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8")
            st.plotly_chart(fig_pie, use_container_width=True)
        with sc2:
            fig_cr = px.bar(
                sub_s.sort_values("Conv_%", ascending=False),
                x="Subarea", y="Conv_%", title=f"{mru} — Conversion Rate %",
                color="Conv_%", color_continuous_scale="RdYlGn",
            )
            fig_cr.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  font_color="#94a3b8", xaxis_tickangle=-35)
            st.plotly_chart(fig_cr, use_container_width=True)

    if st.button("🏠 Back to Menu", key="bot_back_summary"):
        st.session_state.bot_mode = "menu"
        st.session_state.bot_chat = []
        st.rerun()


def _render_charged(df_conn: pd.DataFrame, df_master: pd.DataFrame) -> None:
    """Data Mode: territory + date filter → monthly chart + breakdown + searchable list."""
    _bot_bubble("📋 <b>Data Mode</b> — filter by territory and date to explore charged connections.")
    _section_header("📍 Scope")

    cf1, cf2, cf3 = st.columns(3)
    all_mrus, mru_to_areas, area_to_subareas, subarea_to_mru = _derive_geo_lists(df_conn)
    ch_mrus   = cf1.multiselect("MRU", options=all_mrus, default=all_mrus, key="ch_mru") or all_mrus
    avail_a   = sorted({area for mru in ch_mrus for area in mru_to_areas.get(mru, [])})
    ch_areas  = cf2.multiselect("Main Area", options=avail_a,                                 default=avail_a,   key="ch_area") or avail_a
    avail_s   = sorted({sub for area in ch_areas for sub in area_to_subareas.get(area, [])})
    ch_subs   = cf3.multiselect("Subarea",   options=avail_s,                                 default=avail_s,   key="ch_sub")  or avail_s

    _, ch_fv = _bot_apply_filters(df_conn, df_master, ch_mrus, ch_subs)

    if ch_fv.empty:
        _bot_bubble("⚠️ No charged connections found for the selected scope.")
    else:
        min_d = ch_fv["Conversion Date"].min()
        max_d = ch_fv["Conversion Date"].max()
        _section_header("📅 Date Range")
        dc1, dc2 = st.columns(2)
        d_from = dc1.date_input("From", value=min_d, key="bot_date_from")
        d_to   = dc2.date_input("To",   value=max_d, key="bot_date_to")

        fv_d = ch_fv[
            (ch_fv["Conversion Date"] >= pd.Timestamp(d_from)) &
            (ch_fv["Conversion Date"] <= pd.Timestamp(d_to))
        ]
        _bot_bubble(f"Found <b>{len(fv_d):,}</b> charged connections in this range.")

        # Monthly conversion bar chart
        tl = fv_d.groupby(fv_d["Conversion Date"].dt.to_period("M")).size().reset_index()
        tl.columns = ["Month", "Count"]
        tl["Month"] = tl["Month"].astype(str)
        fig_tl = px.bar(tl, x="Month", y="Count", title="Conversions per Month",
                        color_discrete_sequence=["#00d4ff"])
        st.plotly_chart(_dark_layout(fig_tl), use_container_width=True)

        # Breakdown by MRU & Subarea
        _section_header("📍 Breakdown by MRU & Subarea")
        id_col = "Meter Number" if "Meter Number" in fv_d.columns else fv_d.columns[0]
        bd = (
            fv_d.groupby(["MRU", "Subarea"])
            .agg(Charged=(id_col, "count"))
            .reset_index()
            .sort_values("Charged", ascending=False)
        )
        st.dataframe(bd, use_container_width=True, hide_index=True)

        # Searchable charged list with download
        _section_header("🔎 Search Charged List")
        srch = st.text_input("Search name / meter / mobile", "", key="bot_charged_search")
        show = fv_d[["Meter Number", "Customer Name", "Mobile NUMBER",
                     "Conversion Date", "MRU", "Subarea"]].copy()
        show["Conversion Date"] = show["Conversion Date"].dt.strftime("%Y-%m-%d")
        if srch:
            mask = (
                show["Customer Name"].str.contains(srch, case=False, na=False) |
                show["Meter Number"].str.contains(srch, case=False, na=False) |
                show["Mobile NUMBER"].str.contains(srch, case=False, na=False)
            )
            show = show[mask]
        st.dataframe(
            show.rename(columns={
                "Meter Number": "Meter No", "Customer Name": "Name",
                "Mobile NUMBER": "Mobile", "Conversion Date": "Date",
            }),
            use_container_width=True, hide_index=True,
        )
        st.download_button(
            "⬇️ Download CSV", show.to_csv(index=False),
            file_name="charged_connections.csv", mime="text/csv",
            key="bot_dl_charged",
        )

    if st.button("🏠 Back to Menu", key="bot_back_charged"):
        st.session_state.bot_mode = "menu"
        st.session_state.bot_chat = []
        st.rerun()


def _render_ranking(df_conn: pd.DataFrame, df_master: pd.DataFrame) -> None:
    """Analysis Mode: connection ranking OR Bass Diffusion model per subarea."""
    _bot_bubble(
        "📈 <b>Analysis Mode</b> — select MRUs, then rank by connection metrics "
        "or Bass diffusion parameters."
    )

    _section_header("📍 Select MRUs")
    all_mrus, mru_to_areas, area_to_subareas, subarea_to_mru = _derive_geo_lists(df_conn)
    rk_mrus = st.multiselect(
        "MRU", options=all_mrus, default=all_mrus,
        key="rk_mru", label_visibility="collapsed",
    ) or all_mrus
    rk_fc, rk_fv = _bot_apply_filters(df_conn, df_master, rk_mrus, [])

    _section_header("🔬 Analysis View")
    view_mode = st.radio(
        "View", ["📊 Connection Ranking", "🎵 Bass Diffusion"],
        horizontal=True, key="bot_analysis_view",
    )

    # ── Connection Ranking ────────────────────────────────────────────────────────
    if view_mode == "📊 Connection Ranking":
        _section_header("⚙️ Ranking Options")
        rk1, rk2, rk3, rk4 = st.columns(4)
        direction = rk1.radio("Direction", ["Top", "Bottom"], horizontal=True, key="bot_rank_dir")
        n         = rk2.slider("How many?", 1, 20, 5, key="bot_rank_n")
        hide_uncharged = rk4.toggle("Hide uncharged areas", value=True, key="bot_rank_hide_uncharged")

        sub_sum = _bot_summary_table(rk_fc, rk_fv, grp="Subarea")
        sub_sum["MRU"] = sub_sum["Subarea"].map(subarea_to_mru)
        if hide_uncharged and "Charged" in sub_sum.columns:
            sub_sum = sub_sum[sub_sum["Charged"].fillna(0) > 0].copy()

        available_metrics = [c for c in ["Total_Connections", "Charged", "Conv_%", "Total_GI"]
                             if c in sub_sum.columns]
        metric  = rk3.selectbox("Rank by", available_metrics, key="bot_rank_metric")
        asc     = direction == "Bottom"
        ranked  = sub_sum.sort_values(metric, ascending=asc).head(n)

        fig_rank = px.bar(
            ranked, x=metric, y="Subarea", orientation="h",
            color=metric, color_continuous_scale="Blues" if direction == "Top" else "Reds",
            title=f"{direction} {n} Subareas — {metric.replace('_', ' ')}",
            text=metric,
            hover_data={k: True for k in ["MRU", "Total_Connections", "Charged", "Conv_%"]
                        if k in ranked.columns},
        )
        fig_rank.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_rank.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8",
            yaxis={"categoryorder": "total ascending" if direction == "Top" else "total descending"},
            coloraxis_showscale=False,
            height=max(400, n * 45),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        display_cols = [c for c in ["MRU", "Subarea", "Total_Connections", "Charged", "Conv_%", "Total_GI"]
                        if c in ranked.columns]
        st.dataframe(ranked[display_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

        # Scatter: all subareas, highlighted ranked ones
        _section_header("📡 All Subareas — Scatter View")
        all_sub = _bot_summary_table(rk_fc, rk_fv, grp="Subarea")
        all_sub["MRU"]   = all_sub["Subarea"].map(mru_to_areas)
        hl               = set(ranked["Subarea"].tolist())
        all_sub["Label"] = all_sub["Subarea"].apply(lambda s: f"★ {s}" if s in hl else s)
        scatter_y        = "Conv_%" if "Conv_%" in all_sub.columns else "Charged"
        scatter_size     = "Total_GI" if "Total_GI" in all_sub.columns else "Total_Connections"
        fig_sc = px.scatter(
            all_sub, x="Total_Connections", y=scatter_y,
            size=scatter_size, color="MRU",
            hover_name="Subarea", text="Label",
            title="Connections vs Conversion Rate (size = GI)",
        )
        fig_sc.update_traces(textposition="top center")
        st.plotly_chart(_dark_layout(fig_sc), use_container_width=True)

    # ── Bass Diffusion ────────────────────────────────────────────────────────────
    else:
        _section_header("⚙️ Bass Ranking Options")

        rk_conn_grp = rk_fc.groupby(["MRU", "Subarea"]).size().reset_index(name="total_conn")
        rk_chrg_grp = (
            rk_fv.groupby("Subarea").size().reset_index(name="charged")
            if not rk_fv.empty
            else pd.DataFrame(columns=["Subarea", "charged"])
        )
        rk_area = rk_conn_grp.merge(rk_chrg_grp, on="Subarea", how="left")
        rk_area["charged"]  = rk_area["charged"].fillna(0).astype(int)
        rk_area["adoption"] = (rk_area["charged"] / rk_area["total_conn"] * 100).round(1)

        bass_rows   = []
        rk_fv_dated = rk_fv.dropna(subset=["Conversion Date"]).copy() if not rk_fv.empty else pd.DataFrame()

        if not rk_fv_dated.empty:
            for sub in rk_area["Subarea"].unique():
                grp = rk_fv_dated[rk_fv_dated["Subarea"] == sub].sort_values("Conversion Date")
                row = rk_area[rk_area["Subarea"] == sub]
                if row.empty or len(grp) < 6:
                    continue
                total = row["total_conn"].values[0]
                res   = _fit_bass_bot(grp["Conversion Date"], total)
                if res is None:
                    continue
                p, q, M = res
                bass_rows.append({
                    "Subarea":         sub,
                    "MRU":             row["MRU"].values[0],
                    "Market Size (M)": int(M),
                    "p (innovation)":  round(p, 5),
                    "q (imitation)":   round(q, 4),
                    "q/p ratio":       round(q / p, 2),
                    "Driver":          (
                        "Word-of-mouth 🗣️" if q / p > 3
                        else "Self-motivated 💡" if q / p < 1.5
                        else "Mixed ⚖️"
                    ),
                    "Adoption Now %":  row["adoption"].values[0],
                    "Total Conn":      total,
                    "Charged":         row["charged"].values[0],
                })

        if not bass_rows:
            _bot_bubble(
                "⚠️ Not enough data to fit the Bass model. "
                "Each subarea needs at least 6 charged conversions."
            )
        else:
            bass_df = pd.DataFrame(bass_rows)
            bd1, bd2, bd3 = st.columns(3)
            bass_dir    = bd1.radio("Direction", ["Top", "Bottom"], horizontal=True, key="bot_bass_dir")
            bass_n      = bd2.slider("How many?", 1, len(bass_df), min(5, len(bass_df)), key="bot_bass_n")
            bass_metric = bd3.selectbox(
                "Rank by",
                ["q/p ratio", "p (innovation)", "q (imitation)", "Adoption Now %", "Market Size (M)"],
                key="bot_bass_metric",
            )
            bass_ranked = bass_df.sort_values(bass_metric, ascending=(bass_dir == "Bottom")).head(bass_n)

            fig_bass = px.bar(
                bass_ranked, x=bass_metric, y="Subarea", orientation="h",
                color=bass_metric,
                color_continuous_scale="Blues" if bass_dir == "Top" else "Reds",
                title=f"{bass_dir} {bass_n} Subareas by {bass_metric}",
                text=bass_metric,
                hover_data={k: True for k in ["MRU", "Driver", "Adoption Now %", "q/p ratio"]
                            if k in bass_ranked.columns},
            )
            fig_bass.update_traces(texttemplate="%{text:.3f}", textposition="outside")
            fig_bass.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8",
                yaxis={"categoryorder": "total ascending" if bass_dir == "Top" else "total descending"},
                coloraxis_showscale=False,
                height=max(400, bass_n * 45),
            )
            st.plotly_chart(fig_bass, use_container_width=True)

            _section_header("📋 Full Bass Results — All Subareas in Scope")
            st.dataframe(
                bass_df.sort_values("q/p ratio", ascending=False).style.format({
                    "p (innovation)": "{:.5f}",
                    "q (imitation)":  "{:.4f}",
                    "q/p ratio":      "{:.2f}",
                    "Adoption Now %": "{:.1f}%",
                }),
                use_container_width=True, hide_index=True,
            )
            st.markdown(
                "<div style='background:rgba(0,212,255,0.04);border-radius:14px;"
                "padding:1rem 1.25rem;margin-top:0.75rem;"
                "border:1px solid rgba(0,212,255,0.14)'>"
                "<p style='font-size:0.625rem;font-weight:700;letter-spacing:0.12em;"
                "text-transform:uppercase;color:#44445a;margin:0 0 8px'>How to read this</p>"
                "<p style='font-size:0.8125rem;color:#8888aa;margin:0;line-height:1.9'>"
                "&#8226; <strong style='color:#00d4ff'>High q/p</strong> — "
                "neighbour-driven. Seed one household and the rest follow.<br>"
                "&#8226; <strong style='color:#00d4ff'>Low q/p</strong> — "
                "self-driven. Direct outreach needed.<br>"
                "&#8226; <strong style='color:#00d4ff'>M</strong> — "
                "addressable connections estimate. Compare with actual total.</p></div>",
                unsafe_allow_html=True,
            )

    if st.button("🏠 Back to Menu", key="bot_back_rank"):
        st.session_state.bot_mode = "menu"
        st.session_state.bot_chat = []
        st.rerun()


def _render_search(df_conn: pd.DataFrame, df_master: pd.DataFrame) -> None:
    """Search Mode: real-time full-text search across all connection records."""
    _bot_bubble("🔍 <b>Search Mode</b> — enter a name, meter number, or mobile to search all connections.")

    query = st.text_input(
        "🔎 Search query", "",
        placeholder="e.g. Ramesh / RR2401 / 9876543210",
        key="bot_search_query",
    )
    if query:
        # Build set of charged meter numbers for the "Charged?" indicator column
        charged_meters = (
            set(df_master["Meter Number"].str.strip().str.lower())
            if not df_master.empty and "Meter Number" in df_master.columns
            else set()
        )
        mask = (
            df_conn["NAME"].str.contains(query, case=False, na=False) |
            df_conn["METER NO"].str.contains(query, case=False, na=False) |
            df_conn["MOB NO"].str.contains(query, case=False, na=False)
        )
        results = df_conn[mask].copy()
        results["Charged?"] = results["METER NO"].apply(
            lambda m: "✅ Yes" if str(m).strip().lower() in charged_meters else "❌ No"
        )
        _bot_bubble(f"Found <b>{len(results):,}</b> result(s) for <i>\"{query}\"</i>.")
        if not results.empty:
            show_cols = [c for c in [
                "METER NO", "NAME", "MOB NO", "MRU", "Main_Area",
                "Subarea", "METER INLET GI", "METER OUTLET GI", "TOTAL GI", "Charged?",
            ] if c in results.columns]
            st.dataframe(
                results[show_cols].rename(columns={
                    "METER NO": "Meter No", "NAME": "Name", "MOB NO": "Mobile",
                    "Main_Area": "Area", "METER INLET GI": "Inlet GI",
                    "METER OUTLET GI": "Outlet GI", "TOTAL GI": "Total GI",
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            _bot_bubble("😕 No matches found. Try a different name, meter number, or mobile.")
    else:
        st.markdown(
            '<p class="menu-hint">👆 Type above to search across all records in real-time.</p>',
            unsafe_allow_html=True,
        )

    if st.button("🏠 Back to Menu", key="bot_back_search"):
        st.session_state.bot_mode = "menu"
        st.session_state.bot_chat = []
        st.rerun()
