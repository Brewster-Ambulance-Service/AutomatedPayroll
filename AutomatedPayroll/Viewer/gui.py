# Imports
from nicegui import ui,  events
from datetime import datetime, timedelta
import sys
import os
import tempfile
import shutil
from io import StringIO
from pathlib import Path
import tempfile

# Append project paths for import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Model.PayrollAutomation import PayrollAutomation

ui.add_head_html('''
<style>
    table.nicegui-table tbody tr:nth-child(odd) {
    background-color: #f9f9f9;
    }
    table.nicegui-table tbody tr:nth-child(even) {
    background-color: #ffffff;
    }
</style>
''')

"""
Initializes and centers the Brewster EMS banner to the center of the banner/header at height 100
"""
pa = PayrollAutomation()
dates = []
dataframe = []

# Header and logo
with ui.header().classes('justify-center').props('height-hint=100') as header:
    with ui.tabs():
        brewster = ui.image('BrewsterTwo.png').classes('w-64')

"""
Dynamic method created to find out the past 4 weeks (month) of pay periods
Initialized the date, created value for Saturday, and the Saturday before
Created structure for entire week, and iterated through dates in MonthDayYear format
Returned these days as a list
"""
def pay_periods_month():
    # Using datetime to find today and find where Saturday is
    today = datetime.today()
    # List Saturday at 5
    days_since_saturday = (today.weekday() + 2) % 7  
    last_saturday = today - timedelta(days=days_since_saturday)

    # Pay periods for the last 4 full weeks (Saturday to Friday)
    pay_periods = []
    for i in range(4):
        end_date = last_saturday - timedelta(weeks=i)
        start_date = end_date - timedelta(days=6)
        pay_period = f'{start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}'
        pay_periods.append(pay_period)

    # Add current partial pay period from last Saturday to today at the start
    current_partial_period = f'{last_saturday.strftime("%Y-%m-%d")} - {today.strftime("%Y-%m-%d")}'
    pay_periods.insert(0, current_partial_period)

    # Return the list of dates
    return pay_periods

"""
Created pay_periods to group the pay period dropdown list and 
as well the ability to download the data as a CSV file
"""
pay_periods = pay_periods_month()
selected_period = {'value': pay_periods[0]}  

def on_download_click():
    dates = get_selected_period()
    start_date, end_date = dates.split(' - ')
    df = pa.filter_24_hours(start_date, end_date)

    if df is not None and not df.empty:
        export_df = df.drop(columns=[
            'id', 'earning_code_id', 'cost_center_id',
            'date', 'discrepancy', 'scheduled_start', 'scheduled_end'
        ], errors='ignore')
        downloads_path = str(Path.home() / "Downloads")
        filename = f'anomaly_report_{start_date}_{end_date}.csv'
        full_path = os.path.join(downloads_path, filename)
        export_df.to_csv(full_path, index=False)
        ui.notify(f'✅ CSV saved at: {full_path}')
    else:
        ui.notify("No data to export", type="warning")


# Container to hold the whole app body
with ui.column().classes('w-full p-4 gap-4'):

    # --- Top Control Bar (Always stays at the top) ---
    with ui.row().classes('w-full justify-between items-center'):
        
        # Pay Period Button
        ui.label('Pay Period').classes('text-sm font-semibold')
        ui.select(
            options=pay_periods,
            value=selected_period['value'],
            with_input=True,
            on_change=lambda e: selected_period.update({'value': e.value})
        ).classes('w-60')

        # CSV and Search Buttons
        ui.button('Download CSV', on_click=lambda:on_download_click()).classes('w-40') 
        ui.button("Search", on_click=lambda: on_search_click()).classes('w-40')

    """
    Table container for displaying the data output
    This is updated dynamically after clicking 'Search'
    """
    table_container = ui.column().classes('w-full h-full')

    """
    Get the selected pay period and return it in date format
    """
    def get_selected_period():
        return selected_period['value']

    """
    On Search Click, use selected pay period to get filtered data from PayrollAutomation,
    then display that data in a responsive, styled table.
    """
    def on_search_click():
        dates = get_selected_period()
        start_date, end_date = dates.split(' - ')
        df = pa.filter_24_hours(start_date, end_date)
        df.drop(columns=['id', 'earning_code_id', 'cost_center_id', 'date', 'discrepancy', 'scheduled_start', 'scheduled_end'], inplace=True)
        table_container.clear()
        with table_container:
            if df is not None and not df.empty:
                # Responsive, scrollable, and striped table
               ui.table.from_pandas(df).classes(
                    'nicegui-table w-full max-h-[70vh] overflow-auto'
                ).props(
                    'bordered hoverable dense wrap-cells'
                )

            else:
                ui.label("No anomalies found for this pay period.").classes("text-red-700 font-semibold")
# Run the app
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title='Brewster Finance')
