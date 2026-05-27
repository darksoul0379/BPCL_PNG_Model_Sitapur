"""
github_db.py
============
GitHub CSV database layer for the Sitapur PNG dashboard.

The app's "database" is two CSV files stored on a GitHub branch.
This module handles ALL network calls to read and write those files.

Functions
---------
github_get_file(path)
    Fetch a raw file from the GitHub Contents API.
    Returns (bytes, sha, error_str).
    Cached for 60 s so rapid Streamlit reruns don't hammer the API.

github_put_file(path, file_bytes, sha, commit_message)
    Write or update a file on GitHub via the Contents API.
    Returns (success: bool, response_data: dict).
    NOT cached — every write must hit the network.

read_csv_github(path, expected_cols)
    High-level: fetch a CSV from GitHub, parse it, normalise column names,
    fill missing columns with empty strings, and return (df, sha, error).
    Cached for 60 s.

write_csv_bytes(df)
    Serialise a DataFrame to UTF-8 CSV bytes ready for github_put_file().

normalize_meter(series)
    Normalise a meter-number Series to lowercase alphanumeric only.
    Used for duplicate detection and fuzzy lookup.

lookup_connection_row(df, meter_no)
    Find a single connection row by exact normalised meter number.
    Returns a dict or None.
    Cached for 300 s.

Design notes
------------
- github_get_file falls back to download_url when the base64 payload is
  truncated (GitHub silently truncates files > ~1 MB in the Contents API).
- write_csv_bytes uses StringIO so no temporary files are created on disk.
- normalize_meter strips whitespace, lowercases, and removes non-alphanumeric
  characters, making "RR-2401", "rr2401", and " RR2401 " all match.
"""

import base64
import io

import pandas as pd
import requests
import streamlit as st

from config import (
    GITHUB_OWNER,
    GITHUB_REPO,
    BRANCH,
    GITHUB_TOKEN,
    GH_HEADERS,
    CONNECTION_FILE_COLUMNS,
)


# ── Low-level GitHub file fetch ──────────────────────────────────────────────────

@st.cache_data(ttl=60)
def github_get_file(path: str) -> tuple:
    """
    Fetch a single file from the GitHub repo Contents API.

    Parameters
    ----------
    path : Repo-relative file path (e.g. "connections.csv").

    Returns
    -------
    (content: bytes | None, sha: str | None, error: str | None)
    On success, error is None. On failure, content and sha are None.

    Notes
    -----
    Falls back to download_url when the base64 payload size doesn't match
    the declared file size — GitHub silently truncates files > ~1 MB.
    Cached for 60 s to limit API rate usage during rapid Streamlit reruns.
    """
    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/contents/{path}?ref={BRANCH}"
    )
    try:
        response = requests.get(url, headers=GH_HEADERS, timeout=30)
    except Exception as ex:
        return None, None, f"Request failed: {ex}"

    if response.status_code != 200:
        return None, None, (
            f"GitHub API returned {response.status_code}: {response.text[:200]}"
        )

    data          = response.json()
    content_b64   = data.get("content", "")
    expected_size = data.get("size", 0)
    download_url  = data.get("download_url")

    try:
        content = base64.b64decode(content_b64) if content_b64 else b""
    except Exception as ex:
        return None, None, f"Base64 decode failed: {ex}"

    # Fallback: download full file when API silently truncated it
    if expected_size and len(content) != expected_size and download_url:
        raw_headers = (
            {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        )
        try:
            raw_response = requests.get(download_url, headers=raw_headers, timeout=30)
        except Exception as ex:
            return None, None, f"Download URL request failed: {ex}"

        if raw_response.status_code == 200:
            content = raw_response.content
        else:
            return None, None, (
                f"Download URL returned {raw_response.status_code}: "
                f"{raw_response.text[:200]}"
            )

    return content, data["sha"], None


# ── Low-level GitHub file write ──────────────────────────────────────────────────

def github_put_file(
    path: str,
    file_bytes: bytes,
    sha: str | None,
    commit_message: str,
) -> tuple[bool, dict]:
    """
    Create or update a file on the GitHub repo branch.

    Parameters
    ----------
    path           : Repo-relative file path (e.g. "connections.csv").
    file_bytes     : Raw UTF-8 bytes to write.
    sha            : Current file SHA from github_get_file(). Required for updates;
                     pass None only when creating a brand-new file.
    commit_message : Git commit message string.

    Returns
    -------
    (success: bool, response_data: dict)
    success is True for HTTP 200 (update) or 201 (create).
    """
    url     = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    )
    payload: dict = {
        "message": commit_message,
        "content": base64.b64encode(file_bytes).decode("utf-8"),
        "branch":  BRANCH,
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=GH_HEADERS, json=payload, timeout=30)
    try:
        data = response.json()
    except Exception:
        data = {"message": "Unknown response"}

    return response.status_code in (200, 201), data


