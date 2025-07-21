from datetime import datetime
from PayrollSQL import get_formatted_combined, get_discrepancies
import pandas as pd

class PayrollAutomation:
    """
    Class dedicated to automating the payroll process and finding outliers in shift and payroll data
    acquired from the PayrollSQL module.
    """

    def __init__(self):
        """
        Initializes the PayrollAutomation class and loads shift and error data into DataFrames.
        """
        # Load data from PayrollSQL functions
        shift_data = get_formatted_combined()
        error_data = get_discrepancies()

        # Convert to DataFrames
        self.shift_data_df = pd.DataFrame(shift_data)
        self.error_data_df = pd.DataFrame(error_data)

        # Ensure 'date' column is parsed as datetime
        if not self.shift_data_df.empty:
            self.shift_data_df['date'] = pd.to_datetime(self.shift_data_df['date'], errors='coerce')

        pd.set_option('display.max_rows', None)

    def get_employee(self, name):
        """
        Retrieves shift data for a specific employee by name.
        """
        employee_data = self.shift_data_df[self.shift_data_df['name'] == name]
        return employee_data if not employee_data.empty else None

    def get_pay_period(self, start_date, end_date):
        """
        Filters shift data to a specified pay period between two dates.
        """
        pay_period_data = self.shift_data_df[
            (self.shift_data_df['date'] >= pd.to_datetime(start_date)) &
            (self.shift_data_df['date'] <= pd.to_datetime(end_date))
        ]
        return pay_period_data if not pay_period_data.empty else None

    # Example outlier detection (optional)
    # def find_outliers(self):
    #     outliers = self.shift_data_df[
    #         (self.shift_data_df['total_hours'] > 12) |
    #         (self.shift_data_df['total_hours'] < 0.5)
    #     ]
    #     return outliers if not outliers.empty else None


# Example usage
if __name__ == "__main__":
    payroll = PayrollAutomation()

    # Print all discrepancies
    print("\nDiscrepancies:")
    print(payroll.error_data_df)

    # Uncomment to test pay period
    # start = datetime(2025, 6, 30)
    # end = datetime(2025, 7, 15)
    # pay_period_data = payroll.get_pay_period(start, end)
    # print(pay_period_data if pay_period_data is not None else "No data found.")

    # Uncomment to test employee
    # result = payroll.get_employee('Mark Brewster')
    # print(result if result is not None else "Employee not found.")
