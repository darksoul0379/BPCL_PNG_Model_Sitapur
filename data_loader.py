"""
data_loader.py
==============
Primary data loading layer for the Sitapur PNG dashboard.

Reads from updated root CSV files and prepares flat DataFrames used by the app.
The old db_min folder is no longer used by dashboard reads.
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


def _clean_string_series(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.replace("\ufeff", "", regex=False).str.strip()


def _norm_key(s: pd.Series) -> pd.Series:
    return _clean_string_series(s).str.upper().str.replace(r"\s+", " ", regex=True)


def _in_bbox(lat: float, lon: float) -> bool:
    if pd.isna(lat) or pd.isna(lon):
        return False
    return (
        SITAPUR_BBOX["lat_min"] <= lat <= SITAPUR_BBOX["lat_max"]
        and SITAPUR_BBOX["lon_min"] <= lon <= SITAPUR_BBOX["lon_max"]
    )


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _not_error_coord(lat: float, lon: float) -> bool:
    if pd.isna(lat) or pd.isna(lon):
        return False
    return all(_haversine_m(lat, lon, elat, elon) >= erad for elat, elon, erad in ERROR_ZONES)


@st.cache_data(ttl=60)
def load_connection_data() -> pd.DataFrame:
    conn = pd.read_csv(ROOT_CONNECTIONS_FILE)
    areas = pd.read_csv(ROOT_AREAS_FILE)
    mrus = pd.read_csv(ROOT_MRUS_FILE)

    conn.columns = [_clean_string_series(pd.Series([c])).iloc[0] for c in conn.columns]
    areas.columns = [_clean_string_series(pd.Series([c])).iloc[0] for c in areas.columns]
    mrus.columns = [_clean_string_series(pd.Series([c])).iloc[0] for c in mrus.columns]

    conn = conn.rename(columns={
        "Area": "Main_Area",
    })
    conn = conn.rename(columns={
        conn.columns[0]: "METER NO",
        conn.columns[1]: "NAME",
        conn.columns[2]: "MOB NO",
        conn.columns[3]: "Latitude",
        conn.columns[4]: "Longitude",
        conn.columns[5]: "METER INLET GI",
        conn.columns[6]: "METER OUTLET GI",
        conn.columns[7]: "TOTAL GI",
    })

    areas = areas.rename(columns={
        areas.columns[0]: "Main_Area",
        areas.columns[1]: "MRU_ID",
        areas.columns[2]: "AREA_STATUS",
    })
    mrus = mrus.rename(columns={
        mrus.columns[0]: "MRU_ID",
        mrus.columns[1]: "MRU_NAME",
    })

    conn["Main_Area"] = _clean_string_series(conn["Main_Area"])
    conn["area_key"] = _norm_key(conn["Main_Area"])

    areas["Main_Area"] = _clean_string_series(areas["Main_Area"])
    areas["MRU_ID"] = _clean_string_series(areas["MRU_ID"])
    areas["AREA_STATUS"] = _norm_key(areas["AREA_STATUS"])
    areas["area_key"] = _norm_key(areas["Main_Area"])

    mrus["MRU_ID"] = _clean_string_series(mrus["MRU_ID"])
    mrus["MRU_NAME"] = _clean_string_series(mrus["MRU_NAME"])
    mrus["MRU"] = "MRU-" + mrus["MRU_ID"]

    df = conn.merge(
        areas[["area_key", "MRU_ID", "AREA_STATUS", "Main_Area"]].drop_duplicates("area_key"),
        on="area_key",
        how="left",
        suffixes=("", "_lookup"),
    ).merge(
        mrus[["MRU_ID", "MRU_NAME", "MRU"]],
        on="MRU_ID",
        how="left",
    )

    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    for col in ["NAME", "METER NO", "MOB NO", "METER INLET GI", "METER OUTLET GI", "TOTAL GI"]:
        if col in df.columns:
            df[col] = _clean_string_series(df[col])

    df["Main_Area"] = _clean_string_series(df.get("Main_Area_lookup", df["Main_Area"]))
    df["Subarea"] = df["Main_Area"]
    df["MRU"] = _clean_string_series(df["MRU"]).replace("", "Unassigned")
    df["MRU_NAME"] = _clean_string_series(df["MRU_NAME"])
    df["AREA_STATUS"] = _clean_string_series(df["AREA_STATUS"]).str.upper().replace("", "UNCHARGED")
    df["is_uncharged_area"] = df["AREA_STATUS"].eq("UNCHARGED")

    df = df.dropna(subset=["Latitude", "Longitude"]).copy()
    df = df[df.apply(lambda r: _in_bbox(r["Latitude"], r["Longitude"]), axis=1)].copy()
    df = df[df.apply(lambda r: _not_error_coord(r["Latitude"], r["Longitude"]), axis=1)].copy()

    return df.drop(columns=[c for c in ["area_key", "Main_Area_lookup"] if c in df.columns])


@st.cache_data(ttl=60)
def load_master_data() -> pd.DataFrame:
    df_conn = load_connection_data()
    conv = pd.read_csv(ROOT_CONVERSIONS_FILE)
    conv.columns = [_clean_string_series(pd.Series([c])).iloc[0] for c in conv.columns]

    meter_col = conv.columns[0]
    df = conv.rename(columns={meter_col: "Meter Number"}).copy()
    df["Meter Number"] = _clean_string_series(df["Meter Number"])

    lookup = df_conn[[
        "METER NO", "NAME", "MOB NO", "Latitude", "Longitude", "MRU", "Main_Area", "Subarea"
    ]].drop_duplicates(subset=["METER NO"])

    df = df.merge(lookup, left_on="Meter Number", right_on="METER NO", how="left")
    df = df.rename(columns={
        "NAME": "Customer Name",
        "MOB NO": "Mobile NUMBER",
    })

    if "Conversion Date" not in df.columns:
        df["Conversion Date"] = pd.Timestamp("2025-01-01")
    df["Conversion Date"] = pd.to_datetime(df["Conversion Date"], errors="coerce")

    df["Customer Name"] = _clean_string_series(df["Customer Name"]).replace("", "Unknown")
    df["Mobile NUMBER"] = _clean_string_series(df["Mobile NUMBER"])
    df["MRU"] = _clean_string_series(df["MRU"]).replace("", "Unassigned")
    df["Main_Area"] = _clean_string_series(df["Main_Area"])
    df["Subarea"] = _clean_string_series(df["Subarea"]).replace("", "Unassigned")
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    return df[[
        "Meter Number", "Customer Name", "Mobile NUMBER", "Conversion Date",
        "Latitude", "Longitude", "MRU", "Main_Area", "Subarea"
    ]].copy()
