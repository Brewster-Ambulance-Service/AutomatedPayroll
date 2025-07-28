from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd

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
            'Shift punch is different than crew members'
        ]

        # Convert to DataFrame if it's not already
        self.shift_data_df = pd.DataFrame(shift_data)

        if not self.shift_data_df.empty:
            # Parse 'date_line' and create 'date' alias
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
        
        # Underworked: clocked out early
        if row['discrepancy'] <= -1.5:
            return 'Clocked out at least 90 minutes early'
        
        # Overworked: forgot to clock out
        elif row['discrepancy'] >= 10.0:
            return 'Forgot to clock out for at least 10 hours'
        
        # Overworked: extended shift (but not 10+ hours)
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
        
        # Keep all rows except 24hr shifts without the specific anomaly
        filtered_df = df[~(
            (df['scheduled_hours'] >= 23) &
            (df['anomaly'] != 'ALS/IFT earning code assigned to a 911 cost center')
        )]
        
        # Further drop rows with 'No anomaly'
        filtered_df = filtered_df[filtered_df['anomaly'] != 'No anomaly']

        # filtered_df =  self.get_anomaly_table(start_date, end_date)
        return filtered_df

    
if __name__ == "__main__":
    payroll = PayrollAutomation()

# get_pay_period =  payroll.get_pay_period('2025-07-03', '2025-07-04')
# # print(get_pay_period)

# get_anomalies = payroll.get_discrepancies(get_pay_period)
# print("Anomalies in shift data")
# get_anomaly = payroll.get_punch_issues(get_anomalies)
# print(get_anomaly)
# print(get_anomaly.sort_values(by='date_line', ascending = True))

# # Define pay period (last 14 days)
# end_date = datetime.today().date()
# start_date = end_date - timedelta(days=10)
# df = payroll.shift_data_df
# payroll.get_pay_period("2025-07-24"," 2025-07-25")
# print(df)

# Get the anomaly table
# anomaly_df = payroll.get_anomaly_table(start_date=start_date, end_date=end_date)