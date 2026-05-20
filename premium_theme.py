import streamlit as st


def inject_premium_theme():
    st.markdown("""
    <style>
    /*
     *  THEME: NOVA
     *  Deep navy · neon cyan/magenta/violet · gradient cards · glowing charts
     *  Reference: CRM Dashboard (dark purple-navy base, vivid gradient accents)
     */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        /* Backgrounds — deep navy */
        --bg:          #0e0e1a;
        --bg-2:        #12122a;
        --surface:     #181830;
        --surface-2:   #1e1e38;
        --surface-3:   #252548;

        /* Borders */
        --border:      rgba(255,255,255,0.07);
        --border-2:    rgba(255,255,255,0.12);

        /* Text */
        --text:        #f0f0ff;
        --text-2:      #8888aa;
        --text-3:      #44445a;

        /* Accent system — neon */
        --cyan:        #00d4ff;
        --cyan-dim:    rgba(0,212,255,0.12);
        --cyan-glow:   rgba(0,212,255,0.22);
        --magenta:     #e040fb;
        --magenta-dim: rgba(224,64,251,0.12);
        --violet:      #7c4dff;
        --violet-dim:  rgba(124,77,255,0.15);
        --teal:        #00e5cc;
        --pink:        #ff4db8;

        /* Semantic */
        --green:       #00e5a0;
        --amber:       #ffb340;
        --red:         #ff4d6a;

        /* Gradient presets */
        --grad-cyan-magenta: linear-gradient(135deg, #00d4ff 0%, #e040fb 100%);
        --grad-cyan-violet:  linear-gradient(135deg, #00d4ff 0%, #7c4dff 100%);
        --grad-magenta-pink: linear-gradient(135deg, #e040fb 0%, #ff4db8 100%);
        --grad-teal-cyan:    linear-gradient(135deg, #00e5cc 0%, #00d4ff 100%);

        /* Radius */
        --r-sm:  6px;
        --r-md:  10px;
        --r-lg:  14px;
        --r-xl:  18px;

        /* Shadows */
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.4);
        --shadow-md: 0 4px 24px rgba(0,0,0,0.5);
        --shadow-lg: 0 8px 40px rgba(0,0,0,0.6);
        --glow-cyan:    0 0 20px rgba(0,212,255,0.25), 0 0 6px rgba(0,212,255,0.15);
        --glow-magenta: 0 0 20px rgba(224,64,251,0.25), 0 0 6px rgba(224,64,251,0.15);
        --glow-violet:  0 0 20px rgba(124,77,255,0.25);

        --ease: cubic-bezier(0.16, 1, 0.3, 1);
        --t:    180ms;
        --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Reset ── */
    *, *::before, *::after { box-sizing: border-box; }
    html, body, [class*="css"] {
        font-family: var(--font) !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        letter-spacing: -0.01em;
    }

    /* ── App background — deep navy with ambient glow ── */
    .stApp {
        background:
            radial-gradient(ellipse 70% 40% at 10% 5%,  rgba(124,77,255,0.12) 0%, transparent 55%),
            radial-gradient(ellipse 50% 35% at 90% 90%, rgba(0,229,204,0.08)  0%, transparent 55%),
            radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,212,255,0.04)  0%, transparent 60%),
            #0e0e1a !important;
        background-attachment: fixed !important;
    }

    /* ── Top bar ── */
    header[data-testid="stHeader"] {
        background: rgba(14,14,26,0.90) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border) !important;
        box-shadow: none !important;
    }

    /* ── Layout ── */
    .block-container {
        padding: 2rem 2.5rem 5rem !important;
        max-width: 1480px !important;
    }

    /* ── Typography — Big Bold Gradient Headings ── */
    .stApp h1 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1.1 !important;
        background: linear-gradient(100deg, #ffffff 0%, #00d4ff 50%, #7c4dff 100%) !important;
        background-size: 200% 100% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: gradShift 6s ease infinite !important;
        filter: drop-shadow(0 0 18px rgba(0,212,255,0.25)) !important;
    }
    h2, .stApp h2 {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        background: linear-gradient(90deg, #f0f0ff 0%, #00d4ff 80%, #7c4dff 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        filter: drop-shadow(0 0 10px rgba(0,212,255,0.20)) !important;
    }
    h3, .stApp h3 {
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        background: linear-gradient(90deg, #c0eeff 0%, #7c4dff 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }
    h4, .stApp h4 {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: var(--cyan) !important;
        letter-spacing: 0.02em !important;
        text-transform: uppercase !important;
    }
    p, li, .stMarkdown p {
        color: var(--text-2) !important;
        font-size: 1rem !important;
        line-height: 1.65 !important;
    }
    label { color: rgba(180,180,220,0.85) !important; font-size: 0.9375rem !important; font-weight: 500 !important; }

    /* ── Glowing horizontal divider lines ── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(0,212,255,0.6) 20%,
            rgba(124,77,255,0.8) 50%,
            rgba(224,64,251,0.6) 80%,
            transparent 100%) !important;
        box-shadow: 0 0 12px rgba(0,212,255,0.3), 0 0 24px rgba(124,77,255,0.2) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Colourful card shadows on ALL surface containers ── */
    [data-testid="stVerticalBlock"] > div {
        transition: box-shadow 250ms ease !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 1rem !important;
    }

    /* ── Main content area — ambient multi-colour glow ── */
    .block-container {
        padding: 2rem 2.5rem 5rem !important;
        max-width: 1480px !important;
        position: relative !important;
    }
    .block-container::before {
        content: '';
        position: fixed;
        top: -10%; left: -5%;
        width: 40%; height: 40%;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(124,77,255,0.07) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    .block-container::after {
        content: '';
        position: fixed;
        bottom: 0; right: 0;
        width: 35%; height: 35%;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,229,204,0.06) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Tab bar — glowing active indicator ── */
    [data-testid="stTabs"] {
        border-bottom: 1px solid rgba(0,212,255,0.12) !important;
        box-shadow: 0 1px 0 0 rgba(0,212,255,0.08) !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        color: #44445a !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: var(--r-md) var(--r-md) 0 0 !important;
        transition: color 180ms ease, background 180ms ease !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: #f0f0ff !important;
        background: linear-gradient(135deg, rgba(0,212,255,0.14) 0%, rgba(124,77,255,0.14) 100%) !important;
        box-shadow: 0 0 20px rgba(0,212,255,0.15), inset 0 -2px 0 var(--cyan) !important;
        -webkit-text-fill-color: unset !important;
    }

    /* ── Sidebar section labels — glowing uppercase ── */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 0.6rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.18em !important;
        text-transform: uppercase !important;
        background: linear-gradient(90deg, #00d4ff, #7c4dff) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        filter: drop-shadow(0 0 6px rgba(0,212,255,0.4)) !important;
        margin-top: 1.5rem !important;
    }

    /* ── Toggle (switch) — colourful glow when on ── */
    [data-testid="stToggle"] input:checked + div {
        background: linear-gradient(135deg, #00d4ff, #7c4dff) !important;
        box-shadow: 0 0 14px rgba(0,212,255,0.5) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* Hide native collapse/expand buttons — we use our own toggle */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }


    [data-testid="stSidebar"] .block-container {
        padding: 1.5rem 1.25rem !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 0.6rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        color: var(--text-3) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-2) !important;
    }
    [data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1rem 0 !important;
    }

    /* ── Sidebar nav active item glow ── */
    [data-testid="stSidebar"] [aria-selected="true"],
    [data-testid="stSidebar"] [data-active="true"] {
        background: rgba(124,77,255,0.15) !important;
        border-left: 2px solid var(--violet) !important;
        border-radius: var(--r-md) !important;
    }

    /* ── Inputs — Premium Dropdowns ── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        font-size: 0.9375rem !important;
    }
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stMultiSelect"] > div > div {
        background: linear-gradient(135deg, #1a1a35 0%, #1e1e40 100%) !important;
        border: 1px solid rgba(0,212,255,0.18) !important;
        border-radius: var(--r-lg) !important;
        color: var(--text) !important;
        font-size: 0.8125rem !important;
        transition: border-color 200ms ease, box-shadow 200ms ease !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.35) !important;
    }
    [data-testid="stSelectbox"] > div > div:hover,
    [data-testid="stMultiSelect"] > div > div:hover {
        border-color: rgba(0,212,255,0.35) !important;
        box-shadow: 0 0 16px rgba(0,212,255,0.10), 0 2px 12px rgba(0,0,0,0.35) !important;
    }
    [data-testid="stSelectbox"] > div > div:focus-within,
    [data-testid="stMultiSelect"] > div > div:focus-within {
        border-color: var(--cyan) !important;
        box-shadow: 0 0 0 2px rgba(0,212,255,0.18), 0 0 24px rgba(0,212,255,0.15) !important;
    }
    [data-testid="stSelectbox"] span,
    [data-testid="stMultiSelect"] span { color: var(--text) !important; }
    /* Dropdown chevron */
    [data-testid="stSelectbox"] svg,
    [data-testid="stMultiSelect"] svg { color: rgba(0,212,255,0.6) !important; fill: rgba(0,212,255,0.6) !important; }

    /* ── Dropdown popup menu (the white box!) ── */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    ul[data-baseweb="menu"],
    [role="listbox"] {
        background: #181830 !important;
        background: linear-gradient(160deg, #1c1c38 0%, #181830 100%) !important;
        border: 1px solid rgba(0,212,255,0.15) !important;
        border-radius: var(--r-lg) !important;
        box-shadow: 0 8px 40px rgba(0,0,0,0.7), 0 0 24px rgba(0,212,255,0.08) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        overflow: hidden !important;
    }
    /* Dropdown list items */
    li[role="option"],
    [data-baseweb="menu"] li,
    [role="listbox"] li {
        background: transparent !important;
        color: #8888aa !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        padding: 9px 14px !important;
        border-radius: 0 !important;
        transition: background 150ms ease, color 150ms ease !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    }
    li[role="option"]:hover,
    [data-baseweb="menu"] li:hover,
    [role="listbox"] li:hover {
        background: linear-gradient(135deg, rgba(0,212,255,0.12) 0%, rgba(124,77,255,0.10) 100%) !important;
        color: #f0f0ff !important;
    }
    /* Selected item in dropdown */
    li[aria-selected="true"],
    [data-baseweb="menu"] li[aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,212,255,0.18) 0%, rgba(124,77,255,0.15) 100%) !important;
        color: var(--cyan) !important;
        font-weight: 600 !important;
    }

    /* ── Coloured left-bar per dropdown option ── */
    /* MRU colours */
    li[role="option"]:nth-child(1) { border-left: 3px solid #00d4ff !important; }
    li[role="option"]:nth-child(2) { border-left: 3px solid #7c4dff !important; }
    li[role="option"]:nth-child(3) { border-left: 3px solid #e040fb !important; }
    li[role="option"]:nth-child(4) { border-left: 3px solid #00e5cc !important; }
    li[role="option"]:nth-child(5) { border-left: 3px solid #ff4db8 !important; }
    li[role="option"]:nth-child(6) { border-left: 3px solid #ffb340 !important; }
    li[role="option"]:nth-child(7) { border-left: 3px solid #00e5a0 !important; }
    li[role="option"]:nth-child(8) { border-left: 3px solid #ff4d6a !important; }
    li[role="option"]:nth-child(9) { border-left: 3px solid #a78bfa !important; }
    li[role="option"]:nth-child(10){ border-left: 3px solid #34d399 !important; }

    /* Hover brightens the left bar */
    li[role="option"]:hover {
        padding-left: 18px !important;
        transition: padding-left 150ms ease !important;
    }

    /* Dot indicator before each item */
    li[role="option"]::before {
        content: '';
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
        flex-shrink: 0;
    }
    li[role="option"]:nth-child(1)::before  { background: #00d4ff; box-shadow: 0 0 6px #00d4ff; }
    li[role="option"]:nth-child(2)::before  { background: #7c4dff; box-shadow: 0 0 6px #7c4dff; }
    li[role="option"]:nth-child(3)::before  { background: #e040fb; box-shadow: 0 0 6px #e040fb; }
    li[role="option"]:nth-child(4)::before  { background: #00e5cc; box-shadow: 0 0 6px #00e5cc; }
    li[role="option"]:nth-child(5)::before  { background: #ff4db8; box-shadow: 0 0 6px #ff4db8; }
    li[role="option"]:nth-child(6)::before  { background: #ffb340; box-shadow: 0 0 6px #ffb340; }
    li[role="option"]:nth-child(7)::before  { background: #00e5a0; box-shadow: 0 0 6px #00e5a0; }
    li[role="option"]:nth-child(8)::before  { background: #ff4d6a; box-shadow: 0 0 6px #ff4d6a; }
    li[role="option"]:nth-child(9)::before  { background: #a78bfa; box-shadow: 0 0 6px #a78bfa; }
    li[role="option"]:nth-child(10)::before { background: #34d399; box-shadow: 0 0 6px #34d399; }

    /* Radio — unselected */
    [data-testid="stRadio"] label {
        font-size: 0.8125rem !important;
        color: var(--text-2) !important;
        transition: color 180ms ease !important;
    }
    [data-testid="stRadio"] label:has(input[type="radio"]:not(:checked)) p {
        color: var(--text-2) !important;
    }
    /* Radio circle unselected */
    [data-testid="stRadio"] label span[data-testid="stWidgetLabel"] { display:none; }
    [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
        border: 2px solid rgba(255,255,255,0.2) !important;
        background: var(--surface-2) !important;
        transition: all 180ms ease !important;
    }
    /* Radio circle selected */
    [data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] > div:first-child {
        border-color: var(--cyan) !important;
        background: var(--cyan) !important;
        box-shadow: 0 0 8px var(--cyan-glow) !important;
    }
    [data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] > div:first-child > div {
        background: #0e0e1a !important;
    }
    /* Label text selected */
    [data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] p {
        color: var(--cyan) !important;
        font-weight: 600 !important;
    }

    [data-testid="stDateInput"] input {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-md) !important;
        color: var(--text) !important;
        font-size: 0.8125rem !important;
    }

    /* ── Parallel date inputs in sidebar ── */
    [data-testid="stSidebar"] .stDateInput,
    [data-testid="stSidebar"] [data-testid="stDateInput"] {
        display: inline-block !important;
        width: calc(50% - 4px) !important;
        vertical-align: top !important;
    }
    [data-testid="stSidebar"] .stDateInput:nth-of-type(odd),
    [data-testid="stSidebar"] [data-testid="stDateInput"]:nth-of-type(odd) {
        margin-right: 4px !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
        font-size: 0.75rem !important;
        padding: 4px 6px !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] label p {
        font-size: 0.6875rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background: var(--cyan) !important;
        box-shadow: var(--glow-cyan) !important;
    }

    /* ── Metric cards — gradient header stripe ── */
    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-xl) !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: var(--shadow-sm) !important;
        position: relative;
        overflow: hidden;
        transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease) !important;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--grad-cyan-magenta);
        border-radius: var(--r-xl) var(--r-xl) 0 0;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(0,212,255,0.12) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.625rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: var(--text-3) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.05em !important;
        color: var(--text) !important;
        line-height: 1.05 !important;
    }
    [data-testid="stMetricDelta"] { font-size: 0.75rem !important; font-weight: 600 !important; }

    /* ── Plotly chart container ── */
    [data-testid="stPlotlyChart"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-xl) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ── DataFrame ── */
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-xl) !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] th {
        background: var(--surface-2) !important;
        font-size: 0.625rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.10em !important;
        text-transform: uppercase !important;
        color: var(--text-3) !important;
        border-bottom: 1px solid var(--border) !important;
    }
    [data-testid="stDataFrame"] td {
        font-size: 0.8125rem !important;
        color: var(--text-2) !important;
        border-bottom: 1px solid rgba(255,255,255,0.03) !important;
    }
    [data-testid="stDataFrame"] tr:hover td {
        background: rgba(0,212,255,0.03) !important;
    }

    /* ── Tabs — pill style like reference ── */
    [data-testid="stTabs"] [role="tablist"] {
        background: var(--surface) !important;
        border-radius: var(--r-xl) !important;
        padding: 4px !important;
        border: 1px solid var(--border) !important;
        gap: 2px !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        border-radius: var(--r-lg) !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        color: var(--text-3) !important;
        padding: 0.375rem 1rem !important;
        border: none !important;
        transition: all var(--t) var(--ease) !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,212,255,0.18) 0%, rgba(124,77,255,0.18) 100%) !important;
        color: var(--cyan) !important;
        border: 1px solid rgba(0,212,255,0.2) !important;
        font-weight: 600 !important;
        box-shadow: 0 0 12px rgba(0,212,255,0.12) !important;
    }
    [data-testid="stTabs"] [role="tab"]:hover { color: var(--text-2) !important; }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-xl) !important;
        overflow: hidden !important;
    }
    [data-testid="stExpander"] summary {
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 0.875rem 1rem !important;
        color: var(--text-2) !important;
        background: transparent !important;
    }
    [data-testid="stExpander"] summary:hover { color: var(--text) !important; }

    /* ── Buttons — gradient primary ── */
    .stButton > button {
        background: linear-gradient(135deg, var(--violet) 0%, var(--magenta) 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 999px !important;
        font-size: 0.8125rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.25rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 0 16px rgba(124,77,255,0.30) !important;
        transition: all var(--t) var(--ease) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 0 28px rgba(224,64,251,0.40) !important;
    }
    .stButton > button:active { transform: scale(0.97) !important; }

    /* ── Section divider ── */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 2rem 0 !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(124,77,255,0.25);
        border-radius: 999px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0,212,255,0.35); }

    /* ── Multiselect tags — gradient pill ── */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background: linear-gradient(135deg, rgba(0,212,255,0.18) 0%, rgba(124,77,255,0.18) 100%) !important;
        color: #c0eeff !important;
        border-radius: 20px !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        border: 1px solid rgba(0,212,255,0.30) !important;
        padding: 3px 10px !important;
        box-shadow: 0 0 8px rgba(0,212,255,0.12) !important;
        transition: box-shadow 150ms ease, border-color 150ms ease !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"]:hover {
        border-color: rgba(0,212,255,0.55) !important;
        box-shadow: 0 0 14px rgba(0,212,255,0.22) !important;
    }
    /* Multiselect wrapper — force dark gradient on all child containers */
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div > div,
    [data-testid="stMultiSelect"] div[data-baseweb="select"],
    [data-testid="stMultiSelect"] > div > div {
        background: linear-gradient(135deg, #1a1a35 0%, #1e1e40 100%) !important;
        border-color: rgba(0,212,255,0.18) !important;
        border-radius: var(--r-lg) !important;
        min-height: 44px !important;
        color: var(--text) !important;
    }
    [data-testid="stMultiSelect"] input {
        background: transparent !important;
        color: var(--text) !important;
        caret-color: var(--cyan) !important;
    }
    /* Tag remove × button */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] span:last-child {
        color: rgba(0,212,255,0.55) !important;
        font-weight: 700 !important;
    }
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] span:last-child:hover {
        color: #ff4db8 !important;
    }

    /* ── Alert ── */
    [data-testid="stAlert"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r-xl) !important;
        font-size: 0.875rem !important;
    }

    /* ── Sidebar brand ── */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.75rem;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid var(--border);
    }
    .sidebar-brand-text {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.02em;
    }
    .sidebar-brand-sub {
        font-size: 0.6875rem;
        color: var(--text-3);
        font-weight: 400;
    }

    /* ── Section label ── */
    .section-label {
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 0.625rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.75rem;
        margin-top: 0.25rem;
    }
    .section-label::before {
        content: '';
        display: block;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--grad-cyan-magenta);
        box-shadow: 0 0 8px var(--cyan-glow);
    }

    /* ── Gradient KPI card (custom HTML) ── */
    .kpi-card {
        border-radius: var(--r-xl);
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        min-height: 100px;
    }
    .kpi-card-cyan { background: linear-gradient(135deg, #00b4d8 0%, #7c4dff 100%); }
    .kpi-card-magenta { background: linear-gradient(135deg, #00d4ff 0%, #e040fb 100%); }
    .kpi-card::after {
        content: '';
        position: absolute;
        top: -30%; right: -10%;
        width: 160px; height: 160px;
        border-radius: 50%;
        background: rgba(255,255,255,0.08);
        pointer-events: none;
    }
    .kpi-card .kpi-label {
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.7);
        margin-bottom: 0.5rem;
    }
    .kpi-card .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.05em;
        color: #fff;
        line-height: 1;
    }
    .kpi-card .kpi-sub {
        font-size: 0.8125rem;
        color: rgba(255,255,255,0.6);
        margin-top: 0.25rem;
    }

    /* ── Callout info card ── */
    .callout-card {
        background: var(--surface);
        border: 1px solid rgba(0,212,255,0.14);
        border-radius: var(--r-lg);
        padding: 1rem 1.25rem;
        margin-top: 0.75rem;
    }
    .callout-card p {
        font-size: 0.8125rem !important;
        color: var(--text-2) !important;
        margin: 0 !important;
        line-height: 1.9 !important;
    }
    .callout-card strong { color: var(--cyan) !important; }

    /* ── Map wrapper ── */
    .map-wrapper {
        border-radius: var(--r-xl) !important;
        overflow: hidden !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Badge ── */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .badge-green  { background: rgba(48,209,88,0.15); color: #30d158; }
    .badge-red    { background: rgba(255,77,106,0.15); color: #ff4d6a; }
    .badge-cyan   { background: var(--cyan-dim);       color: var(--cyan); }
    .badge-violet { background: var(--violet-dim);     color: #a57fff; }

    /* ── Spinner ── */
    [data-testid="stSpinner"] { color: var(--cyan) !important; }

    /* ── Hide chrome ── */
    #MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

    /* ── Page enter ── */
    .stApp { animation: enter 0.4s cubic-bezier(0.16,1,0.3,1); }
    @keyframes enter {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Animated gradient border on KPI cards ── */
    @keyframes borderSpin {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes gradShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 18px rgba(0,212,255,0.18), 0 4px 24px rgba(0,0,0,0.5); }
        50%       { box-shadow: 0 0 32px rgba(124,77,255,0.28), 0 4px 32px rgba(0,0,0,0.55); }
    }
    @keyframes shimmerBar {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* KPI metric cards — animated gradient top stripe + ambient glow */
    [data-testid="stMetric"] {
        background: linear-gradient(160deg, #1a1a35 0%, #1e1e40 60%, #181830 100%) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: var(--r-xl) !important;
        padding: 1.25rem 1.5rem !important;
        position: relative;
        overflow: hidden;
        transition: transform 220ms cubic-bezier(0.16,1,0.3,1),
                    box-shadow 220ms cubic-bezier(0.16,1,0.3,1) !important;
        animation: pulseGlow 4s ease-in-out infinite !important;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg,
            #00d4ff, #7c4dff, #e040fb, #ff4db8, #00e5cc, #00d4ff);
        background-size: 300% 100%;
        animation: shimmerBar 3s linear infinite;
        border-radius: var(--r-xl) var(--r-xl) 0 0;
    }
    /* Ambient inner glow orb */
    [data-testid="stMetric"]::after {
        content: '';
        position: absolute;
        bottom: -30px; right: -20px;
        width: 100px; height: 100px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,212,255,0.10) 0%, transparent 70%);
        pointer-events: none;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) scale(1.01) !important;
        box-shadow: 0 0 40px rgba(0,212,255,0.22), 0 12px 40px rgba(0,0,0,0.6) !important;
        border-color: rgba(0,212,255,0.25) !important;
    }
    /* Gradient metric values */
    [data-testid="stMetricValue"] > div {
        background: linear-gradient(135deg, #f0f0ff 30%, #00d4ff 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    /* ── Plotly chart containers — gradient bg + animated border ── */
    [data-testid="stPlotlyChart"] {
        background: linear-gradient(160deg, #161628 0%, #1c1c36 50%, #181830 100%) !important;
        border: 1px solid rgba(0,212,255,0.10) !important;
        border-radius: var(--r-xl) !important;
        overflow: hidden !important;
        transition: border-color 220ms ease, box-shadow 220ms ease !important;
        position: relative;
    }
    [data-testid="stPlotlyChart"]:hover {
        border-color: rgba(0,212,255,0.22) !important;
        box-shadow: 0 0 30px rgba(0,212,255,0.10), 0 8px 40px rgba(0,0,0,0.5) !important;
    }
    /* Top shimmer bar on every chart */
    [data-testid="stPlotlyChart"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg,
            transparent 0%, #00d4ff 30%, #7c4dff 60%, #e040fb 80%, transparent 100%);
        background-size: 200% 100%;
        animation: shimmerBar 4s linear infinite;
        z-index: 1;
    }

    /* ── Sidebar — subtle animated gradient bg ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,
            #131326 0%,
            #181830 40%,
            #141428 100%) !important;
        border-right: 1px solid rgba(0,212,255,0.08) !important;
    }

    /* ── Tab active — gradient underline ── */
    [data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,212,255,0.12) 0%, rgba(124,77,255,0.12) 100%) !important;
        border-bottom: 2px solid transparent !important;
        border-image: linear-gradient(90deg, #00d4ff, #7c4dff, #e040fb) 1 !important;
    }

    /* ── Expander — gradient header bg ── */
    [data-testid="stExpander"] summary {
        background: linear-gradient(135deg, rgba(0,212,255,0.06) 0%, rgba(124,77,255,0.06) 100%) !important;
        border-radius: var(--r-md) !important;
    }

    /* ── Dataframe container — gradient bg ── */
    [data-testid="stDataFrame"] {
        background: linear-gradient(160deg, #161628 0%, #1c1c38 100%) !important;
        border-radius: var(--r-xl) !important;
        border: 1px solid rgba(0,212,255,0.08) !important;
        overflow: hidden !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # ── Mouse-tracking glow + hover sidebar JS ──
    st.markdown("""
    <script>
    (function() {

        /* ── 1. Card mouse-glow ── */
        function applyMouseGlow() {
            const cards = document.querySelectorAll(
                '[data-testid="stMetric"], [data-testid="stPlotlyChart"]'
            );
            cards.forEach(card => {
                if (card._glowBound) return;
                card._glowBound = true;
                card.addEventListener('mousemove', e => {
                    const r = card.getBoundingClientRect();
                    const x = ((e.clientX - r.left) / r.width  * 100).toFixed(1);
                    const y = ((e.clientY - r.top)  / r.height * 100).toFixed(1);
                    card.style.background =
                        `radial-gradient(circle at ${x}% ${y}%, rgba(0,212,255,0.13) 0%, rgba(124,77,255,0.08) 35%, #161628 70%) !important`;
                });
                card.addEventListener('mouseleave', () => {
                    card.style.background = '';
                });
            });
        }

        /* ── Boot card glow after Streamlit renders ── */
        const obs = new MutationObserver(() => applyMouseGlow());
        obs.observe(document.body, { childList: true, subtree: true });
        setTimeout(() => applyMouseGlow(), 800);

    })();
    </script>
    """, unsafe_allow_html=True)


def render_sidebar_brand():
    """Gradient brand block matching reference dashboard."""
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="9" fill="url(#nb)"/>
            <defs>
                <linearGradient id="nb" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stop-color="#7c4dff"/>
                    <stop offset="100%" stop-color="#00d4ff"/>
                </linearGradient>
            </defs>
            <circle cx="16" cy="13" r="4.5" stroke="white" stroke-width="1.75"/>
            <path d="M8 27c0-4.418 3.582-8 8-8s8 3.582 8 8" stroke="rgba(255,255,255,0.7)" stroke-width="1.75" stroke-linecap="round"/>
            <circle cx="24" cy="9" r="2.5" fill="#00e5a0"/>
        </svg>
        <div>
            <div class="sidebar-brand-text">Sitapur PNG</div>
            <div class="sidebar-brand-sub">BPCL &middot; Field Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = ""):
    """Nova page header — large bold animated gradient title."""
    sub_html = (
        f'<p style="margin:0.5rem 0 0;font-size:0.9rem;color:#6666aa;font-weight:400;'
        f'letter-spacing:0.01em">{subtitle}</p>'
    ) if subtitle else ""
    st.markdown(f"""
    <div style="margin-bottom:2rem;padding-bottom:1.75rem;position:relative">
        <h1 style="margin:0;font-size:2.4rem;font-weight:800;letter-spacing:-0.04em;
                   line-height:1.1;
                   background:linear-gradient(100deg,#ffffff 0%,#00d4ff 45%,#7c4dff 80%,#e040fb 100%);
                   background-size:200% 100%;
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   background-clip:text;
                   filter:drop-shadow(0 0 22px rgba(0,212,255,0.30))">{title}</h1>
        {sub_html}
        <div style="margin-top:1.25rem;height:1px;
                    background:linear-gradient(90deg,transparent 0%,rgba(0,212,255,0.7) 20%,rgba(124,77,255,0.9) 50%,rgba(224,64,251,0.7) 80%,transparent 100%);
                    box-shadow:0 0 14px rgba(0,212,255,0.35),0 0 28px rgba(124,77,255,0.20);"></div>
    </div>
    """, unsafe_allow_html=True)


def apply_plotly_theme(fig, title: str = None, height: int = None):
    """Nova dark plotly theme — navy bg, neon grid, glowing lines."""
    updates = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", size=11, color="#44445a"),
        margin=dict(r=20, t=44 if title else 20, l=20, b=20),
        legend=dict(
            bgcolor="rgba(24,24,48,0.90)",
            bordercolor="rgba(255,255,255,0.07)",
            borderwidth=1,
            font=dict(size=11, color="#8888aa"),
            x=0.01, y=0.99,
        ),
        hoverlabel=dict(
            bgcolor="#1e1e38",
            bordercolor="rgba(0,212,255,0.25)",
            font=dict(family="Inter, sans-serif", size=11, color="#f0f0ff"),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            linecolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=10, color="#44445a"),
            ticklen=0,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            linecolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=10, color="#44445a"),
            ticklen=0,
        ),
    )
    if title:
        updates["title"] = dict(
            text=title,
            font=dict(size=13, color="#8888aa", family="Inter, sans-serif"),
            x=0, xanchor="left",
            pad=dict(l=4)
        )
    if height:
        updates["height"] = height
    fig.update_layout(**updates)
    return fig


# ── Colour palettes ──

MRU_COLORS_PREMIUM = {
    "MRU-1":      "#0071e3",   # Blue
    "MRU-2":      "#ff9f0a",   # Orange
    "MRU-5":      "#bf5af2",   # Purple
    "MRU-6":      "#ff453a",   # Red
    "MRU-7":      "#00c8ff",   # Cyan
    "Unassigned": "#aeaeb2",   # Gray
}

PRIORITY_COLOR_PREMIUM = {
    "\U0001f680 Quick Win":  "#0071e3",
    "\U0001f48e High Value": "#ff9f0a",
    "\u26a1 Maintain":       "#bf5af2",
    "\U0001f501 Review":     "#aeaeb2",
}

CHARGED_COLOR_PREMIUM = "#30d158"   # Green — exclusive to charged dots

CHART_PALETTE = [
    "#00d4ff",  # cyan      — primary
    "#e040fb",  # magenta
    "#00e5a0",  # green
    "#ffb340",  # amber
    "#a57fff",  # violet
    "#ff4d6a",  # red
    "#00e5cc",  # teal
    "#ff8c66",  # orange
]
