from datetime import datetime, timedelta
import sys
import os
import pandas as pd

# Ensure compatibility with PyInstaller for relative imports
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # Set by PyInstaller during runtime
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Add the parent directory of this script to the path if needed
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Model.PayrollSQL import export

class PayrollAutomation:
    """
    Class for automating payroll analysis and identifying anomalies.
    """

    def __init__(self):
        """
        Initializes the class and loads shift data from the database.
        """
        shift_data = export()  # Should return a DataFrame directly

        self.anomalies = [
            'Forgot to clock out',
            'Clocked out 90 min early',
            'Shift is 4 hours longer than scheduled',
        ]

        self.shift_data_df = pd.DataFrame(shift_data)

        if not self.shift_data_df.empty:
            self.shift_data_df['date_line'] = pd.to_datetime(self.shift_data_df['date_line'], errors='coerce')
            self.shift_data_df['date'] = self.shift_data_df['date_line']

        pd.set_option('display.max_rows', None)

    def get_pay_period(self, start_date, end_date):
        """
        Filters shift data between two dates.
        """
        pay_period_data = self.shift_data_df[
            (self.shift_data_df['date'] >= pd.to_datetime(start_date)) &
            (self.shift_data_df['date'] <= pd.to_datetime(end_date))
        ]
        return pay_period_data if not pay_period_data.empty else None

    def get_discrepancies(self, pay_period_data):
        """
        Identifies rows with significant time discrepancies.
        """
        if pay_period_data is None or pay_period_data.empty:
            return None
        discrepancies = pay_period_data[
            (pay_period_data['discrepancy'].abs() > 1)
        ]
        return discrepancies if not discrepancies.empty else None

    def punch_anomaly(self, row):
        """
        Classifies anomaly type for a given row.
        """
        if row['actual_hours'] == 0:
            return 'Did not punch in/PTO'

        if (row['earning_code_id'] in [53, 58]) and (126 <= row['cost_center_id'] <= 135):
            return 'ALS/IFT earning code assigned to 911 cost center'

        if row['discrepancy'] <= -1.5:
            return 'Clocked out at least 90 minutes early'

        elif row['discrepancy'] >= 10.0:
            return 'Forgot to clock out for at least 10 hours'

        elif 4.0 <= row['discrepancy'] < 10.0:
            return 'Shift is at least 4 hours longer than scheduled'

        else:
            return 'No anomaly'

    def get_punch_issues(self, df):
        """
        Applies anomaly logic to each row.
        """
        df = df.copy()
        df['anomaly'] = df.apply(self.punch_anomaly, axis=1)
        return df

    def get_anomaly_table(self, start_date=None, end_date=None):
        """
        Returns a DataFrame of anomalies between two dates.
        """
        pay_period = self.get_pay_period(start_date, end_date)
        anomalies = self.get_discrepancies(pay_period)
        if anomalies is not None:
            return self.get_punch_issues(anomalies)
        return None

    def filter_24_hours(self, start_date, end_date):
        """
        Drops:
        - 24-hour shifts that do NOT have the specific anomaly
        - Rows with 'No anomaly' as the anomaly type
        """
        df = self.get_anomaly_table(start_date, end_date)
        if df is None or df.empty:
            return None

        filtered_df = df[~(
            (df['scheduled_hours'] >= 23) &
            (df['anomaly'] != 'ALS/IFT earning code assigned to 911 cost center')
        )]

        filtered_df = filtered_df[filtered_df['anomaly'] != 'No anomaly']
        return filtered_df
    
    def filter_anomaly(self, anomaly, start_date, end_date):
        """
        Filters results by specific anomalies that the user provides.
        If 'All' is selected, return all anomalies.
        """
        df = self.filter_24_hours(start_date, end_date)
        if df is None or df.empty:
            return None

        if anomaly == 'All':
            return df  # No filtering if 'All' is selected
        
        filtered_df = df[df['anomaly'] == anomaly]
        return filtered_df



if __name__ == "__main__":
    payroll = PayrollAutomation()
    print(payroll.shift_data_df.head())  # Optional test output
