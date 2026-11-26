import gurobipy as gp
from gurobipy import GRB

def solve(params):
    raw_material_cost = params["raw_material_cost"]
    labor_hours_per_unit = params["labor_hours_per_unit"]
    unit_price = params["unit_price"]
    initial_workers = params["initial_workers"]
    initial_inventory = params["initial_inventory"]
    normal_wage = params["normal_wage"]
    normal_hours_per_day = params["normal_hours_per_day"]
    overtime_wage = params["overtime_wage"]
    working_days_per_month = params["working_days_per_month"]
    max_overtime_hours_per_worker = params["max_overtime_hours_per_worker"]
    outsourcing_cost = params["outsourcing_cost"]
    inventory_cost = params["inventory_cost"]
    stockout_cost = params["stockout_cost"]
    hiring_cost = params["hiring_cost"]
    firing_cost = params["firing_cost"]
    demand = params["demand"]  # list of 6 values
    min_final_inventory = params["min_final_inventory"]

    T = 6
    months = range(T)  # 0..5

    # Normal production capacity per worker per month (hours)
    normal_hours_per_month = normal_hours_per_day * working_days_per_month

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # workers[t]: number of workers in month t
    workers = model.addVars(T, name="workers", lb=0, vtype=GRB.INTEGER)
    # hire[t]: workers hired at start of month t
    hire = model.addVars(T, name="hire", lb=0, vtype=GRB.INTEGER)
    # fire[t]: workers fired at start of month t
    fire = model.addVars(T, name="fire", lb=0, vtype=GRB.INTEGER)
    # overtime_hours[t]: total overtime hours used in month t (across all workers)
    overtime_hours = model.addVars(T, name="overtime_hours", lb=0)
    # produce[t]: units produced in month t (normal + overtime)
    produce = model.addVars(T, name="produce", lb=0)
    # outsource[t]: units outsourced in month t
    outsource = model.addVars(T, name="outsource", lb=0)
    # inventory[t]: ending inventory at end of month t (non-negative means surplus)
    inventory = model.addVars(T, name="inventory", lb=0)
    # stockout[t]: unmet demand at end of month t
    stockout = model.addVars(T, name="stockout", lb=0)

    # Worker dynamics
    for t in months:
        if t == 0:
            model.addConstr(workers[t] == initial_workers + hire[t] - fire[t],
                            name=f"worker_balance_{t}")
        else:
            model.addConstr(workers[t] == workers[t-1] + hire[t] - fire[t],
                            name=f"worker_balance_{t}")

    # Overtime hours constraint per worker per month
    for t in months:
        model.addConstr(overtime_hours[t] <= max_overtime_hours_per_worker * workers[t],
                        name=f"max_overtime_{t}")

    # Production capacity: units produced = (normal hours + overtime hours) / labor_hours_per_unit
    for t in months:
        normal_capacity_hours = normal_hours_per_month * workers[t]
        model.addConstr(
            produce[t] * labor_hours_per_unit <= normal_capacity_hours + overtime_hours[t],
            name=f"prod_capacity_{t}"
        )

    # Inventory / stockout balance
    for t in months:
        prev_inv = initial_inventory if t == 0 else inventory[t-1]
        prev_stock = 0 if t == 0 else stockout[t-1]
        d = demand[t]
        # supply = prev_inv - prev_stockout + produce + outsource
        # if supply >= demand: inventory[t] = supply - demand, stockout[t] = 0
        # if supply < demand: stockout[t] = demand - supply, inventory[t] = 0
        model.addConstr(
            inventory[t] - stockout[t] == prev_inv - prev_stock + produce[t] + outsource[t] - d,
            name=f"inv_balance_{t}"
        )

    # Minimum final inventory requirement
    model.addConstr(inventory[T-1] >= min_final_inventory, name="min_final_inv")

    # Objective: maximize total net profit
    # Revenue - raw material cost - labor cost (normal + overtime) - outsourcing cost
    #         - inventory cost - stockout cost - hiring cost - firing cost

    revenue = gp.quicksum(unit_price * (demand[t] - stockout[t] + 0) for t in months)
    # Actually, revenue = price * units sold = price * (demand satisfied)
    # Units sold in month t = demand[t] - stockout[t]
    revenue = gp.quicksum(unit_price * (demand[t] - stockout[t]) for t in months)

    raw_mat_cost_total = gp.quicksum(raw_material_cost * produce[t] for t in months)

    normal_labor_cost = gp.quicksum(
        normal_wage * normal_hours_per_month * workers[t] for t in months
    )
    overtime_labor_cost = gp.quicksum(overtime_wage * overtime_hours[t] for t in months)

    outsource_cost_total = gp.quicksum(outsourcing_cost * outsource[t] for t in months)

    inv_cost_total = gp.quicksum(inventory_cost * inventory[t] for t in months)

    stockout_cost_total = gp.quicksum(stockout_cost * stockout[t] for t in months)

    hire_cost_total = gp.quicksum(hiring_cost * hire[t] for t in months)
    fire_cost_total = gp.quicksum(firing_cost * fire[t] for t in months)

    total_profit = (
        revenue
        - raw_mat_cost_total
        - normal_labor_cost
        - overtime_labor_cost
        - outsource_cost_total
        - inv_cost_total
        - stockout_cost_total
        - hire_cost_total
        - fire_cost_total
    )

    model.setObjective(total_profit, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}