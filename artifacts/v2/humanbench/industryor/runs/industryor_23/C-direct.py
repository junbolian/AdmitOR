import gurobipy as gp
from gurobipy import GRB

def solve(params):
    device_A_hours = params["device_A_hours_per_unit"]  # list of 3 values [I, II, III]
    device_B_hours = params["device_B_hours_per_unit"]
    device_C_hours = params["device_C_hours_per_unit"]
    capacity_A = params["capacity_A"]
    capacity_B = params["capacity_B"]
    capacity_C = params["capacity_C"]
    unit_profit = params["unit_profit"]  # list of 3 values [I, II, III]

    products = range(3)  # 0=I, 1=II, 2=III

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of each product to produce
    x = model.addVars(products, lb=0.0, name="x")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(unit_profit[j] * x[j] for j in products),
        GRB.MAXIMIZE
    )

    # Capacity constraints (equality — "fully utilize" the capacity)
    model.addConstr(
        gp.quicksum(device_A_hours[j] * x[j] for j in products) == capacity_A,
        name="capacity_A"
    )
    model.addConstr(
        gp.quicksum(device_B_hours[j] * x[j] for j in products) == capacity_B,
        name="capacity_B"
    )
    model.addConstr(
        gp.quicksum(device_C_hours[j] * x[j] for j in products) == capacity_C,
        name="capacity_C"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}