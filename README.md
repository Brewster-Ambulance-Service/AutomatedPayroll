# AutomatedPayroll

The `AutomatedPayroll` is a gui based native hosting python app built to detect and label anomalies in the Brewster Ambulance Service Payroll period depending on the pay period dating back to the last 4-5 pay periods. It detects anomalies, classifies them, and is able to filter them according to specification.

---

## 🚀 Features

- ✅ **Anomaly Detection** - labels all anomalies in the pay period with one of 4 different anomaly labels as specified in user stories
- 🧠 **In-memory Caching** — caches the data by the day to prevent repeated querying
- 🧼 **Filtering** - ability to filter the data for the pay period, by anomaly, divison, or the cost center to allow supervisor managing
- 📦 **Batch Querying** — only queries the last 1.5 months worth of data

---

## 📂 Primary Use Cases

- Allowing Supervisors at cost centers and sites, as well as Weymouthe staff have a high level look at discrepoancies
- allows cost saving measures by able to look at and change timecards with proper management 
- Helps force looking at employee timecard rather than auto-approve

