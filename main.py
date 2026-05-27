"""
main.py
=======
Entry point for the Sitapur PNG Field Intelligence Dashboard.

Orchestration order
-------------------
1.  Page config + early CSS (must be the very first st.* call).
2.  Startup guards — missing GitHub token or missing users → st.stop().
3.  Auth gate — check_password() from auth.py → st.stop() if not logged in.
4.  Sidebar force-reset JS (runs once after logout to clean up stale DOM).
5.  inject_premium_theme() — full NOVA dark CSS.
6.  Sidebar toggle JS — animated left-edge collapse button.
7.  Header title bar — app name centred in the Streamlit header.
8.  Tab-aware sidebar section JS — hides irrelevant sidebar sections per tab.
9.  Tab bar extra CSS (pill tabs, bot bubble styles).
10. Sidebar render — render_sidebar() from sidebar_ui.py.
11. Data load — load_connection_data() + load_master_data() from data_loader.py.
12. Apply territory filter to df_conn for the Overview tab.
13. Six tabs are created.
14. Hidden logout button + JS logout pill injected into the tab bar.
15. Tab content:
      Overview      — KPI cards + map.
      Map Analysis  — expandable MRU KPIs + run_analysis() from analysis.py.
      Analysis      — run_analysis() without map section.
      New Connection — render_new_connection_tab() from portal_tabs.py.
      Converted      — render_converted_tab() from portal_tabs.py.
      PNG Assistant  — render_bot_tab() from bot_tab.py.

Module imports
--------------
All logic lives in the sub-modules below. main.py only orchestrates — it
contains no business logic, no data-processing code, and no duplicates.

  premium_theme  — NOVA CSS theme + Plotly theme + colour palettes.
  auth           — Login gate + logout helper.
  config         — Constants: GitHub settings, column schemas, colours.
  data_loader    — load_connection_data(), load_master_data().
  sidebar_ui     — render_sidebar(), apply_area_filter().
  analysis       — run_analysis() for Map Analysis and Analysis tabs.
  portal_tabs    — render_new_connection_tab(), render_converted_tab().
  bot_tab        — render_bot_tab() for the PNG Assistant tab.
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ── Theme (must import before set_page_config to avoid Streamlit warnings) ───────
from premium_theme import (
    inject_premium_theme,
    apply_plotly_theme,
    MRU_COLORS_PREMIUM,
    CHARGED_COLOR_PREMIUM,
)

# ── App sub-modules ───────────────────────────────────────────────────────────────
from auth        import check_password, logout_user, APP_USERS
from config      import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, MRU_COLORS, CHARGED_COLOR
from data_loader import load_connection_data, load_master_data
from sidebar_ui  import render_sidebar, apply_area_filter

# ══════════════════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG — must be the FIRST st.* call in the entire app
# ══════════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Sitapur PNG — Field Intelligence",
    layout="wide",
    page_icon="🔵",
    initial_sidebar_state="expanded",
)

# Compact sidebar and tab overrides applied before any content renders
st.markdown(
    """
    <style>
    div[data-testid="stTabs"] { margin-top:-0.65rem !important; margin-bottom:1.05rem !important; }
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        flex-wrap:nowrap !important; overflow-x:auto !important;
        white-space:nowrap !important; scrollbar-width:none !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar { display:none !important; }
    div[data-testid="stTabs"] [data-baseweb="tab"] {
        white-space:nowrap !important; flex-shrink:0 !important;
        padding-left:0.75rem !important; padding-right:0.75rem !important;
        font-size:0.82rem !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top:0 !important; }
    div[data-testid="stTabs"] [role="tabpanel"]          { padding-top:0 !important; }
    section.main > div.block-container { padding-top:0.25rem !important; margin-top:0 !important; }
    header[data-testid="stHeader"]     { height:2.75rem !important; min-height:2.75rem !important; }
    [data-testid="stSidebar"]          { min-width:230px !important; max-width:230px !important; width:230px !important; }
    [data-testid="stSidebar"] > div:first-child { width:230px !important; }
    /* hide empty secondary button used as logout trigger */
    button[kind="secondary"]:has(p:empty) { display:none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════════
# 2. STARTUP GUARDS
# ══════════════════════════════════════════════════════════════════════════════════
if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
    st.error("Missing GitHub configuration. Add GITHUB_TOKEN in .streamlit/secrets.toml.")
    st.stop()

if not APP_USERS:
    st.error("No app users configured. Add app_users in .streamlit/secrets.toml.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════════
# 3. AUTH GATE — stops execution here if not logged in
# ══════════════════════════════════════════════════════════════════════════════════
check_password()

# ══════════════════════════════════════════════════════════════════════════════════
# 4. SIDEBAR FORCE-RESET (runs once after logout to clean up stale DOM elements)
# ══════════════════════════════════════════════════════════════════════════════════
if st.session_state.pop("sidebar_force_reset", False):
    components.html(
        """
        <script>
        (function(){
            const pdoc = window.parent.document;
            ['sb-toggle-injected','sb-toggle-style','sb-smart-injected',
             'st-logout-btn','st-app-title'].forEach(id => {
                const el = pdoc.getElementById(id);
                if (el) el.remove();
            });
            if (window._sbObserver) { window._sbObserver.disconnect(); window._sbObserver = null; }
            pdoc.body.classList.remove('sidebar-hidden');
            const sidebar = pdoc.querySelector('[data-testid="stSidebar"]');
            const appView = pdoc.querySelector('[data-testid="stAppViewContainer"]');
            if (sidebar) {
                ['transform','pointer-events','position','top','left','transition']
                    .forEach(p => sidebar.style.removeProperty(p));
            }
            if (appView) appView.style.removeProperty('grid-template-columns');
        })();
        </script>
        """,
        height=0,
    )

# ══════════════════════════════════════════════════════════════════════════════════
# 5. PREMIUM THEME
# ══════════════════════════════════════════════════════════════════════════════════
inject_premium_theme()

# ══════════════════════════════════════════════════════════════════════════════════
# 6. SIDEBAR TOGGLE — animated left-edge collapse/expand button
# ══════════════════════════════════════════════════════════════════════════════════
components.html(
    """
<script>
(function(){
    const pdoc = window.parent.document;

    // Teardown any stale instance from a previous Streamlit rerun
    ['sb-toggle-injected','sb-smart-injected','sb-toggle-style'].forEach(id => {
        const el = pdoc.getElementById(id); if (el) el.remove();
    });
    if (window._sbObserver) { window._sbObserver.disconnect(); window._sbObserver = null; }

    // Mark as fresh
    const flag = pdoc.createElement('div');
    flag.id = 'sb-smart-injected'; flag.style.display = 'none';
    pdoc.body.appendChild(flag);

    // ── Styles ──────────────────────────────────────────────────────────────────
    const style = pdoc.createElement('style');
    style.id = 'sb-toggle-style';
    style.textContent = `
        #sb-toggle-injected {
            position:fixed; top:50%; transform:translateY(-50%);
            z-index:999999; width:20px; height:72px; left:0;
            background:linear-gradient(180deg,transparent 0%,rgba(0,212,255,0.3) 50%,transparent 100%);
            border:none; border-right:2px solid rgba(0,212,255,0.55);
            border-radius:0 8px 8px 0; cursor:pointer;
            transition:width 180ms ease,background 180ms ease,opacity 200ms ease;
            display:flex; align-items:center; justify-content:center; padding:0;
        }
        #sb-toggle-injected:hover {
            width:28px;
            background:linear-gradient(180deg,transparent 0%,rgba(0,212,255,0.5) 50%,transparent 100%);
            border-right:2px solid rgba(0,212,255,0.9);
            box-shadow:3px 0 18px rgba(0,212,255,0.3);
        }
        #sb-toggle-injected svg { width:10px; height:10px; transition:transform 300ms ease; }
        #sb-toggle-injected.closed svg { transform:rotate(180deg); }

        body.sidebar-hidden [data-testid="stSidebar"] {
            width:0 !important; min-width:0 !important; max-width:0 !important;
            overflow:hidden !important; transform:translateX(-100%) !important;
            visibility:hidden !important; pointer-events:none !important; position:absolute !important;
        }
        body.sidebar-hidden [data-testid="stAppViewContainer"] {
            grid-template-columns:0px 1fr !important; padding-left:0 !important;
        }
        body.sidebar-hidden [data-testid="stMain"],
        body.sidebar-hidden section[data-testid="stMain"] {
            margin-left:0 !important; width:100vw !important;
            max-width:100vw !important; flex:1 !important;
        }
        body.sidebar-hidden [data-testid="stAppViewBlockContainer"] {
            max-width:100% !important; width:100% !important;
        }
        body:not(.sidebar-hidden) [data-testid="stSidebar"] {
            transform:translateX(0) !important; visibility:visible !important;
            pointer-events:auto !important; position:relative !important;
            width:var(--sidebar-width,230px) !important;
        }
    `;
    pdoc.head.appendChild(style);

    // ── Toggle button ────────────────────────────────────────────────────────────
    const btn = pdoc.createElement('button');
    btn.id = 'sb-toggle-injected'; btn.className = 'closed'; btn.title = 'Toggle sidebar';
    btn.innerHTML = `<svg viewBox="0 0 10 16" xmlns="http://www.w3.org/2000/svg">
        <polyline points="7,2 2,8 7,14" stroke="rgba(0,212,255,0.9)"
            stroke-width="2" fill="none" stroke-linecap="round"/></svg>`;
    pdoc.body.appendChild(btn);

    const D = 280;
    let open = false;

    function sbWidth() {
        const sb = pdoc.querySelector('[data-testid="stSidebar"]');
        return sb ? sb.getBoundingClientRect().width : 0;
    }
    function closeSb(animate) {
        open = false; btn.className = 'closed';
        if (animate) {
            const sb = pdoc.querySelector('[data-testid="stSidebar"]');
            if (sb) sb.style.transition = 'transform 280ms cubic-bezier(0.16,1,0.3,1)';
        }
        pdoc.body.classList.add('sidebar-hidden'); btn.style.left = '0px';
    }
    function openSb(animate) {
        open = true; btn.className = 'open';
        if (animate) {
            const sb = pdoc.querySelector('[data-testid="stSidebar"]');
            if (sb) sb.style.transition = 'transform 280ms cubic-bezier(0.16,1,0.3,1)';
        }
        pdoc.body.classList.remove('sidebar-hidden');
        setTimeout(() => { btn.style.left = (sbWidth() - 10) + 'px'; }, animate ? D : 0);
    }
    btn.addEventListener('click', () => { if (open) closeSb(true); else openSb(true); });

    // ── Tab-aware sidebar visibility ──────────────────────────────────────────────
    const SIDEBAR_TABS = ['Overview', 'Map Analysis'];
    function activeTab() {
        for (const t of pdoc.querySelectorAll('[data-baseweb="tab"]'))
            if (t.getAttribute('aria-selected') === 'true') return t.innerText.trim();
        return null;
    }
    function applyTabBehavior() {
        const active = activeTab();
        if (!active) return;
        const wants = SIDEBAR_TABS.some(n => active.includes(n));
        btn.style.opacity = wants ? '1' : '0';
        btn.style.pointerEvents = wants ? 'auto' : 'none';
        if (!wants) closeSb(false);
        else if (!open) closeSb(false);
    }
    function attachTabListeners() {
        pdoc.querySelectorAll('[data-baseweb="tab"]').forEach(tab => {
            tab.removeEventListener('click', tab._sbH || (()=>{}));
            tab._sbH = () => setTimeout(applyTabBehavior, 150);
            tab.addEventListener('click', tab._sbH);
        });
    }
    window._sbObserver = new MutationObserver(() => attachTabListeners());
    window._sbObserver.observe(pdoc.body, { childList:true, subtree:true });

    function init() {
        const sb = pdoc.querySelector('[data-testid="stSidebar"]');
        if (sb) { closeSb(false); attachTabListeners(); applyTabBehavior(); }
        else setTimeout(init, 100);
    }
    setTimeout(init, 600);
})();
</script>
""",
    height=0,
)

# ══════════════════════════════════════════════════════════════════════════════════
# 7. HEADER TITLE BAR — app name centred in the Streamlit header strip
# ══════════════════════════════════════════════════════════════════════════════════
_user = st.session_state.get("logged_in_user", "unknown")
st.markdown(
    f"""
<style>
#st-app-title {{
    position:fixed; top:8px; left:50%; transform:translateX(-50%);
    z-index:99998; display:flex; align-items:center; gap:8px; pointer-events:none;
}}
#st-app-title .title-main {{
    font-size:0.82rem; font-weight:800; letter-spacing:0.14em; text-transform:uppercase;
    background:linear-gradient(90deg,#00d4ff,#7c4dff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
#st-app-title .title-sub {{ font-size:0.67rem; color:#44556a; font-weight:500; letter-spacing:0.06em; }}
</style>
<div id="st-app-title">
    <span class="title-main">Sitapur PNG</span>
    <span class="title-sub">· BPCL Field Intelligence</span>
</div>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════════
# 8. TAB-AWARE SIDEBAR SECTION VISIBILITY JS
#    Hides #sb-section-overview / #sb-section-map based on the active tab.
# ══════════════════════════════════════════════════════════════════════════════════
components.html(
    """
<script>
(function(){
    const pdoc = window.parent.document;

    function activeTabText() {
        for (const t of pdoc.querySelectorAll('[data-baseweb="tab"]'))
            if (t.getAttribute('aria-selected') === 'true') return t.innerText.trim();
        return '';
    }

    function applyTabSidebarSections() {
        const active    = activeTabText();
        const isOverview = active.includes('Overview');
        const isMap      = active.includes('Map Analysis');
        const sidebar    = pdoc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;

        // First pass: tag blocks by which sentinel div they follow
        if (!sidebar.dataset.sbSectioned) {
            const allBlocks = sidebar.querySelectorAll(
                ':scope > div > div > div > div[data-testid="stVerticalBlock"] > div'
            );
            let mode = 'shared';
            allBlocks.forEach(block => {
                const html = block.innerHTML || '';
                if (html.includes('id="sb-section-overview"')) mode = 'overview';
                else if (html.includes('id="sb-section-map"'))  mode = 'map';
                if (!block.dataset.sbSection) block.dataset.sbSection = mode;
            });
            sidebar.dataset.sbSectioned = '1';
        }

        // Show/hide tagged blocks
        sidebar.querySelectorAll('[data-sb-section]').forEach(block => {
            const sec = block.dataset.sbSection;
            if      (sec === 'overview') block.style.display = isOverview ? '' : 'none';
            else if (sec === 'map')      block.style.display = isMap      ? '' : 'none';
            // 'shared' blocks (brand, refresh) are always visible
        });
    }

    // Re-scan on DOM mutations (Streamlit reruns re-render sidebar)
    let _timer = null;
    const obs = new MutationObserver(() => {
        clearTimeout(_timer);
        _timer = setTimeout(() => {
            const sidebar = pdoc.querySelector('[data-testid="stSidebar"]');
            if (sidebar) delete sidebar.dataset.sbSectioned;
            applyTabSidebarSections();
        }, 200);
    });

    function startObserving() {
        const sidebar = pdoc.querySelector('[data-testid="stSidebar"]');
        if (sidebar) obs.observe(sidebar, { childList:true, subtree:true });
        else setTimeout(startObserving, 200);
    }

    function attachTabListeners() {
        pdoc.querySelectorAll('[data-baseweb="tab"]').forEach(tab => {
            tab.addEventListener('click', () => {
                setTimeout(() => {
                    const sb = pdoc.querySelector('[data-testid="stSidebar"]');
                    if (sb) delete sb.dataset.sbSectioned;
                    applyTabSidebarSections();
                }, 150);
            });
        });
    }

    const bodyObs = new MutationObserver(() => attachTabListeners());
    bodyObs.observe(pdoc.body, { childList:true, subtree:false });

    setTimeout(() => {
        applyTabSidebarSections();
        attachTabListeners();
        startObserving();
    }, 900);
})();
</script>
""",
    height=0,
)

# ══════════════════════════════════════════════════════════════════════════════════
# 9. TAB BAR EXTRA CSS — pill tabs + bot bubble / KPI card styles
# ══════════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
div[data-baseweb="tab-list"] {
    gap:0.5rem; padding:0.15rem 0 0.55rem; margin-top:-0.35rem;
    border-bottom:1px solid rgba(255,255,255,0.08);
    position:sticky; top:0; z-index:40;
    background:rgba(8,12,20,0.82); backdrop-filter:blur(14px);
}
div[data-baseweb="tab"] {
    background:rgba(255,255,255,0.04);
    border:1px solid rgba(255,255,255,0.08); border-radius:999px; padding:0.55rem 1rem;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background:linear-gradient(90deg,rgba(0,212,255,0.18),rgba(124,77,255,0.18));
    border-color:rgba(0,212,255,0.45);
}

/* ── PNG Assistant bot styles (used by bot_tab.py classes) ── */
.bot-bubble {
    background:linear-gradient(135deg,rgba(0,212,255,0.08),rgba(124,77,255,0.08));
    border-left:3px solid #00d4ff; border-radius:0 14px 14px 14px;
    padding:14px 18px; margin:10px 0; color:#c8d6e5;
    font-size:0.93rem; line-height:1.65; box-shadow:0 2px 12px rgba(0,212,255,0.08);
}
.user-bubble {
    background:linear-gradient(135deg,rgba(124,77,255,0.12),rgba(0,212,255,0.06));
    border-right:3px solid #7c4dff; border-radius:14px 0 14px 14px;
    padding:12px 18px; margin:10px 30px 10px 0; color:#c8d6e5;
    font-size:0.93rem; text-align:right; box-shadow:0 2px 12px rgba(124,77,255,0.08);
}
.bot-kpi-card {
    background:linear-gradient(135deg,rgba(0,212,255,0.07),rgba(124,77,255,0.07));
    border:1px solid rgba(0,212,255,0.18); border-radius:12px;
    padding:14px 16px; text-align:center;
}
.bot-kpi-value { font-size:1.6rem; font-weight:700; color:#00d4ff; }
.bot-kpi-label { font-size:0.72rem; color:#6b7fa3; text-transform:uppercase;
                 letter-spacing:0.06em; margin-top:4px; }
.bot-section-header {
    font-size:0.78rem; font-weight:700; letter-spacing:0.14em;
    text-transform:uppercase; color:#00d4ff;
    border-bottom:1px solid rgba(0,212,255,0.15); padding-bottom:6px; margin:18px 0 10px;
}
.menu-hint { color:#44556a; font-size:0.80rem; margin-top:6px; }

/* ── Logout pill ── */
#st-logout-btn {
    position:fixed; top:50px; right:16px; z-index:999999;
    display:flex; align-items:center; gap:8px;
    background:transparent; border:none; padding:0; cursor:pointer;
}
#st-logout-btn .logout-user { font-size:0.72rem; color:#44556a; font-weight:500; }
#st-logout-btn .logout-pill {
    display:inline-flex; align-items:center; gap:5px; padding:4px 12px;
    border-radius:999px; background:rgba(255,59,48,0.10);
    border:1px solid rgba(255,59,48,0.30); color:#ff6b6b;
    font-size:0.75rem; font-weight:600; cursor:pointer; transition:background 150ms;
}
#st-logout-btn .logout-pill:hover {
    background:rgba(255,59,48,0.22); border-color:rgba(255,59,48,0.6);
}
</style>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════════
# 10. SIDEBAR — renders all sidebar widgets and returns a settings dict
# ══════════════════════════════════════════════════════════════════════════════════
# NOTE: df_conn / df_master are loaded AFTER the sidebar so the sidebar widgets
# render immediately on the first run without waiting for data. The loaded frames
# are passed into render_sidebar so the date-range picker can derive its bounds.
# We load first so the sidebar date picker has real min/max dates to work with.

df_conn   = load_connection_data()
df_master = load_master_data()

sb = render_sidebar(df_conn, df_master)

# Unpack sidebar return dict into local names for readability
filter_mode          = sb["filter_mode"]
allowed_mrus         = sb["allowed_mrus"]
allowed_areas        = sb["allowed_areas"]
grey_uncharged      = sb["grey_uncharged"]
show_charged        = sb["show_charged"]
map_style            = sb["map_style"]
date_d0              = sb["date_d0"]
date_d1              = sb["date_d1"]
df_master_f          = sb["df_master_f"]
_map_mode            = sb["map_mode"]
_heatmap_tile        = sb["heatmap_tile"]
_anim_mrus           = sb["anim_mrus"]
_show_charged_overlay = sb["show_charged_overlay"]

# Territory-filtered connections (for the Overview tab only)
df_conn_f = apply_area_filter(df_conn, allowed_areas, allowed_mrus)

# ══════════════════════════════════════════════════════════════════════════════════
# 11. TABS
# ══════════════════════════════════════════════════════════════════════════════════
main_tab, map_tab, analysis_tab, new_conn_tab, converted_tab, bot_tab = st.tabs([
    "🏠 Overview", "🗺️ Map Analysis", "📊 Analysis",
    "➕ New Connection", "⚡ Converted", "🤖 PNG Assistant",
])

# ══════════════════════════════════════════════════════════════════════════════════
# 12. LOGOUT BUTTON (hidden real button + visible JS pill in the top-right)
# ══════════════════════════════════════════════════════════════════════════════════
# The real Streamlit button is hidden via CSS; the JS pill clicks it on trigger.
st.markdown(
    '<style>[data-testid="stButton"][id="tab_logout_hidden_wrap"]{display:none!important}</style>',
    unsafe_allow_html=True,
)
if st.button("🚪", key="tab_logout_hidden"):
    logout_user()

components.html(
    f"""
<script>
(function(){{
    const user = {repr(_user)};
    function inject() {{
        const pdoc = window.parent.document;
        if (pdoc.getElementById('st-logout-btn')) return;
        const allBtns = pdoc.querySelectorAll('button');
        let hiddenBtn = null;
        for (const b of allBtns) {{
            if (b.innerText.trim() === '🚪') {{ hiddenBtn = b; break; }}
        }}
        if (!hiddenBtn) {{ setTimeout(inject, 300); return; }}
        const wrap = hiddenBtn.closest('[data-testid="stButton"]') || hiddenBtn.parentElement;
        if (wrap) wrap.style.display = 'none';
        const pill = pdoc.createElement('div');
        pill.id = 'st-logout-btn';
        pill.innerHTML = `
            <span class="logout-user">👤 ${{user}}</span>
            <span class="logout-pill">🚪 Logout</span>
        `;
        pill.querySelector('.logout-pill').addEventListener('click', () => hiddenBtn.click());
        pdoc.body.appendChild(pill);
    }}
    setTimeout(inject, 800);
}})();
</script>
""",
    height=0,
)

# ══════════════════════════════════════════════════════════════════════════════════
# 13. OVERVIEW TAB — KPI cards + full map
# ══════════════════════════════════════════════════════════════════════════════════
import plotly.express as px

# KPI metrics
_total         = len(df_conn_f)
_converted     = len(df_master_f)
_uncharged     = len(df_conn_f[df_conn_f["AREA_STATUS"].astype(str).str.upper() == "UNCHARGED"])
_not_converted = _total - _converted
_conversion_pct = f"{_converted / _total * 100:.1f}%" if _total > 0 else "—"

with main_tab:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔌 Total",          f"{_total:,}")
    c2.metric("⚡ Converted",      f"{_converted:,}")
    c3.metric("📈 Conversion %",   _conversion_pct)
    c4.metric("⭕ Not Converted",  f"{_not_converted:,}")
    c5.metric("📍 Uncharged",      f"{_uncharged:,}")

# Build the Overview map
_GOOGLE_TILES = {
    "google-satellite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    "google-road":      "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "google-terrain":   "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
}

# Compute map centre from all visible points
_all_lats = list(df_conn_f["Latitude"])
_all_lons = list(df_conn_f["Longitude"])
if show_charged and not df_master_f.empty:
    _all_lats += list(df_master_f["Latitude"].dropna())
    _all_lons += list(df_master_f["Longitude"].dropna())
center_lat = pd.Series(_all_lats).median() if _all_lats else 27.560
center_lon = pd.Series(_all_lons).median() if _all_lons else 80.690

# Connections scatter with resolved visual state
plot_df = df_conn_f.copy()
charged_meter_set = set(df_master_f["Meter Number"].dropna().astype(str).str.strip()) if not df_master_f.empty else set()
plot_df["dot_state"] = plot_df["MRU"].astype(str)
if grey_uncharged:
    mask_unch = plot_df["AREA_STATUS"].astype(str).str.upper().eq("UNCHARGED")
    plot_df.loc[mask_unch, "dot_state"] = "UNCHARGED"
if show_charged:
    mask_chg = plot_df["METER NO"].astype(str).str.strip().isin(charged_meter_set)
    plot_df.loc[mask_chg, "dot_state"] = "CHARGED"

color_map = dict(MRU_COLORS)
color_map["UNCHARGED"] = "#9AA0A6"
color_map["CHARGED"] = CHARGED_COLOR

_base_style = "white-bg" if map_style in _GOOGLE_TILES else map_style
fig = px.scatter_mapbox(
    plot_df,
    lat="Latitude", lon="Longitude",
    hover_name="NAME",
    hover_data={
        "METER NO": True, "MOB NO": True,
        "MRU": True, "Main_Area": True,
        "AREA_STATUS": True,
        "Latitude": ":.6f", "Longitude": ":.6f",
    },
    color="dot_state",
    color_discrete_map=color_map,
    zoom=13,
    center={"lat": center_lat, "lon": center_lon},
    mapbox_style=_base_style,
    height=700,
    title=f"PNG Houses — {_total:,} connections · {_converted:,} converted",
)
for tr in fig.data:
    if getattr(tr, "name", "") == "CHARGED":
        tr.marker.size = 4.4
        tr.marker.opacity = 0.98
    else:
        tr.marker.size = 4
        tr.marker.opacity = 0.85


# Apply Google tile overlay when a Google style is selected
if map_style in _GOOGLE_TILES:
    fig.update_layout(
        mapbox={
            "style":  "white-bg",
            "zoom":   13,
            "center": {"lat": center_lat, "lon": center_lon},
            "layers": [{
                "sourcetype":        "raster",
                "sourceattribution": "Google",
                "source":            [_GOOGLE_TILES[map_style]],
                "below":             "traces",
            }],
        }
    )

apply_plotly_theme(fig, height=700)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    legend=dict(
        title=dict(text="MRU / STATUS",
                   font=dict(size=9, color="#44445a", family="Inter, sans-serif")),
        bgcolor="rgba(24,24,48,0.92)",
        bordercolor="rgba(255,255,255,0.07)",
        borderwidth=1,
        font=dict(size=11, color="#8888aa", family="Inter, sans-serif"),
        x=0.01, y=0.99,
    ),
)

with main_tab:
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

# ══════════════════════════════════════════════════════════════════════════════════
# 14. MAP ANALYSIS TAB — expandable KPI table + analysis.py map
# ══════════════════════════════════════════════════════════════════════════════════
with map_tab:
    # Map only — charts and scorecard table live in the Analysis tab
    from analysis import run_analysis
    run_analysis(
        df_conn, df_master,
        show_deep_tabs=False,
        widget_prefix="map_analysis",
        show_map_section=True,
        d0=date_d0, d1=date_d1,
        map_mode=_map_mode,
        heatmap_tile=_heatmap_tile,
        anim_mrus=_anim_mrus,
        show_charged_overlay=_show_charged_overlay,
        show_uncov_overlay=grey_uncharged,
    )

# ══════════════════════════════════════════════════════════════════════════════════
# 15. ANALYSIS TAB — same analysis.py call, map section suppressed
# ══════════════════════════════════════════════════════════════════════════════════
with analysis_tab:
    from analysis import run_analysis
    run_analysis(
        df_conn, df_master,
        show_deep_tabs=True,
        widget_prefix="deep_analysis",
        show_map_section=False,
        d0=date_d0, d1=date_d1,
        map_mode=_map_mode,
        heatmap_tile=_heatmap_tile,
        anim_mrus=_anim_mrus,
        show_charged_overlay=_show_charged_overlay,
        show_uncov_overlay=grey_uncharged,
    )

# ══════════════════════════════════════════════════════════════════════════════════
# 16. PORTAL TABS — data entry forms (read/write GitHub CSVs)
# ══════════════════════════════════════════════════════════════════════════════════
from portal_tabs import render_new_connection_tab, render_converted_tab

with new_conn_tab:
    render_new_connection_tab()

with converted_tab:
    render_converted_tab()

# ══════════════════════════════════════════════════════════════════════════════════
# 17. PNG ASSISTANT TAB
# ══════════════════════════════════════════════════════════════════════════════════
from bot_tab import render_bot_tab

with bot_tab:
    render_bot_tab(df_conn, df_master)
