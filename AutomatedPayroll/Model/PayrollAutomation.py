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

    #global variable for the divisions data for which cost centers are in which divisions
    Divisions = {
            'Division 1': [14, 15, 16, 17, 41, 43, 44, 45, 46, 47, 48, 102, 112, 119, 165, 166, 167, 22, 57],
            'Division 2': [33, 34, 35, 36, 42, 61, 62, 63, 64, 65, 66, 67, 68, 69, 73, 74, 76, 77, 99, 113, 120, 126, 131, 132, 133, 220, 250, 18, 72],
            'Division 3': [25, 26, 27, 30, 31, 100, 114, 121, 127, 128, 212, 238, 29],
            'Division 4': [49, 51, 52, 53, 58, 59, 145, 60, 79, 80, 81, 82, 83, 135, 84, 85, 86, 87, 88, 89, 134, 90, 91, 92, 101, 115, 122, 130],
            'Division 5': [116, 123, 144, 146, 147],
            'Division 6': [103, 107, 108, 117, 125, 129, 152, 153, 154, 155, 156, 157, 158, 159, 161, 162, 163, 160],
            'Division 7': [104, 118, 124, 180, 182, 183, 184, 188],
            'Florida':    [251, 252, 253, 254, 255]
                }
    
    # global variable for the different type of anomalies an empployee can have
    anomalies = [
        'Shift is at least 4 hours longer than scheduled',
        'Forgot to clock out for at least 10 hours',
        'Clocked out at least 90 minutes early',
        'ALS/IFT earning code assigned to 911 cost center',
        'Did not punch in/PTO'
    ]


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
    
    def filter_division(self, anomaly, start_date, end_date, division):
        """
        Filters results in the table by division based on predefined cost center IDs.
        If 'Other' is selected, returns rows where cost_center_id is not in any known division.
        """
        df = self.filter_anomaly(anomaly, start_date, end_date)
        if df is None or df.empty:
            return None

        if division == 'All':
            return df

        # Get all known cost center IDs
        all_known_ids = {id for ids in self.Divisions.values() for id in ids}

        if division == 'Other':
            return df[~df['cost_center_id'].isin(all_known_ids)]

        return df[df['cost_center_id'].isin(self.Divisions[division])]

    
    def filter_cost_centers(self, anomaly, start_date, end_date, division, center):
        """
        Filters by a specific cost center name that is located in the specified division.
        """
        df = self.filter_division(anomaly, start_date, end_date, division)
        if df is None or df.empty:
            return None

        if center == 'All':
            return df

        # Get all known cost center IDs
        all_known_ids = {id for ids in self.Divisions.values() for id in ids}

        if division == 'Other':
            df = df[~df['cost_center_id'].isin(all_known_ids)]
        else:
            df = df[df['cost_center_id'].isin(self.Divisions[division])]

        # Filter by cost_center_name
        return df[df['cost_center_name'] == center]
    
    def get_cost_centers(self, division):
        """
        Returns a sorted list of unique (cost_center_id, cost_center_name) tuples filtered by division.

        - If division == 'All', return all cost centers.
        - If division == 'Other', return cost centers not in any division.
        - Otherwise, return cost centers for the specified division.
        """
        if self.shift_data_df is None or self.shift_data_df.empty:
            return []

        # Get unique cost centers
        unique_centers_df = self.shift_data_df[['cost_center_id', 'cost_center_name']].dropna().drop_duplicates()

        # All known cost center IDs in all divisions
        all_known_ids = {id for ids in self.Divisions.values() for id in ids}

        if division == 'All':
            filtered_df = unique_centers_df
        elif division == 'Other':
            filtered_df = unique_centers_df[~unique_centers_df['cost_center_id'].isin(all_known_ids)]
        else:
            # Check if division exists in Divisions dict
            if division not in self.Divisions:
                return []
            division_ids = set(self.Divisions[division])
            filtered_df = unique_centers_df[unique_centers_df['cost_center_id'].isin(division_ids)]

        # Sort by cost_center_name
        sorted_centers = filtered_df.sort_values(by='cost_center_name')

        # Return list of tuples (cost_center_id, cost_center_name)
        return list(sorted_centers.itertuples(index=False, name=None))

    def create_dashboard(self, start_date, end_date):
        df = self.filter_24_hours(start_date, end_date)
        all_anomalies = [
            'Shift is at least 4 hours longer than scheduled',
            'Forgot to clock out for at least 10 hours',
            'Clocked out at least 90 minutes early',
            'ALS/IFT earning code assigned to 911 cost center',
            'Did not punch in/PTO'
        ]
        all_divisions = list(self.Divisions.keys())

        if df is None or df.empty:
            # Return empty dashboard with zeros including 'Other'
            empty_data = {div: [0]*len(all_anomalies) for div in all_divisions}
            empty_data['Other'] = [0]*len(all_anomalies)  # Add Other column
            dashboard = pd.DataFrame(empty_data, index=all_anomalies)
            dashboard['Totals'] = dashboard.sum(axis=1)  # Add Totals column
            dashboard.loc['Actual Total'] = dashboard.sum()
            return dashboard

        # Map cost_center_id to division
        def map_division(cc_id):
            for div, ids in self.Divisions.items():
                if cc_id in ids:
                    return div
            return 'Unassigned'

        df['division'] = df['cost_center_id'].apply(map_division)

        # Count anomalies per division including 'Unassigned'
        summary = pd.crosstab(index=df['anomaly'], columns=df['division'])

        # Extract 'Unassigned' counts (if any)
        if 'Unassigned' in summary.columns:
            other_col = summary['Unassigned']
            summary = summary.drop(columns=['Unassigned'])
        else:
            other_col = pd.Series(0, index=summary.index)

        # Ensure all anomalies and all divisions present
        combined_anomalies = summary.index.union(pd.Index(all_anomalies))
        summary = summary.reindex(index=combined_anomalies, columns=all_divisions, fill_value=0)

        # Add 'Other' column with Unassigned counts aligned by anomaly index
        other_col = other_col.reindex(summary.index, fill_value=0)
        summary['Other'] = other_col

        # Add 'Totals' column summing across all divisions + Other
        summary['Totals'] = summary.sum(axis=1)

        # Add 'Actual Total' row summing everything including Totals column
        summary.loc['Actual Total'] = summary.sum()

        return summary



# if __name__ == "__main__":
#     payroll = PayrollAutomation()
#     dashboard_df = payroll.create_dashboard("2025-07-01", "2025-07-08")
#     with pd.option_context('display.max_columns', None, 'display.expand_frame_repr', False):
#      print(dashboard_df)


# payroll = PayrollAutomation()

# division_name = 'Division 2'
# division_centers = payroll.get_cost_centers(division_name)
# print(f"Cost centers for {division_name}:")
# print(division_centers)


    # dashboard_df = self.create_dashboard("2025-07-01", "2025-07-15")
    # print(dashboard_df)
