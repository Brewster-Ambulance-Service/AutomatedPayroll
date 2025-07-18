# Imports

from nicegui import ui


        
class ToggleButton(ui.button):

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self._state = False
            self.on('click', self.toggle)

        def toggle(self) -> None:
            """Toggle the button state."""
            self._state = not self._state
            self.update()

        def update(self) -> None:
            self.props(f'color={"green" if self._state else "red"}')
            super().update()
"""
Toggle Anomalies
"""



with ui.header().classes('justify-center').props('height-hint=100') as header:
    with ui.tabs() as tabs:
       
        brewster=ui.image('BrewsterTwo.png').classes('w-64')

"""
Brewster png banner
"""

        
        
with ui.button_group():
    with ui.row().classes('w-full justify-between items-center'):
        with ui.dropdown_button('Pay Periods', auto_close=True):
            ui.item('Item 1')
            ui.item('Item 2')
        ui.button('Download CSV', on_click=lambda: print('Connect backend CSV here'))
        ToggleButton('Anomalies')

"""
Grouping together buttons
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
            'flag': '🟡'
        },
        {
            'name': 'Mark Brewster',
            'pay_period': '12345',
            'date': '08/25/27',
            'reason': 'No error occured',
            'flag': '🟢'
        }    
    ]
)

""" 
Dummy Data
"""



# Launch in native app
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title = 'Brewster Finance')
