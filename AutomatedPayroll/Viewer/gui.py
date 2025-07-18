from nicegui import ui

# --- Dropdown + Download Button ---
with ui.row().classes('w-full justify-between items-center'):
    time_filter = ui.select(
        options=['Day', 'Week', 'Month'],
        value='Week',
        label='Time Range'
    )
    ui.button('Download CSV', on_click=lambda: print('Connect backend CSV here'))


# print('rows loading...')
# print([
#     {'name': 'John Doe', 'pay_period': '00287', 'date': '07/19/25', 'reason': 'Forgot to clock out', 'flag': 'Red'},
#     {'name': 'Jane Smith', 'pay_period': '00287', 'date': '07/20/25', 'reason': 'Overpaid (not IFT)', 'flag': 'Yellow'}
# ])
# --- Table With Dummy Data (Fixed) ---
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
            'flag': 'Red'
        },
        {
            'name': 'Jane Smith',
            'pay_period': '00287',
            'date': '07/20/25',
            'reason': 'Overpaid (not IFT)',
            'flag': 'Yellow'
        }
    ]
)





# --- Flag Legend ---
with ui.row().classes('mt-6 gap-4'):
    ui.label('Red: High confidence error detected').style('color: #cc4444; font-weight: bold')
    ui.label('Yellow: Moderate confidence error detected').style('color: #d6a300; font-weight: bold')

# --- Native App Launch ---
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True)
