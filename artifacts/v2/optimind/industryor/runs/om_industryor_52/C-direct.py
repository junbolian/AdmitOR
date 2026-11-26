import gurobipy as gp
from gurobipy import GRB

def solve(params):
    hours_A = params["equipment_hours_per_unit_A"]  # per-unit hours on A for products I, II, III
    hours_B = params["equipment_hours_per_unit_B"]
    hours_C = params["equipment_hours_per_unit_C"]
    cap_A = params["capacity_A"]
    cap_B = params["capacity_B"]
    cap_C = params["capacity_C"]
    profit = params["unit_profit"]  # per-unit profit for products I, II, III

    products = range(3)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(products, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(profit[j] * x[j] for j in products), GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(hours_A[j] * x[j] for j in products) <= cap_A, name="capacity_A")
    model.addConstr(gp.quicksum(hours_B[j] * x[j] for j in products) <= cap_B, name="capacity_B")
    model.addConstr(gp.quicksum(hours_C[j] * x[j] for j in products) <= cap_C, name="capacity_C")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}