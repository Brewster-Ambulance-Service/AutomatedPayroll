# gui.py

from nicegui import ui
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# === For PyInstaller-compatible resource access ===
def resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Append parent directory to path for importing Model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Model.PayrollAutomation import PayrollAutomation

# Initialize
pa = PayrollAutomation()
dates = []
dataframe = []

# === UI Header with logo ===
with ui.header().classes('justify-center').props('height-hint=100'):
    with ui.tabs():
        try:
            image_path = resource_path('BrewsterTwo.png')
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found at: {image_path}")
            ui.image(image_path).classes('w-64')
        except Exception as e:
            ui.label(f"⚠️ Failed to load logo: {e}").classes("text-red-500 text-sm")

# === Pay period generator ===
def pay_periods_month():
    today = datetime.today()
    days_since_saturday = (today.weekday() + 2) % 7
    last_saturday = today - timedelta(days=days_since_saturday)

    pay_periods = []
    for i in range(4):
        end_date = last_saturday - timedelta(weeks=i)
        start_date = end_date - timedelta(days=6)
        pay_periods.append(f'{start_date:%Y-%m-%d} - {end_date:%Y-%m-%d}')

    pay_periods.insert(0, f'{last_saturday:%Y-%m-%d} - {today:%Y-%m-%d}')
    return pay_periods

pay_periods = pay_periods_month()
selected_period = {'value': pay_periods[0]}

# === Download handler ===
def on_download_click():
    dates = get_selected_period()
    start_date, end_date = dates.split(' - ')
    df = pa.filter_24_hours(start_date, end_date)

    if df is not None and not df.empty:
        export_df = df.drop(columns=[
            'id', 'earning_code_id', 'cost_center_id',
            'date', 'discrepancy', 'scheduled_start', 'scheduled_end'
        ], errors='ignore')
        filename = f'anomaly_report_{start_date}_{end_date}.csv'
        full_path = os.path.join(str(Path.home() / "Downloads"), filename)
        export_df.to_csv(full_path, index=False)
        ui.notify(f'✅ CSV saved at: {full_path}')
    else:
        ui.notify("No data to export", type="warning")

# === Search handler ===
def on_search_click():
    dates = get_selected_period()
    start_date, end_date = dates.split(' - ')
    df = pa.filter_24_hours(start_date, end_date)
    df.drop(columns=['id', 'earning_code_id', 'cost_center_id', 'date', 'discrepancy', 'scheduled_start', 'scheduled_end'], inplace=True)
    table_container.clear()
    with table_container:
        if df is not None and not df.empty:
            ui.table.from_pandas(df).classes('w-full max-h-[70vh] overflow-auto').props('striped bordered hoverable dense wrap-cells')
        else:
            ui.label("No anomalies found for this pay period.").classes("text-red-700 font-semibold")

# === UI layout ===
with ui.column().classes('w-full p-4 gap-4'):
    with ui.row().classes('w-full justify-between items-center'):
        ui.label('Pay Period').classes('text-sm font-semibold')
        ui.select(
            options=pay_periods,
            value=selected_period['value'],
            with_input=True,
            on_change=lambda e: selected_period.update({'value': e.value})
        ).classes('w-60')

        ui.button('Download CSV', on_click=on_download_click).classes('w-40')
        ui.button("Search", on_click=on_search_click).classes('w-40')

    table_container = ui.column().classes('w-full h-full')

    def get_selected_period():
        return selected_period['value']

# === App launcher ===
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title='Brewster Finance')
