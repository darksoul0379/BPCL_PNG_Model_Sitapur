import base64
import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="BPCL Sitapur | PNG Portal",
    page_icon="🔵",
    layout="centered",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #f4f7fb;
    --surface: #ffffff;
    --surface-soft: #f8fafc;
    --border: #e5eaf0;
    --text: #14213d;
    --muted: #6b7280;
    --primary: #0a3d62;
    --primary-hover: #0c4f80;
    --success-bg: #e8f5e9;
    --success-text: #2e7d32;
    --radius: 14px;
    --shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(10, 61, 98, 0.05), transparent 30%),
        linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
}

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 980px;
}

.portal-header {
    background: linear-gradient(135deg, #0a3d62 0%, #114d78 100%);
    color: white;
    border-radius: 18px;
    padding: 22px 24px;
    margin-bottom: 22px;
    box-shadow: 0 18px 40px rgba(10, 61, 98, 0.20);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.portal-header-top {
    display: flex;
    align-items: center;
    gap: 14px;
}

.portal-logo {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    background: rgba(255, 255, 255, 0.12);
    font-size: 1.4rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.14);
}

.portal-title {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.portal-subtitle {
    margin-top: 3px;
    font-size: 0.86rem;
    opacity: 0.82;
}

.info-strip {
    margin-top: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.info-chip {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.10);
}

.block-card {
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    padding: 20px 22px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}

.block-label {
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eef2f6;
}

.autofill-pill {
    display: inline-block;
    background: var(--success-bg);
    color: var(--success-text);
    font-size: 0.68rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 999px;
    margin-left: 8px;
    vertical-align: middle;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] input {
    border-radius: 10px !important;
    border: 1px solid #dbe3eb !important;
    font-size: 0.92rem !important;
    background: var(--surface-soft) !important;
    min-height: 44px !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stDateInput"] input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(10, 61, 98, 0.12) !important;
}

.stButton > button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    background: var(--primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.62rem 1.2rem !important;
    transition: all 0.18s ease !important;
    min-height: 46px !important;
}

.stButton > button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--primary-hover) !important;
    transform: translateY(-1px);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #edf2f7;
    border-radius: 12px;
    padding: 5px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 8px 16px !important;
    color: #475467 !important;
}

.stTabs [aria-selected="true"] {
    background: white !important;
    color: var(--primary) !important;
    font-weight: 800 !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
}

div[data-testid="metric-container"] {
    background: var(--surface-soft);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 14px;
    box-shadow: none;
}

.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
}

div[data-baseweb="radio"] > div {
    gap: 14px;
}

@media (max-width: 640px) {
    .portal-header {
        padding: 18px;
    }

    .portal-title {
        font-size: 1.05rem;
    }

    .portal-subtitle {
        font-size: 0.8rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="portal-header">
    <div class="portal-header-top">
        <div class="portal-logo">🔵</div>
        <div>
            <h1 class="portal-title">BPCL Sitapur · PNG Portal</h1>
            <div class="portal-subtitle">Excel-backed connection workflow for new entries, charged entries, and records</div>
        </div>
    </div>
    <div class="info-strip">
        <div class="info-chip">New Connections</div>
        <div class="info-chip">Charged Connections</div>
        <div class="info-chip">GitHub Sync</div>
        <div class="info-chip">Excel Records</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Hardcode your values here
GITHUB_TOKEN = "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"
GITHUB_OWNER = "darksoul0379"
GITHUB_REPO = "BPCL_PNG_Model_Sitapur"
BRANCH = "main"

CONNECTION_FILE = "Connection-Data.xlsx"
MASTER_FILE = "Master-Data.xlsx"

GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

CONNECTION_FILE_COLUMNS = [
    "METER NO",
    "NAME",
    "MOB NO",
    "Latitude",
    "Longitude",
    "METER INLET GI",
    "METER OUTLET GI",
    "TOTAL GI",
]

MASTER_FILE_COLUMNS = [
    "Meter Number",
    "Customer Name",
    "Mobile NUMBER",
    "Conversion Date",
    "Latitude",
    "Longitude",
]

if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
    st.error("Missing GitHub configuration. Add token, owner, repo, and branch values in the code.")
    st.stop()


def github_get_file(path):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}?ref={BRANCH}"
    response = requests.get(url, headers=GH_HEADERS, timeout=30)

    if response.status_code == 200:
        data = response.json()
        content_b64 = data.get("content", "")
        expected_size = data.get("size", 0)
        download_url = data.get("download_url")

        try:
            content = base64.b64decode(content_b64) if content_b64 else b""
        except Exception:
            return None, None

        if expected_size and len(content) != expected_size and download_url:
            raw_headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            raw_response = requests.get(download_url, headers=raw_headers, timeout=30)
            if raw_response.status_code == 200:
                content = raw_response.content
            else:
                return None, None

        return content, data["sha"]

    return None, None


def github_put_file(path, file_bytes, sha, commit_message):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    encoded = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=GH_HEADERS, json=payload, timeout=30)

    try:
        data = response.json()
    except Exception:
        data = {"message": "Unknown response"}

    return response.status_code in (200, 201), data


