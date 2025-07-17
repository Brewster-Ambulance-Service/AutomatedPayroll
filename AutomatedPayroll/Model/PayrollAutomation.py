from datetime import datetime
from PayrollSQL import get_formatted_combined, get_discrepancies
import pandas as pd 
import numpy as np
from sklearn.ensemble import IsolationForest    
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
        error_data = get_discrepancies()
        self.error_data_df = pd.DataFrame(error_data)
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
    
    # def find_outliers(self):
    #     """
    #     Identifies outliers in the shift data based on predefined criteria.
    #     This function can be extended to include specific logic for detecting anomalies in shift times or hours worked.
    #     """
    #     # Example logic to find outliers (to be customized)
    #     outliers = self.shift_data_df[
    #         (self.shift_data_df['total_hours'] > 12) | 
    #         (self.shift_data_df['total_hours'] < 0.5)
    #     ]
    #     return outliers if not outliers.empty else None


payroll = PayrollAutomation()

print(payroll.error_data_df)
# start = datetime(2025, 6, 30)
# end = datetime(2025, 7, 15)

# # Call the method
# pay_period_data = payroll.get_pay_period(start, end)

# # Display results
# if pay_period_data is not None:
#     print(pay_period_data.head())
# else:
#     print("No data found in the specified pay period.")
# result = payroll.get_employee('Mark Brewster')  # Example usage
# print(result)  # Output the employee data