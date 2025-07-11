#Automated Payroll Timesheet Audit

The Automated Payroll timesheet audit is an automated payroll system that allows executives at Brewster EMS to more easily view discrepencies and errors in the punch in/punch outs of employees at the company. It enables comparison between a users clocked in hours and their assigned shifts and the diferences between that and their assigned hours per week. 

---

## 🚀 Features

- ✅ **Punch-in/Punch-out Discrepancies** — compares an employees difference in punch in and punch out time compared to 
- 🧠 **In-memory Caching** — avoids redundant queries by storing previously fetched tables.
- 🧼 **PHI Scrubbing** — automatically drops a defined list of sensitive columns when loading key clinical datasets.
- 📦 **Batch Querying** — handles large datasets by paginating MySQL reads (default: 50,000 rows per batch).
- 🔁 **Bulk Refreshing** — quickly refreshes all key Traumasoft tables at once.

---

## 📂 Primary Use Cases

- Feeding **Power BI** dashboards with clean, preloaded MySQL data.
- Running analytics on **call volume, scheduling, unit utilization**, and **trip legs** without exposing PHI.
- Supporting automated data pipelines in Brewster Ambulance's analytics ecosystem.

---

## 🔐 Sensitive Field Scrubbing

The following fields are automatically dropped from sensitive tables (like `cad_trip_legs_rev`):


