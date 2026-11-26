import gurobipy as gp
from gurobipy import GRB

def solve(params):
    microwave_processing_hours_A = params["microwave_processing_hours_A"]
    water_heater_processing_hours_A = params["water_heater_processing_hours_A"]
    microwave_assembly_hours_B = params["microwave_assembly_hours_B"]
    water_heater_assembly_hours_B = params["water_heater_assembly_hours_B"]
    inspection_sales_cost_microwave = params["inspection_sales_cost_microwave"]
    inspection_sales_cost_water_heater = params["inspection_sales_cost_water_heater"]
    workshop_A_hours_available = params["workshop_A_hours_available"]
    workshop_B_hours_available = params["workshop_B_hours_available"]
    workshop_A_hour_cost = params["workshop_A_hour_cost"]
    workshop_B_hour_cost = params["workshop_B_hour_cost"]
    max_sales_microwave = params["max_sales_microwave"]
    max_sales_water_heater = params["max_sales_water_heater"]
    min_sales_microwave = params["min_sales_microwave"]
    min_sales_water_heater = params["min_sales_water_heater"]
    inspection_sales_budget = params["inspection_sales_budget"]
    workshop_A_overtime_cap = params["workshop_A_overtime_cap"]

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables: production quantities
    x = model.addVar(lb=0, name="microwave")
    y = model.addVar(lb=0, name="water_heater")

    # Overtime variables (non-negative by lb=0)
    oa = model.addVar(lb=0, name="overtime_A")
    ob = model.addVar(lb=0, name="overtime_B")

    # Total hours used in each workshop
    # hours_A = microwave_processing_hours_A * x + water_heater_processing_hours_A * y
    # hours_B = microwave_assembly_hours_B * x + water_heater_assembly_hours_B * y

    # Objective: minimize total cost (workshop hours + inspection/sales)
    # Total workshop A cost: cost per hour * (regular + overtime hours used)
    # Total workshop B cost: cost per hour * (regular + overtime hours used)
    # Inspection/sales cost per unit
    obj = (workshop_A_hour_cost * (microwave_processing_hours_A * x + water_heater_processing_hours_A * y) +
           workshop_B_hour_cost * (microwave_assembly_hours_B * x + water_heater_assembly_hours_B * y) +
           inspection_sales_cost_microwave * x +
           inspection_sales_cost_water_heater * y)

    model.setObjective(obj, GRB.MINIMIZE)

    # Workshop A: hours used = available + overtime (overtime tracks excess over regular capacity)
    # This means: hours_used - overtime_A = workshop_A_hours_available
    # Since overtime_A >= 0, hours_used >= workshop_A_hours_available ("fully utilized")
    model.addConstr(
        microwave_processing_hours_A * x + water_heater_processing_hours_A * y - oa == workshop_A_hours_available,
        name="workshop_A_utilization"
    )

    # Workshop B: hours used = available + overtime
    model.addConstr(
        microwave_assembly_hours_B * x + water_heater_assembly_hours_B * y - ob == workshop_B_hours_available,
        name="workshop_B_utilization"
    )

    # Overtime cap for workshop A
    model.addConstr(oa <= workshop_A_overtime_cap, name="overtime_A_cap")

    # Sales upper bounds (market capacity)
    model.addConstr(x <= max_sales_microwave, name="max_microwave_sales")
    model.addConstr(y <= max_sales_water_heater, name="max_water_heater_sales")

    # Sales lower bounds (minimum required)
    model.addConstr(x >= min_sales_microwave, name="min_microwave_sales")
    model.addConstr(y >= min_sales_water_heater, name="min_water_heater_sales")

    # Inspection and sales budget constraint
    model.addConstr(
        inspection_sales_cost_microwave * x + inspection_sales_cost_water_heater * y <= inspection_sales_budget,
        name="inspection_sales_budget_cap"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}