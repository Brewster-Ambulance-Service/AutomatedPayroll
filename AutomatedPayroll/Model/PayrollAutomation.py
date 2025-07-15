from PayrollSQL import get_formatted_combined
import pandas as pd 
import numpy as np

"""
Class dedicated to automating the payroll process and finding outliers in shift and payroll data acquired from the PayrollSQL module.
This class uses the formatted data from PayrollSQL to perform operations such as identifying discrepancies in punch times
"""
class PayrollAutomation:

    #loading in data from PayrollSQL and saving it in a pandas dataframe to allow for easy manipulation and analysis
    shift_data = get_formatted_combined()
    shift_data_df= pd.DataFrame(shift_data)
    pd.set_option('display.max_rows', None)
    print(shift_data_df)
    # for r in results:
    #     print(r)