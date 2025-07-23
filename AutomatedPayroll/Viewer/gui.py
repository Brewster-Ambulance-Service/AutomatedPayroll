# Imports
from nicegui import ui
from datetime import datetime, timedelta
from nicegui import app




"""
Initalizes and centers the Brewster EMS banner to the center of the banner/header at height 100
"""
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
        pay_period = f'{start_date.strftime("%m/%d/%y")} - {end_date.strftime("%m/%d/%y")}'
        pay_periods.append(pay_period)
        # Return the list of dates
    return pay_periods



"""
Created pay_periods to group the pay period dropdown lsit and as well the ability to download the data as a CSV file
"""

pay_periods = pay_periods_month()
with ui.button_group():
    with ui.row().classes('w-full justify-between items-center'):
        selected_period = {'value': pay_periods[0]}  

        #Pay Period Button
        ui.label('Pay Period').classes('text-sm font-semibold')
        ui.select(
            options=pay_periods,
            value=selected_period['value'],
            with_input=True,
            on_change=lambda e: selected_period.update({'value': e.value})
            ).classes('w-55')
           
        

        # CSV Button
        ui.button('Download CSV', on_click=lambda: print('Connect backend CSV here')).classes('w-40') 
        ui.button("Search", on_click=lambda: print('Connect backend to search')).classes('w-30')



""""
Created Multiple examples of dummy Data

This includes name, pay_period, date, reason, and level of severity indicated by a flag

allowed sorting for each column, by either alphabetically or numerically through the user interface in the GUI

Severity goes in levels of: 
🟡(considered) -> 🟠(slight possibility) -> 🔴 (high probability)
"""
ui.table(
    columns=[
        {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'sortable': True},
        {'name': 'pay_period', 'label': 'Pay Period', 'field': 'pay_period', 'required': True, 'sortable': True},
        {'name': 'date', 'label': 'Date', 'field': 'date', 'required': True, 'sortable': True},
        {'name': 'reason', 'label': 'Reason for Error', 'field': 'reason', 'required': True},
        {'name': 'flag', 'label': 'Status', 'field': 'flag', 'required': True},
    ],
    rows=[
        {
            'name': 'John Doe',
            'pay_period': '00287',
            'date': '07/19/25',
            'reason': 'Forgot to clock out',
            'flag': '🔴'
        },
        {
            'name': 'Jane Smith',
            'pay_period': '00287',
            'date': '07/20/25',
            'reason': 'Overpaid (not IFT)',
            'flag': '🟠'
        },
        {
            'name': 'Mark Brewster',
            'pay_period': '12345',
            'date': '08/25/27',
            'reason': '0 trips, more than 7 hours',
            'flag': '🟡'
        }    
    ]
)



# Launch in native app
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title = 'Brewster Finance')