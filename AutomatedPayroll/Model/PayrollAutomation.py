from datetime import datetime
from PayrollSQL import get_formatted_combined
import pandas as pd 
import numpy as np

"""
Class dedicated to automating the payroll process and finding outliers in shift and payroll data acquired from the PayrollSQL module.
This class uses the formatted data from PayrollSQL to perform operations such as identifying discrepancies in punch times
"""
class PayrollAutomation:

    def __init__(self):
        """
        Initializes the PayrollAutomation class.
        This constructor can be extended to include any necessary setup for the payroll automation process.
        """
        shift_data = get_formatted_combined()
        self.shift_data_df = pd.DataFrame(shift_data)

        # 🔧 Ensure 'date' column is in datetime format
        self.shift_data_df['date'] = pd.to_datetime(self.shift_data_df['date'], errors='coerce')

        pd.set_option('display.max_rows', None)


    def get_employee(self, name):
         """
         Retrieves employee data based on the provided name.
         This function filters the shift data for a specific employee.
         """
         employee_data = self.shift_data_df[self.shift_data_df['name'] == name]
         return employee_data if not employee_data.empty else None
    
    def get_pay_period(self, start_date, end_date):
        """
        Retrieves payroll data for a specific pay period defined by start and end dates.
        This function filters the shift data for shifts that fall within the specified date range.
        """
        pay_period_data = self.shift_data_df[
            (self.shift_data_df['date'] >= start_date) & 
            (self.shift_data_df['date'] <= end_date)
        ]
        return pay_period_data if not pay_period_data.empty else None


payroll = PayrollAutomation()
start = datetime(2025, 6, 30)
end = datetime(2025, 7, 15)

# Call the method
pay_period_data = payroll.get_pay_period(start, end)

# Display results
if pay_period_data is not None:
    print(pay_period_data)
else:
    print("No data found in the specified pay period.")
# result = payroll.get_employee('Mark Brewster')  # Example usage
# print(result)  # Output the employee data