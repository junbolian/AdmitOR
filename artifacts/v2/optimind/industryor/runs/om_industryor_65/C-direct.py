import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_I   = params["demand_I"]    # list of 12 monthly demands for product I
    demand_II  = params["demand_II"]   # list of 12 monthly demands for product II
    prod_cost_I      = params["prod_cost_I"]       # cost Jan-May
    prod_cost_I_late = params["prod_cost_I_late"]  # cost Jun-Dec
    prod_cost_II      = params["prod_cost_II"]
    prod_cost_II_late = params["prod_cost_II_late"]
    cap_month  = params["cap_month"]   # combined monthly capacity
    vol_I      = params["vol_I"]
    vol_II     = params["vol_II"]
    wh_cap     = params["wh_cap"]
    hold_own   = params["hold_own"]
    hold_rent  = params["hold_rent"]

    # Months indexed 0..5 corresponding to July..December (months 7-12)
    # In the full year array, July = index 6, ..., December = index 11
    months = range(6)  # 0=Jul, 1=Aug, 2=Sep, 3=Oct, 4=Nov, 5=Dec

    # Demands for July-December (indices 6-11 of the demand arrays)
    d_I  = [demand_I[6 + t]  for t in months]
    d_II = [demand_II[6 + t] for t in months]

    # Production costs for July-December: all fall in the "late" period (Jun-Dec)
    # (prod_cost_I and prod_cost_II cover Jan-May; late covers Jun-Dec)
    c_I  = prod_cost_I_late
    c_II = prod_cost_II_late

    model = gp.Model("production_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x_I[t], x_II[t]: units produced in month t (July=0 .. December=5)
    x_I  = model.addVars(6, lb=0.0, name="x_I")
    x_II = model.addVars(6, lb=0.0, name="x_II")

    # inv_I[t], inv_II[t]: inventory at END of month t
    inv_I  = model.addVars(6, lb=0.0, name="inv_I")
    inv_II = model.addVars(6, lb=0.0, name="inv_II")

    # own_used[t]: cubic meters used in own warehouse at end of month t
    # rent_used[t]: cubic meters used in rented warehouse at end of month t
    own_used  = model.addVars(6, lb=0.0, name="own_used")
    rent_used = model.addVars(6, lb=0.0, name="rent_used")

    # Inventory balance constraints (initial inventory = 0 at start of July)
    for t in months:
        prev_I  = inv_I[t-1]  if t > 0 else 0.0
        prev_II = inv_II[t-1] if t > 0 else 0.0
        # inventory at end of month = inventory at start + production - demand
        model.addConstr(inv_I[t]  == prev_I  + x_I[t]  - d_I[t],  name=f"bal_I_{t}")
        model.addConstr(inv_II[t] == prev_II + x_II[t] - d_II[t], name=f"bal_II_{t}")

    # Combined monthly production capacity
    for t in months:
        model.addConstr(x_I[t] + x_II[t] <= cap_month, name=f"cap_{t}")

    # Warehouse constraints: total volume = own + rented; own <= wh_cap
    for t in months:
        total_vol = vol_I * inv_I[t] + vol_II * inv_II[t]
        model.addConstr(own_used[t] + rent_used[t] == total_vol, name=f"wh_total_{t}")
        model.addConstr(own_used[t] <= wh_cap, name=f"wh_own_cap_{t}")

    # Objective: minimize total production cost + storage cost
    prod_cost_expr = gp.quicksum(
        c_I * x_I[t] + c_II * x_II[t] for t in months
    )
    hold_cost_expr = gp.quicksum(
        hold_own * own_used[t] + hold_rent * rent_used[t] for t in months
    )
    model.setObjective(prod_cost_expr + hold_cost_expr, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}