"""
portal_tabs.py
==============
Data-entry portal tabs for the Sitapur PNG dashboard.

Functions
---------
render_new_connection_tab()
    "➕ New Connection" tab — form to add a new meter record to
    connections.csv on GitHub.

render_converted_tab()
    "⚡ Converted" tab — meter lookup + form to record a gas conversion,
    writing a new row to conversions.csv on GitHub.

Both functions
  - Read the current CSV from GitHub (cached 60 s) to check for duplicates.
  - Write back to GitHub on successful form submission.
  - Show success / error feedback and a balloons animation on success.

Dependencies: github_db.py for all network calls; config.py for file paths.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from config import CONNECTION_FILE, MASTER_FILE, CONNECTION_FILE_COLUMNS, MASTER_FILE_COLUMNS
from github_db import (
    read_csv_github,
    github_put_file,
    write_csv_bytes,
    normalize_meter,
    lookup_connection_row,
)


def render_new_connection_tab() -> None:
    """
    Render the "Add New Connection" form.

    Reads connections.csv from GitHub, validates for duplicate meter numbers,
    appends the new row, and commits the updated CSV back to GitHub.
    Shows st.success + st.balloons on success, st.error on failure.
    """
    st.caption("Connected to GitHub CSV file: `connections.csv`")

    conn_df, conn_sha, conn_error = read_csv_github(
        CONNECTION_FILE, CONNECTION_FILE_COLUMNS
    )
    if conn_error:
        st.warning(f"connections.csv read issue: {conn_error}")

    st.markdown("### Add New Connection")

    with st.form("new_connection_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        meter_no  = c1.text_input("Meter No *",      placeholder="e.g. RR2401")
        cust_name = c2.text_input("Customer Name *",  placeholder="Full name")

        c3, c4 = st.columns(2)
        phone_no  = c3.text_input("Mobile No *",      placeholder="+91 98XXXXXXXX")
        total_gi  = c4.text_input("Total GI",         placeholder="Auto or manual")

        c5, c6 = st.columns(2)
        lat       = c5.text_input("Latitude",         placeholder="27.XXXX")
        long_val  = c6.text_input("Longitude",        placeholder="80.XXXX")

        c7, c8 = st.columns(2)
        inlet_gi  = c7.text_input("Meter Inlet GI",  placeholder="0")
        outlet_gi = c8.text_input("Meter Outlet GI", placeholder="0")

        submitted = st.form_submit_button("Save New Connection", use_container_width=True)

    if not submitted:
        return

    # ── Validate required fields ──────────────────────────────────────────────────
    if not meter_no or not cust_name or not phone_no:
        st.error("Meter No, Customer Name, and Mobile No are required.")
        return

    # ── Duplicate check ───────────────────────────────────────────────────────────
    existing = (
        normalize_meter(conn_df["METER NO"])
        if not conn_df.empty
        else pd.Series(dtype=str)
    )
    if meter_no.strip().lower() in existing.values:
        st.warning(f"Meter `{meter_no}` already exists in connections.csv.")
        return

    # ── Build new row and commit ──────────────────────────────────────────────────
    new_row = {
        "METER NO":        meter_no.strip(),
        "NAME":            cust_name.strip(),
        "MOB NO":          phone_no.strip(),
        "Latitude":        lat.strip(),
        "Longitude":       long_val.strip(),
        "METER INLET GI":  inlet_gi.strip(),
        "METER OUTLET GI": outlet_gi.strip(),
        "TOTAL GI":        total_gi.strip(),
    }
    updated_df = pd.concat(
        [conn_df, pd.DataFrame([new_row])], ignore_index=True
    )
    ok, resp = github_put_file(
        CONNECTION_FILE,
        write_csv_bytes(updated_df),
        conn_sha,
        f"[portal] add connection {meter_no} · {datetime.now():%Y-%m-%d %H:%M}",
    )
    if ok:
        st.success(f"Meter **{meter_no}** added successfully and committed to GitHub.")
        st.balloons()
    else:
        st.error(f"GitHub write error: {resp.get('message', 'Unknown error')}")


def render_converted_tab() -> None:
    """
    Render the "Add Converted Connection" form.

    - User types a meter number; the app looks it up in connections.csv to
      auto-fill customer name, lat, and lon.
    - Shows fuzzy suggestions if the exact meter is not found.
    - On submission, appends a row to conversions.csv on GitHub.
    - Duplicate conversions (same meter already in conversions.csv) are rejected.
    """
    st.caption(
        "Connected to GitHub CSV files: `connections.csv` and `conversions.csv`"
    )

    conn_df, _conn_sha, conn_error = read_csv_github(
        CONNECTION_FILE, CONNECTION_FILE_COLUMNS
    )
    # Conversion-Data.csv actual schema: "Meter No." and "Date" only
    CONV_COLS = ["Meter No.", "Date"]
    master_df, master_sha, master_error = read_csv_github(
        MASTER_FILE, CONV_COLS
    )
    if conn_error:
        st.warning(f"connections.csv read issue: {conn_error}")
    if master_error:
        st.warning(f"conversions.csv read issue: {master_error}")

    st.markdown("### Add Converted Connection")

    # ── Meter lookup ──────────────────────────────────────────────────────────────
    lookup_meter   = st.text_input(
        "Enter Meter No", placeholder="RR2401", key="conv_lookup_meter"
    )
    cleaned_lookup = lookup_meter.strip()

    auto_data:   dict | None = None
    found:       bool        = False
    suggestions: list[str]   = []

    if cleaned_lookup:
        # Exact normalised match first
        auto_data = lookup_connection_row(conn_df, cleaned_lookup)

        # Fuzzy / partial match if exact fails
        if auto_data is None and not conn_df.empty:
            norm_series  = normalize_meter(conn_df["METER NO"])
            norm_lookup  = normalize_meter(pd.Series([cleaned_lookup])).iloc[0]

            # Try exact-after-normalise
            partial_mask = norm_series == norm_lookup
            if not partial_mask.any():
                # Try contains / startswith
                partial_mask = (
                    norm_series.str.contains(norm_lookup, na=False) |
                    norm_series.str.startswith(norm_lookup, na=False)
                )

            if partial_mask.any():
                auto_data   = conn_df[partial_mask].iloc[0].to_dict()
                suggestions = conn_df.loc[partial_mask, "METER NO"].astype(str).head(5).tolist()
            else:
                # Broader hint: first 6 chars of the normalised query
                prefix    = norm_lookup[:6] if len(norm_lookup) >= 6 else norm_lookup
                hint_mask = norm_series.str.contains(prefix, na=False)
                if hint_mask.any():
                    suggestions = conn_df.loc[hint_mask, "METER NO"].astype(str).head(5).tolist()

        found = auto_data is not None

    # ── Show lookup result ────────────────────────────────────────────────────────
    if cleaned_lookup:
        if found:
            m1, m2, m3 = st.columns(3)
            m1.metric("Customer",  auto_data.get("NAME",      "—"))
            m2.metric("Latitude",  auto_data.get("Latitude",  "—"))
            m3.metric("Longitude", auto_data.get("Longitude", "—"))
            st.success("Meter found. Details auto-filled from connection data.")
        else:
            st.warning("Meter not found in connection data. You can still enter values manually.")
            if suggestions:
                st.caption("Closest matches found: " + ", ".join(suggestions))

    # ── Conversion entry form ─────────────────────────────────────────────────────
    with st.form("converted_connection_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        ch_meter = c1.text_input(
            "Meter No *",
            value=auto_data.get("METER NO", lookup_meter) if found else lookup_meter,
        )
        conversion_date = c2.date_input("Conversion Date", format="DD/MM/YYYY")
        submit_charge = st.form_submit_button(
            "Save Converted Entry", use_container_width=True
        )

    if not submit_charge:
        return

    if not ch_meter.strip():
        st.error("Meter No is required.")
        return

    # ── Duplicate check in conversions ───────────────────────────────────────────
    existing = (
        normalize_meter(master_df["Meter No."])
        if not master_df.empty
        else pd.Series(dtype=str)
    )
    if ch_meter.strip().lower() in existing.values:
        st.warning(f"Meter `{ch_meter}` already exists in conversions.csv.")
        return

    # Write only the 2 columns that match the actual CSV schema
    new_row = {
        "Meter No.": ch_meter.strip(),
        "Date":      conversion_date.strftime("%d/%m/%Y"),
    }
    updated_df = pd.concat(
        [master_df, pd.DataFrame([new_row])], ignore_index=True
    )
    ok, resp = github_put_file(
        MASTER_FILE,
        write_csv_bytes(updated_df),
        master_sha,
        f"[portal] add converted connection {ch_meter} · {datetime.now():%Y-%m-%d %H:%M}",
    )
    if ok:
        st.success(
            f"Converted entry for **{ch_meter}** saved successfully and committed to GitHub."
        )
        st.balloons()
    else:
        st.error(f"GitHub write error: {resp.get('message', 'Unknown error')}")
