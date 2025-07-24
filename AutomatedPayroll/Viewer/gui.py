# Imports
from nicegui import ui
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Model.PayrollAutomation import PayrollAutomation

"""
Initalizes and centers the Brewster EMS banner to the center of the banner/header at height 100
"""

pa = PayrollAutomation()
dates =[]
with ui.header().classes('justify-center').props('height-hint=100') as header:
    with ui.tabs() as tabs:
        brewster=ui.image('BrewsterTwo.png').classes('w-64')
        

"""
Dynamic method created to find out the past 4 weeks (month) of pay periods
Initalized the date, created value for Saturday, and the saturday before
Created structure for entire week, and iterated through dates in MonthDayYear format
Returned these days as a list
"""
def pay_periods_month():
    #Using datetime find today, find where saturday is, and 
    today = datetime.today()
    #List Saturday at 5
    days_since_saturday = (today.weekday() + 2) % 7  
    last_saturday = today - timedelta(days=days_since_saturday)
    # Make a list of dates
    pay_periods = []
    for i in range(4):
        end_date = last_saturday - timedelta(weeks=i)
        start_date = end_date - timedelta(days=6)
        pay_period = f'{start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}'
        pay_periods.append(pay_period)
        # Return the list of dates
    return pay_periods



"""
Created pay_periods to group the pay period dropdown lsit and as well the ability to download the data as a CSV file
"""

pay_periods = pay_periods_month()

selected_period = {'value': pay_periods[0]}  

with ui.column().classes('w-full'):
    # Top bar with select and buttons
    with ui.row().classes('w-full justify-between items-center mb-4'):
        ui.label('Pay Period').classes('text-sm font-semibold')
        ui.select(
            options=pay_periods,
            value=selected_period['value'],
            with_input=True,
            on_change=lambda e: selected_period.update({'value': e.value})
        ).classes('w-60')

        ui.button('Download CSV', on_click=lambda: print('Connect backend CSV here')).classes('w-40')
        ui.button("Search", on_click=lambda: on_search_click()).classes('w-40')

    table_container = ui.column().classes('w-full h-full')

def get_selected_period():
    return selected_period['value']

def on_search_click():
    dates = get_selected_period()
    start_date, end_date = dates.split(' - ')
    df = pa.get_anomaly_table(start_date, end_date)

    table_container.clear()
    with table_container:
        ui.table.from_pandas(df).classes('w-full h-full').props('striped bordered hoverable')




if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title = 'Brewster Finance')