def read_excel_with_sheet(path, expected_cols):
    file_bytes, sha = github_get_file(path)
    if file_bytes is None:
        return pd.DataFrame(columns=expected_cols), None, "Sheet1"

    excel_buffer = io.BytesIO(file_bytes)

    try:
        workbook = pd.ExcelFile(excel_buffer, engine="openpyxl")
        sheet_name = workbook.sheet_names[0]
        excel_buffer.seek(0)
        df = pd.read_excel(excel_buffer, sheet_name=sheet_name, engine="openpyxl")
    except Exception:
        return pd.DataFrame(columns=expected_cols), sha, "Sheet1"

    df.columns = [str(col).strip() for col in df.columns]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("")

    ordered_cols = [col for col in expected_cols if col in df.columns]
    extra_cols = [col for col in df.columns if col not in expected_cols]
    df = df[ordered_cols + extra_cols]

    return df, sha, sheet_name


def write_excel_bytes(df, sheet_name):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output.getvalue()


def normalize_meter(series):
    return series.astype(str).str.strip().str.lower()


def lookup_connection_row(df, meter_no):
    if df.empty or not meter_no:
        return None

    matches = df[normalize_meter(df["METER NO"]) == meter_no.strip().lower()]
    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


st.caption("Connected to GitHub Excel files: `Connection-Data.xlsx` and `Master-Data.xlsx`")

conn_df, conn_sha, conn_sheet = read_excel_with_sheet(CONNECTION_FILE, CONNECTION_FILE_COLUMNS)
master_df, master_sha, master_sheet = read_excel_with_sheet(MASTER_FILE, MASTER_FILE_COLUMNS)

tab1, tab2, tab3 = st.tabs(["➕ New Connection", "⚡ Charged Connection", "📋 View Records"])