# ── High-level CSV read helper ───────────────────────────────────────────────────

@st.cache_data(ttl=60)
def read_csv_github(path: str, expected_cols: list) -> tuple:
    """
    Fetch a CSV from GitHub, parse it, normalise column names, and return a
    clean DataFrame.

    Column normalisation handles common alias names so the app works even if
    the CSV was manually edited with slightly different header names.

    Parameters
    ----------
    path          : Repo-relative CSV path.
    expected_cols : List of canonical column names (from config.py).

    Returns
    -------
    (df: pd.DataFrame, sha: str | None, error: str | None)
    On error, df is an empty DataFrame with expected_cols as columns.
    """
    file_bytes, sha, error = github_get_file(path)
    if file_bytes is None:
        return (
            pd.DataFrame(columns=expected_cols),
            None,
            error or "Unknown GitHub read error",
        )

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as ex:
        return pd.DataFrame(columns=expected_cols), sha, f"CSV parse failed: {ex}"

    # Strip whitespace from all column headers
    df.columns = [str(col).strip() for col in df.columns]

    # Alias map — canonical name → list of alternate names the CSV might use
    _ALIASES: dict[str, list[str]] = {
        "METER NO":        ["meter_no"],
        "NAME":            ["customer_name"],
        "MOB NO":          ["mobile_no"],
        "Latitude":        ["latitude"],
        "Longitude":       ["longitude"],
        "METER INLET GI":  ["meter_inlet_gi"],
        "METER OUTLET GI": ["meter_outlet_gi"],
        "TOTAL GI":        ["total_gi"],
        "Meter Number":    ["meter_no", "meter_number"],
        "Customer Name":   ["customer_name"],
        "Mobile NUMBER":   ["mobile_no", "mobile_number"],
        "Conversion Date": ["conversion_date"],
    }
    for target_col, aliases in _ALIASES.items():
        if target_col not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df[target_col] = df[alias]
                    break

    # Ensure every expected column exists (fill with empty string if absent)
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    # Fill NaN with empty string for all object columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("")

    # Reorder: expected columns first, extras at the end
    ordered = [c for c in expected_cols if c in df.columns]
    extras  = [c for c in df.columns if c not in expected_cols]
    return df[ordered + extras], sha, None


# ── CSV serialisation helper ─────────────────────────────────────────────────────

def write_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Serialise a DataFrame to UTF-8 CSV bytes with no row index.
    Used before every github_put_file() call.
    """
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


# ── Meter number normalisation ───────────────────────────────────────────────────

def normalize_meter(series: pd.Series) -> pd.Series:
    """
    Normalise a meter-number Series for comparison.

    Strips whitespace, lowercases, and removes all non-alphanumeric characters
    so that "RR-2401", " rr2401 ", and "RR2401" all compare equal.
    Used for duplicate detection and fuzzy lookup in the portal forms.
    """
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]", "", regex=True)
    )


# ── Connection row lookup ────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def lookup_connection_row(df: pd.DataFrame, meter_no: str) -> dict | None:
    """
    Find a single connection row by exact normalised meter number.

    Parameters
    ----------
    df       : Connections DataFrame (from read_csv_github or load_connection_data).
    meter_no : Raw meter number string as typed by the user.

    Returns
    -------
    A dict of {column: value} for the matched row, or None if not found.
    Cached for 300 s so repeated lookups within the same session are instant.
    """
    if df is None or df.empty or not meter_no:
        return None
    key     = normalize_meter(pd.Series([meter_no])).iloc[0]
    matches = df[normalize_meter(df["METER NO"]) == key]
    return matches.iloc[0].to_dict() if not matches.empty else None
