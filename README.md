# flexible_employee_scheduling
Code for Master Thesis at NTNU

# Data Structure

Employees are identified by the employee_id. This is equivalent to ScheduleRow.RowNbr - 1, as we use 0-indexing while the data is provided with 1-indexing. To get employee-specific info from a list or dict you have to use the id as an index or key.

**Variables**

    Number of weeks
    Number of employees

**Sets**

    Working hours: a list of all working hours
    Time periods with demand (any key with max `demand[key] > 0)
        Default competency
        Competency A ... Z
        Any competency

_To ble implemented_

    Preferences
    Blocked / vetos

**Dicts**
_Demand_

Demand is, for now, defined in increments of 15 minutes. This may change.

    Min demand
        Default competency
            Dict with aggregated demand for each time period with demand > 0
        Competency A
            Array with aggregated demand for each time period with demand > 0
    Ideal demand
        ...
    Max demand
        ...

_Competencies_

Competency A is the default competency. All employees have this competency.

    Competency A...Z: a dict of all employees with competency A