with tab1:
    st.markdown(
        '<div class="block-card"><div class="block-label">New Connection Details</div>',
        unsafe_allow_html=True,
    )

    with st.form("new_connection_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        meter_no = c1.text_input("Meter No *", placeholder="e.g. RR2401")
        cust_name = c2.text_input("Customer Name *", placeholder="Full name")

        c3, c4 = st.columns(2)
        phone_no = c3.text_input("Mobile No *", placeholder="+91 98XXXXXXXX")
        total_gi = c4.text_input("Total GI", placeholder="Auto or manual")

        c5, c6 = st.columns(2)
        lat = c5.text_input("Latitude", placeholder="27.XXXX")
        long_val = c6.text_input("Longitude", placeholder="80.XXXX")

        c7, c8 = st.columns(2)
        inlet_gi = c7.text_input("Meter Inlet GI", placeholder="0")
        outlet_gi = c8.text_input("Meter Outlet GI", placeholder="0")

        submitted = st.form_submit_button("Save New Connection", use_container_width=True)

    if submitted:
        if not meter_no or not cust_name or not phone_no:
            st.error("Meter No, Customer Name, and Mobile No are required.")
        else:
            existing = normalize_meter(conn_df["METER NO"]) if not conn_df.empty else pd.Series(dtype=str)
            meter_key = meter_no.strip().lower()

            if meter_key in existing.values:
                st.warning(f"Meter `{meter_no}` already exists in `{CONNECTION_FILE}`.")
            else:
                new_row = {
                    "METER NO": meter_no.strip(),
                    "NAME": cust_name.strip(),
                    "MOB NO": phone_no.strip(),
                    "Latitude": lat.strip(),
                    "Longitude": long_val.strip(),
                    "METER INLET GI": inlet_gi.strip(),
                    "METER OUTLET GI": outlet_gi.strip(),
                    "TOTAL GI": total_gi.strip(),
                }

                updated_df = pd.concat([conn_df, pd.DataFrame([new_row])], ignore_index=True)
                file_bytes = write_excel_bytes(updated_df, conn_sheet)

                ok, resp = github_put_file(
                    CONNECTION_FILE,
                    file_bytes,
                    conn_sha,
                    f"[portal] add connection {meter_no} · {datetime.now():%Y-%m-%d %H:%M}",
                )

                if ok:
                    st.success(f"Meter **{meter_no}** added successfully and committed to GitHub.")
                    st.balloons()
                else:
                    st.error(f"GitHub write error: {resp.get('message', 'Unknown error')}")

    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown(
        '<div class="block-card"><div class="block-label">Lookup Meter</div>',
        unsafe_allow_html=True,
    )

    lookup_meter = st.text_input(
        "Enter Meter No",
        placeholder="RR2401",
        key="lookup_meter",
        label_visibility="collapsed",
    )

    auto_data = lookup_connection_row(conn_df, lookup_meter)
    found = auto_data is not None

    if lookup_meter.strip():
        if found:
            m1, m2, m3 = st.columns(3)
            m1.metric("Customer", auto_data.get("NAME", "—"))
            m2.metric("Latitude", auto_data.get("Latitude", "—"))
            m3.metric("Longitude", auto_data.get("Longitude", "—"))
            st.success("Meter found. Details auto-filled from connection data.")
        else:
            st.warning("Meter not found in connection data. You can still enter values manually.")

    st.markdown("</div>", unsafe_allow_html=True)

    badge = '<span class="autofill-pill">auto-filled</span>' if found else ""
    st.markdown(
        f'<div class="block-card"><div class="block-label">Charge Entry {badge}</div>',
        unsafe_allow_html=True,
    )

    with st.form("charged_connection_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        ch_meter = c1.text_input("Meter No *", value=auto_data.get("METER NO", lookup_meter) if found else lookup_meter)
        ch_name = c2.text_input("Customer Name", value=auto_data.get("NAME", "") if found else "")

        c3, c4 = st.columns(2)
        ch_phone = c3.text_input("Mobile No", value=str(auto_data.get("MOB NO", "")) if found else "")
        conversion_date = c4.date_input("Conversion Date", format="DD/MM/YYYY")

        c5, c6 = st.columns(2)
        ch_lat = c5.text_input("Latitude", value=str(auto_data.get("Latitude", "")) if found else "", disabled=found)
        ch_long = c6.text_input("Longitude", value=str(auto_data.get("Longitude", "")) if found else "", disabled=found)

        submit_charge = st.form_submit_button("Save Charge Entry", use_container_width=True)

    if submit_charge:
        final_meter = ch_meter.strip()

        if not final_meter:
            st.error("Meter No is required.")
        else:
            final_lat = str(auto_data.get("Latitude", ch_lat)).strip() if found else ch_lat.strip()
            final_long = str(auto_data.get("Longitude", ch_long)).strip() if found else ch_long.strip()
            final_name = ch_name.strip() if ch_name else (str(auto_data.get("NAME", "")).strip() if found else "")
            final_phone = ch_phone.strip() if ch_phone else (str(auto_data.get("MOB NO", "")).strip() if found else "")

            new_charge = {
                "Meter Number": final_meter,
                "Customer Name": final_name,
                "Mobile NUMBER": final_phone,
                "Conversion Date": conversion_date.strftime("%d/%m/%Y") if conversion_date else "",
                "Latitude": final_lat,
                "Longitude": final_long,
            }

            updated_master = pd.concat([master_df, pd.DataFrame([new_charge])], ignore_index=True)
            file_bytes = write_excel_bytes(updated_master, master_sheet)

            ok, resp = github_put_file(
                MASTER_FILE,
                file_bytes,
                master_sha,
                f"[portal] charge {final_meter} · {datetime.now():%Y-%m-%d %H:%M}",
            )

            if ok:
                st.success(f"Charge entry for **{final_meter}** added successfully and committed to GitHub.")
                st.balloons()
            else:
                st.error(f"GitHub write error: {resp.get('message', 'Unknown error')}")

    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown(
        '<div class="block-card"><div class="block-label">Records</div>',
        unsafe_allow_html=True,
    )

    dataset = st.radio(
        "Dataset",
        ["Connection Data", "Master Data"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if dataset == "Connection Data":
        df_view = conn_df.copy()
        download_name = CONNECTION_FILE
        meter_col = "METER NO"
        name_col = "NAME"
    else:
        df_view = master_df.copy()
        download_name = MASTER_FILE
        meter_col = "Meter Number"
        name_col = "Customer Name"

    if not df_view.empty:
        s1, s2 = st.columns([3, 1])
        query = s1.text_input(
            "Search by Meter No or Name",
            placeholder="Type to filter records...",
            label_visibility="collapsed",
        )
        s2.metric("Total", len(df_view))

        if query:
            df_view = df_view[
                df_view[meter_col].astype(str).str.contains(query, case=False, na=False)
                | df_view[name_col].astype(str).str.contains(query, case=False, na=False)
            ]

        st.dataframe(df_view, use_container_width=True, height=420)

        st.download_button(
            "⬇️ Download current view as Excel",
            data=write_excel_bytes(df_view, "Data"),
            file_name=download_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("No records found yet.")

    st.markdown("</div>", unsafe_allow_html=True)
