from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd

from Model.PayrollSQL import get_data



class PayrollAutomation:

    """
    Class dedicated to automating the payroll process and finding outliers in shift and payroll data
    acquired from the PayrollSQL module.
    """

    def __init__(self):
        """
        Initializes the PayrollAutomation class and loads shift and error data into DataFrames.
        """
        #load data using the first element of the tuple holding the shift data and the second elemeny holding the discrepancy data
        shift_data = get_data()[0]
        self.anomalies = ['Forgot to clock out', 'Clocked out 90 min early', 'Shift is 4 hours longer than scheduled', 
                          'Shift punch is different than crew members']

        # Convert and load into pandas dataframes
        self.shift_data_df = pd.DataFrame(shift_data)

        # Ensure 'date' column is parsed as datetime
        if not self.shift_data_df.empty:
            self.shift_data_df['date'] = pd.to_datetime(self.shift_data_df['date'], errors='coerce')

        pd.set_option('display.max_rows', None)


    #Filters shift data to those specified between 2 dates
    def get_pay_period(self, start_date, end_date):
        """
        Filters shift data to a specified pay period between two dates.
        """
        pay_period_data = self.shift_data_df[
            (self.shift_data_df['date'] >= pd.to_datetime(start_date)) &
            (self.shift_data_df['date'] <= pd.to_datetime(end_date))
        ]
        return pay_period_data if not pay_period_data.empty else None
    

    #filters the data solely to those who have anomalies in punches
    def get_discrepancies(self, pay_period_data):
        """
        Identifies discrepancies in the pay period data.
        Discrepancies are defined as shifts where the total hours worked
        differ significantly from the scheduled shift hours.
        """
        if pay_period_data is None or pay_period_data.empty:
            return None
        
        # Calculate discrepancies
        discrepancies = pay_period_data[
            (pay_period_data['discrepancy'].abs() > 1)  # Threshold for discrepancy detection
             ]
        return discrepancies if not discrepancies.empty else None
    
    
    def punch_anomaly(self, row):
        if(row['earning_code_id'] == 53 or row['earning_code_id'] == 58)and 126 <= row['cost_center_id'] <= 135:
            return 'ALS/IFT earning code assigned to 911 cost center'
        if row['discrepancy'] >= 1.5:
            return 'Clocked out at least 90 minutes early'
        elif row['discrepancy'] < -10.0:
            return 'Forgot to clock out for at least 10 hours'
        elif row['discrepancy'] < -4.0 and row['discrepancy'] >= -10.0:
            return 'Shift is at least 4 hours longer than scheduled'
        else:
            return 'No anomaly'
        
    def get_punch_issues(self, df):
    
        df = df.copy()  # Avoid SettingWithCopyWarning
        df['anomaly'] = df.apply(self.punch_anomaly, axis=1)
        return df
    
        

    def get_partner_punchout():

        """
        Placeholder for future implementation to get partner punch-out data.
        Currently not implemented.
        """
        raise NotImplementedError("Partner punch-out functionality is not yet implemented.")
    
    def get_anomaly_table(self, start_date=None, end_date=None):
      """
        Returns a DataFrame containing anomalies in shift data.
        """ 
      get_pay_period = self.get_pay_period(start_date, end_date)
      get_anomalies = self.get_discrepancies(get_pay_period)
      get_anomaly = self.get_punch_issues(get_anomalies)
      
      return get_anomaly 

 
# # # Example usage
# if __name__ == "__main__":
#     payroll = PayrollAutomation()

# get_pay_period = payroll.get_pay_period('2025-07-03', '2025-07-24')
# # print("Pay Period Data:")
# # print(get_pay_period)

# get_anomalies = payroll.get_discrepancies(get_pay_period)
# print("Anomalies in Shift Data:")
# get_anomaly = payroll.get_punch_issues(get_anomalies)
# print(get_anomaly.sort_values(by='shift_assignment_id', ascending=True))