"""
data_loader.py
==============
Primary data loading layer for the Sitapur PNG dashboard.

CSV structure (actual):
  Connection-Data.csv : METER NO, NAME, MOB NO, Latitude, Longitude,
                        METER INLET GI, METER OUTLET GI, TOTAL GI, Area
  AREAs.csv           : AREA, MRU (integer 1-9), STATUS (CHARGED/UNCHARGED)
  MRUs.csv            : MRU (integer 1-9), MRU NAME
  Conversion-Data.csv : Meter No., Date  (mixed DD/MM/YY and DD.MM.YYYY formats)

There is no Subarea level — Area is the only geographic grouping below MRU.
Subarea is kept as an alias for Main_Area throughout so the rest of the app works.
"""

from __future__ import annotations

import math
import pandas as pd
import streamlit as st

from config import (
    ROOT_AREAS_FILE,
    ROOT_CONNECTIONS_FILE,
    ROOT_CONVERSIONS_FILE,
    ROOT_MRUS_FILE,
    SITAPUR_BBOX,
    ERROR_ZONES,
)


def _clean(s: pd.Series) -> pd.Series:
    """Strip BOM, whitespace, normalise to str."""
    return s.fillna("").astype(str).str.replace("\ufeff", "", regex=False).str.strip()


def _norm_key(s: pd.Series) -> pd.Series:
    """Upper-case + collapse internal whitespace for join keys."""
    return _clean(s).str.upper().str.replace(r"\s+", " ", regex=True)


def _in_bbox(lat: float, lon: float) -> bool:
    if pd.isna(lat) or pd.isna(lon):
        return False
    return (
        SITAPUR_BBOX["lat_min"] <= lat <= SITAPUR_BBOX["lat_max"]
        and SITAPUR_BBOX["lon_min"] <= lon <= SITAPUR_BBOX["lon_max"]
    )


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _not_error_coord(lat: float, lon: float) -> bool:
    if pd.isna(lat) or pd.isna(lon):
        return False
    return all(_haversine_m(lat, lon, elat, elon) >= erad for elat, elon, erad in ERROR_ZONES)


def _parse_mixed_dates(series: pd.Series) -> pd.Series:
    """
    Parse mixed date formats in a single column:
      DD/MM/YY   → 20/12/25
      DD/MM/YYYY → 20/12/2025
      DD.MM.YYYY → 26.05.2026
      DD.MM.YY   → 26.05.26
    """
    result = pd.Series([pd.NaT] * len(series), index=series.index, dtype="datetime64[ns]")
    for fmt in ["%d/%m/%y", "%d/%m/%Y", "%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"]:
        mask = result.isna() & (series != "") & series.notna()
        if not mask.any():
            break
        result[mask] = pd.to_datetime(series[mask], format=fmt, errors="coerce")
    # Final fallback
    still_na = result.isna() & (series != "") & series.notna()
    if still_na.any():
        result[still_na] = pd.to_datetime(series[still_na], errors="coerce")
    return result


