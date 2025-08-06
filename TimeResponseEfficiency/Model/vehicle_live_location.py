#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests
import re
import logging
from datetime import datetime, timedelta, timezone
import os

# ---------------- LOGGING SETUP ---------------- #
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FOLDER = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)
LOG_FILE = os.path.join(LOG_FOLDER, "vehicle_live_location.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.info(f"✅ Logging initialized at: {LOG_FILE}")

# ---------------- ENV + FILE PATH ---------------- #
EXEC_PING_PATH = r'S:\Brewster Ambulance Service\Data & Analytics\Power BI\TraumaSoft\Executive KPI\Exec_Data_Feed\Vehicle Ping Data.csv'
LIVE_DATA_PATH = os.path.join(SCRIPT_DIR, "Live Data.csv")

# ---------------- FORMAT FUNCTION ---------------- #
def format_unit(unit):
    try:
        num = float(unit)
        if num == -1:
            return None
        return f"BA-{int(num):03d}"
    except:
        unit_str = str(unit).upper().replace(" ", "")
        if unit_str.startswith("FS-"):
            return "B" + unit_str
        if unit_str.startswith("RI-"):
            ri_match = re.match(r"RI-(\d{1,4})", unit_str)
            if ri_match:
                number = int(ri_match.group(1))
                return f"BP-{number:03d}"
        p_match = re.match(r"^P(\d{1,3})", unit_str)
        if p_match:
            number = int(p_match.group(1))
            return f"BP-{number:03d}"
        general_match = re.match(r"^([A-Z]{2,3})[-_]?(\d{1,4})", unit_str)
        if general_match:
            prefix = general_match.group(1)
            number = int(general_match.group(2))
            return f"{prefix}-{number:03d}"
        return unit_str

# ---------------- LOAD & CLEAN ---------------- #
df_msch = pd.read_csv(r"S:\Brewster Ambulance Service\Data & Analytics\Power BI\TraumaSoft\Executive KPI\Exec_Data_Feed\Permanently Scheduled Hours.csv")
df_msch['Home Base'] = df_msch['Base'].astype(str).str.strip()
df_msch['Unit'] = df_msch['Unit'].apply(format_unit)
df_msch = df_msch[df_msch['Unit'].notna()]
df_unit_base = df_msch[['Unit', 'Home Base', 'Division', 'LOS']].drop_duplicates().sort_values(by=['Unit', 'Home Base']).reset_index(drop=True)

# ---------------- RESOLVE LOS ---------------- #
def resolve_los(group):
    if set(group['LOS']) == {'ALS', 'BLS'}:
        group = group.head(1).copy()
        group['LOS'] = 'ALS'
        return group
    return group

df_bp = df_unit_base[df_unit_base['Unit'].str.contains("BP", case=False)]
df_bp_merged = df_bp.groupby(['Unit', 'Home Base', 'Division'], as_index=False, group_keys=False).apply(resolve_los).reset_index(drop=True)
df_unit_base = pd.concat([
    df_bp_merged,
    df_unit_base[~df_unit_base['Unit'].str.contains("BP", case=False)]
], ignore_index=True)

# ---------------- GPS TOKEN ---------------- #
url = 'https://api.gpsinsight.com/v2/userauth/login'
params = {'username': 'manand@brewsterambulance.com', 'password': 'Ocean-Theta1!'}
response = requests.get(url, params=params)

try:
    resp_json = response.json()
    logging.info(f"Login response JSON: {resp_json}")
    data = resp_json.get('data')
    logging.info(f"Type of 'data': {type(data)}")
    session_token = None
    if isinstance(data, list) and len(data) > 0:
        session_token = data[0].get('token')
    elif isinstance(data, dict):
        session_token = data.get('token')
    if not session_token:
        raise ValueError("Token not found in login response data.")
    logging.info("✅ Session token retrieved.")
except Exception as e:
    logging.exception("❌ Failed to extract token from response.")
    raise e

# ---------------- VEHICLE LIST ---------------- #
headers = {
    "Authorization": f"Bearer {session_token}",
    "Content-Type": "application/json"
}
vehicle_list_url = "https://api.gpsinsight.com/v2/vehicle/list"
vehicle_response = requests.get(vehicle_list_url, headers=headers)

if vehicle_response.status_code == 200:
    vehicle_data = vehicle_response.json()
    vehicle_df = pd.DataFrame(vehicle_data.get("data", []))
    logging.info(f"✅ Retrieved {len(vehicle_df)} vehicles")
else:
    logging.error(f"❌ Failed to get vehicle list: {vehicle_response.status_code}")
    vehicle_df = pd.DataFrame()

# ---------------- LOCATION DATA ---------------- #
cutoff_time_iso = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
location_url = "https://api.gpsinsight.com/v2/vehiclegroup/location"
params = {
    "vehicle_group": "ALL VEHICLES",
    "end_time": cutoff_time_iso
}
location_response = requests.get(location_url, headers=headers, params=params)

if location_response.status_code == 200:
    location_data = location_response.json()
    location_df = pd.DataFrame(location_data.get("data", []))
    logging.info(f"✅ Retrieved location data for {len(location_df)} vehicles")
else:
    logging.error(f"❌ Failed to get location data: {location_response.status_code}")
    location_df = pd.DataFrame()

# ---------------- MERGE DATA ---------------- #
if not vehicle_df.empty and not location_df.empty:
    overlapping_cols = ['vin', 'label', 'serial_number']
    vehicle_df_clean = vehicle_df.drop(columns=[col for col in overlapping_cols if col in location_df.columns], errors='ignore')
    merged_df = pd.merge(location_df, vehicle_df_clean, on="id", how="left")
else:
    logging.warning("⚠️ Merge skipped — one or both datasets are empty.")
    merged_df = pd.DataFrame()

# ---------------- POST-MERGE CLEANUP ---------------- #
merged_df['label'] = merged_df['label'].astype(str).str.strip().str.upper()
df_unit_base['Home Base'] = df_unit_base['Home Base'].str.replace(r'Weymouth D\d+', 'Weymouth', regex=True)
merged_df = merged_df.merge(df_unit_base, how='left', left_on='label', right_on='Unit', suffixes=('', '_dup'))
merged_df.drop(columns=['Unit'], inplace=True)

# ---------------- TIMESTAMP ---------------- #
execution_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
merged_df['exec_time'] = execution_timestamp

# ---------------- OPTIONAL SMARTSHEET ---------------- #
SPARE_VEHICLES_SHEET_ID = '6351545328160644'
SMARTSHEET_ACCESS_TOKEN = "Rx8MUzKprXdIHnocIoEpeOfBSrNGyuN80EIO2"
HEADERS = {
    "Authorization": f"Bearer {SMARTSHEET_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
smartsheet_url = f"https://api.smartsheet.com/2.0/sheets/{SPARE_VEHICLES_SHEET_ID}"
smartsheet_response = requests.get(smartsheet_url, headers=HEADERS)

if smartsheet_response.status_code == 200:
    sheet_data = smartsheet_response.json()
    column_map = {col['id']: col['title'] for col in sheet_data['columns']}
    rows = []
    for row in sheet_data['rows']:
        row_dict = {}
        for cell in row['cells']:
            col_name = column_map.get(cell['columnId'])
            row_dict[col_name] = cell.get('displayValue', cell.get('value'))
        rows.append(row_dict)
    spare_vehicle_df = pd.DataFrame(rows)
    merged_df = merged_df.merge(spare_vehicle_df[['Vehicle', 'Type']], left_on='label', right_on='Vehicle', how='outer')
    merged_df.drop(columns='Vehicle', inplace=True)
else:
    logging.error(f"❌ Failed to fetch Smartsheet data: {smartsheet_response.status_code}")

# ---------------- SAVE TO CSVs ---------------- #
# Save live snapshot
merged_df.to_csv(LIVE_DATA_PATH, index=False)
logging.info(f"✅ Live data snapshot saved to {LIVE_DATA_PATH}")

# Append to master CSV
try:
    existing = pd.read_csv(EXEC_PING_PATH, index_col=0, on_bad_lines='warn')
    last_index = existing.index.max() + 1
except Exception as e:
    logging.warning(f"⚠️ Could not read existing CSV cleanly: {e}")
    existing = pd.DataFrame()
    last_index = 0

merged_df.index = range(last_index, last_index + len(merged_df))
merged_df.to_csv(EXEC_PING_PATH, mode='a', header=not os.path.exists(EXEC_PING_PATH), index=True)
logging.info(f"✅ Appended {len(merged_df)} rows starting at index {last_index}")

