"""
config.py
=========
Central configuration for the Sitapur PNG dashboard.

This version uses the updated root CSV files as the source of truth:
- Connection-Data.csv
- AREAs.csv
- MRUs.csv
- Conversion-Data.csv

The old db_min / centroid-based territory mapping is no longer used.
"""

import streamlit as st

from premium_theme import CHARGED_COLOR_PREMIUM

# ── GitHub Database Settings ─────────────────────────────────────────────────────
GITHUB_OWNER = "darksoul0379"
GITHUB_REPO  = "BPCL_PNG_Model_Sitapur"
BRANCH       = "main"
try:
    GITHUB_TOKEN: str = st.secrets.get("GITHUB_TOKEN", "")
except Exception:
    GITHUB_TOKEN = ""

CONNECTION_FILE = "Connection-Data.csv"
MASTER_FILE     = "Conversion-Data.csv"

GH_HEADERS: dict = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

# ── GitHub portal CSV column schemas ────────────────────────────────────────────
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

# ── Root CSV files used by the dashboard ─────────────────────────────────────────
ROOT_CONNECTIONS_FILE = "Connection-Data.csv"
ROOT_AREAS_FILE       = "AREAs.csv"
ROOT_MRUS_FILE        = "MRUs.csv"
ROOT_CONVERSIONS_FILE = "Conversion-Data.csv"

# ── Coordinate sanity guards ─────────────────────────────────────────────────────
SITAPUR_BBOX = {
    "lat_min": 27.45,
    "lat_max": 27.68,
    "lon_min": 80.58,
    "lon_max": 80.78,
}

ERROR_ZONES = [
    (0.0, 0.0, 1000),
]

# ── Colors ──────────────────────────────────────────────────────────────────────
MRU_COLORS: dict[str, str] = {
    "MRU-1": "#00BFFF",
    "MRU-2": "#FFA500",
    "MRU-3": "#FF5C5C",
    "MRU-4": "#8A5CF6",
    "MRU-5": "#B04FFF",
    "MRU-6": "#FF69B4",
    "MRU-7": "#FFD700",
    "MRU-8": "#00E5CC",
    "MRU-9": "#FF6B35",
    "Unassigned": "#9AA0A6",
}

CHARGED_COLOR: str = CHARGED_COLOR_PREMIUM
UNCHARGED_GREY: str = "#9AA0A6"
