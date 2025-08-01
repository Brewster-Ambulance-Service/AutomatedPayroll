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
            ui.label(f"Failed to load logo: {e}").classes("text-red-500 text-sm")

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

def get_cost_centers_by_division(division, start_date, end_date, anomaly):
    df = pa.filter_division(anomaly, start_date, end_date, division)
    if df is None or df.empty:
        return ['All']

    if division == 'All':
        return ['All'] + sorted(df['cost_center_name'].unique().tolist())

    if division == 'Other':
        all_known_ids = {id for ids in pa.Divisions.values() for id in ids}
        filtered = df[~df['cost_center_id'].isin(all_known_ids)]
    else:
        if division not in pa.Divisions:
            return ['All']
        division_ids = pa.Divisions[division]
        filtered = df[df['cost_center_id'].isin(division_ids)]

    return ['All'] + sorted(filtered['cost_center_name'].unique().tolist())

# === Download handler ===
def on_download_click():
    dates = get_selected_period()
    start_date, end_date = dates.split(' - ')
    anomaly = get_filter()
    division = get_division()
    center = get_center()
    # df = pa.filter_anomaly(anomaly, start_date, end_date)
    # super_dash = pa.create_dashboard(start_date, end_date)
    # df = pa.filter_division(anomaly, start_date, end_date, division)
    df = pa.filter_cost_centers(anomaly, start_date, end_date, division, center)

    if df is not None and not df.empty:
        export_df = df.drop(columns=[
            'id', 
            'date', 'discrepancy', 'scheduled_start', 'scheduled_end'
        ], errors='ignore')
        filename = f'anomaly_report_{start_date}_{end_date}.csv'
        full_path = os.path.join(str(Path.home() / "Downloads"), filename)
        export_df.to_csv(full_path, index=False)
        ui.notify(f'CSV saved at: {full_path}')
    else:
        ui.notify("No data to export", type="warning")

# === Search handler ===
def on_search_click():
    dates = get_selected_period()
    anomaly = get_filter()
    division = get_division()
    start_date, end_date = dates.split(' - ')
    center = get_center()
    # Get data
    # df = pa.filter_division(anomaly, start_date, end_date, division)
    df = pa.filter_cost_centers(anomaly, start_date, end_date, division, center)
    super_dash = pa.create_dashboard(start_date, end_date)

    # Cleanup
    table_container.clear()
    dashboard_container.clear()

    # === Anomaly Table ===
    with table_container:
        if df is not None and not df.empty:
            df.drop(columns=['id', 'earning_code_id', 'date', 'discrepancy', 'scheduled_start', 'scheduled_end'], inplace=True, errors='ignore')
            ui.label("Anomaly Data").classes("text-lg font-semibold mb-2")
            ui.table.from_pandas(df).classes('w-full max-h-[70vh] overflow-auto').props('striped bordered hoverable dense wrap-cells')
        else:
            ui.label("No anomalies found for this pay period.").classes("text-red-700 font-semibold")

        # === Dashboard Table ===
        with dashboard_container:
            if super_dash is not None and not super_dash.empty:
                ui.label("Dashboard Summary").classes("text-lg font-semibold mt-6 mb-2")

                # Make sure anomaly names (index) show up as a column
                super_dash_display = super_dash.reset_index().rename(columns={'index': 'Anomaly'})

                ui.table.from_pandas(super_dash_display).classes(
                    'w-full max-h-[60vh] overflow-auto'
                ).props('striped bordered hoverable dense wrap-cells')
            else:
                ui.label("No dashboard summary data available.").classes("text-gray-700 font-semibold")

# === UI layout ===
with ui.column().classes('w-full p-4 gap-4'):
    with ui.row().classes('w-full justify-between items-center'):
        # === Pay Period Dropdown ===
        ui.label('Pay Period').classes('text-sm font-semibold')
        ui.select(
            options=pay_periods,
            value=selected_period['value'],
            with_input=True,
            on_change=lambda e: selected_period.update({'value': e.value})
        ).classes('w-60')

        # === Anomaly Dropdown ===
        anomalies = ['All','Shift is at least 4 hours longer than scheduled', 'Forgot to clock out for at least 10 hours', 'Clocked out at least 90 minutes early', 'ALS/IFT earning code assigned to 911 cost center',
                       'Did not punch in/PTO']
        selected_anomaly = {'value': anomalies[0]}
        ui.label('Anomaly').classes('text-sm font-semibold')
        ui.select(
            options=anomalies,
            value=selected_anomaly['value'],
            with_input=True,
            on_change=lambda e: selected_anomaly.update({'value': e.value})
        ).classes('w-60')

        # === Division Dropwdown === 
        division_names = ['All', 'Division 1', 'Division 2', 'Division 3', 'Division 4', 'Division 5', 'Division 6', 'Division 7', 'Florida', 'Other']
        selected_division = {'value': division_names[0]}
        ui.label('Division').classes('text-sm font-semibold')
        ui.select(
            options=division_names,
            value=selected_division['value'],
            with_input=True,
            on_change=lambda e: selected_division.update({'value': e.value})
        ).classes('w-60')

                # === Cost Center Dropdown ===
        # Get cost centers dynamically based on selected division
        cost_centers_tuples = pa.get_cost_centers(selected_division['value'])
        cost_center_options = ['All'] + [name for _, name in cost_centers_tuples]

        selected_cost_center = {'value': cost_center_options[0]}

        ui.label('Cost Center').classes('text-sm font-semibold')
        ui.select(
            options=cost_center_options,
            value=selected_cost_center['value'],
            with_input=True,
            on_change=lambda e: selected_cost_center.update({'value': e.value})
        ).classes('w-60')


        # === Buttons ===
        ui.button('Download CSV', on_click=on_download_click).classes('w-40')
        ui.button("Search", on_click=on_search_click).classes('w-40')


    table_container = ui.column().classes('w-full h-full')
    dashboard_container = ui.column().classes('w-full h-full')




    def get_selected_period():
        return selected_period['value']
    
    def get_filter():
        return selected_anomaly['value']
    
    def get_division():
        return selected_division['value']
    
    def get_center():
        return selected_cost_center['value']
    

# === App launcher ===
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title='Brewster Finance')
