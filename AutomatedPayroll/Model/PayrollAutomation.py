from PayrollSQL import get_formatted_combined

class PayrollAutomation:
    results = get_formatted_combined()
    for r in results:
        print(r)