@st.cache_data(ttl=60)
def load_connection_data() -> pd.DataFrame:
    """
    Load and join Connection-Data + AREAs + MRUs.

    Output columns:
        METER NO, NAME, MOB NO, Latitude, Longitude,
        METER INLET GI, METER OUTLET GI, TOTAL GI,
        Main_Area, Subarea (== Main_Area),
        MRU  (e.g. "MRU-1"),
        MRU_NAME, MRU_ID (integer str),
        AREA_STATUS, is_uncharged_area
    """
    # ── Read ──────────────────────────────────────────────────────────────────
    conn  = pd.read_csv(ROOT_CONNECTIONS_FILE)
    areas = pd.read_csv(ROOT_AREAS_FILE)
    mrus  = pd.read_csv(ROOT_MRUS_FILE)

    # Strip BOM from column headers
    conn.columns  = [c.strip().replace("\ufeff", "") for c in conn.columns]
    areas.columns = [c.strip().replace("\ufeff", "") for c in areas.columns]
    mrus.columns  = [c.strip().replace("\ufeff", "") for c in mrus.columns]

    # Drop unnamed trailing columns
    conn  = conn.loc[:, ~conn.columns.str.startswith("Unnamed")]
    areas = areas.loc[:, ~areas.columns.str.startswith("Unnamed")]

    # ── Normalise AREAs ───────────────────────────────────────────────────────
    # Actual columns: AREA, MRU (int), STATUS
    areas = areas.rename(columns={"AREA": "Main_Area", "STATUS": "AREA_STATUS"})
    areas["Main_Area"]   = _clean(areas["Main_Area"])
    areas["MRU_ID"]      = _clean(areas["MRU"].astype(str))   # "1".."9"
    areas["AREA_STATUS"] = _norm_key(areas["AREA_STATUS"])     # CHARGED / UNCHARGED
    areas["area_key"]    = _norm_key(areas["Main_Area"])

    # ── Normalise MRUs ────────────────────────────────────────────────────────
    # Actual columns: MRU (int), MRU NAME
    mrus = mrus.rename(columns={"MRU NAME": "MRU_NAME"})
    mrus["MRU_ID"]   = _clean(mrus["MRU"].astype(str))        # "1".."9"
    mrus["MRU"]      = "MRU-" + mrus["MRU_ID"]                # "MRU-1".."MRU-9"
    mrus["MRU_NAME"] = _clean(mrus["MRU_NAME"])

    # ── Normalise Connections ─────────────────────────────────────────────────
    # Actual columns: METER NO, NAME, MOB NO, Lat, Lon, ...GI..., Area
    conn = conn.rename(columns={"Area": "Main_Area"})
    # Ensure canonical column names for the fixed columns
    col_map = {}
    for i, canonical in enumerate(["METER NO", "NAME", "MOB NO", "Latitude", "Longitude",
                                    "METER INLET GI", "METER OUTLET GI", "TOTAL GI"]):
        if canonical not in conn.columns and i < len(conn.columns):
            col_map[conn.columns[i]] = canonical
    if col_map:
        conn = conn.rename(columns=col_map)

    conn["Main_Area"] = _clean(conn["Main_Area"])
    conn["area_key"]  = _norm_key(conn["Main_Area"])

    for col in ["METER NO", "NAME", "MOB NO", "METER INLET GI", "METER OUTLET GI", "TOTAL GI"]:
        if col in conn.columns:
            conn[col] = _clean(conn[col])

    conn["Latitude"]  = pd.to_numeric(conn["Latitude"],  errors="coerce")
    conn["Longitude"] = pd.to_numeric(conn["Longitude"], errors="coerce")

    # ── Join areas lookup ─────────────────────────────────────────────────────
    area_lookup = areas[["area_key", "MRU_ID", "AREA_STATUS", "Main_Area"]].drop_duplicates("area_key")
    df = conn.merge(area_lookup, on="area_key", how="left", suffixes=("", "_lookup"))
    df = df.merge(mrus[["MRU_ID", "MRU_NAME", "MRU"]], on="MRU_ID", how="left")

    # Prefer lookup Main_Area (clean) over raw conn Main_Area
    if "Main_Area_lookup" in df.columns:
        df["Main_Area"] = df["Main_Area_lookup"].where(
            df["Main_Area_lookup"].notna() & (df["Main_Area_lookup"] != ""),
            df["Main_Area"]
        )

    # ── Final column setup ────────────────────────────────────────────────────
    df["Subarea"]          = df["Main_Area"]   # Subarea == Area (no sub-level exists)
    df["MRU"]              = _clean(df["MRU"]).replace("", "Unassigned")
    df["MRU_NAME"]         = _clean(df["MRU_NAME"])
    df["MRU_ID"]           = _clean(df["MRU_ID"])
    df["AREA_STATUS"]      = _clean(df["AREA_STATUS"]).str.upper().replace("", "UNCHARGED")
    df["is_uncharged_area"] = df["AREA_STATUS"].eq("UNCHARGED")

    # ── Coordinate filters ────────────────────────────────────────────────────
    df = df.dropna(subset=["Latitude", "Longitude"]).copy()
    df = df[df.apply(lambda r: _in_bbox(r["Latitude"], r["Longitude"]), axis=1)].copy()
    df = df[df.apply(lambda r: _not_error_coord(r["Latitude"], r["Longitude"]), axis=1)].copy()

    drop_cols = [c for c in ["area_key", "Main_Area_lookup", "MRU_x", "MRU_y"] if c in df.columns]
    return df.drop(columns=drop_cols).reset_index(drop=True)


@st.cache_data(ttl=60)
def load_master_data() -> pd.DataFrame:
    """
    Load Conversion-Data and join MRU/Area from connection data.

    Output columns:
        Meter Number, Customer Name, Mobile NUMBER, Conversion Date,
        Latitude, Longitude, MRU, Main_Area, Subarea
    """
    df_conn = load_connection_data()

    conv = pd.read_csv(ROOT_CONVERSIONS_FILE)
    conv.columns = [c.strip().replace("\ufeff", "") for c in conv.columns]

    # Map real column names → canonical names
    conv = conv.rename(columns={
        "Meter No.":       "Meter Number",
        "Meter No":        "Meter Number",
        "Date":            "Conversion Date",
    })
    # Fallback: first col is meter number if still missing
    if "Meter Number" not in conv.columns:
        conv = conv.rename(columns={conv.columns[0]: "Meter Number"})

    conv["Meter Number"] = _clean(conv["Meter Number"])

    # Build lookup from connection data
    lookup = df_conn[[
        "METER NO", "NAME", "MOB NO", "Latitude", "Longitude",
        "MRU", "MRU_NAME", "Main_Area", "Subarea"
    ]].drop_duplicates(subset=["METER NO"])

    df = conv.merge(lookup, left_on="Meter Number", right_on="METER NO", how="left")
    df = df.rename(columns={"NAME": "Customer Name", "MOB NO": "Mobile NUMBER"})

    # Parse mixed date formats
    date_str = df["Conversion Date"].fillna("").astype(str).str.strip() \
        if "Conversion Date" in df.columns else pd.Series([""] * len(df))
    df["Conversion Date"] = _parse_mixed_dates(date_str)

    df["Customer Name"] = _clean(df["Customer Name"]).replace("", "Unknown")
    df["Mobile NUMBER"] = _clean(df["Mobile NUMBER"])
    df["MRU"]           = _clean(df["MRU"]).replace("", "Unassigned")
    df["Main_Area"]     = _clean(df["Main_Area"])
    df["Subarea"]       = _clean(df["Subarea"]).replace("", "Unassigned")
    df["Latitude"]      = pd.to_numeric(df["Latitude"],  errors="coerce")
    df["Longitude"]     = pd.to_numeric(df["Longitude"], errors="coerce")

    return df[[
        "Meter Number", "Customer Name", "Mobile NUMBER", "Conversion Date",
        "Latitude", "Longitude", "MRU", "Main_Area", "Subarea"
    ]].copy().reset_index(drop=True)
