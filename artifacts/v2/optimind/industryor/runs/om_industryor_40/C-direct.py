import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a = params["a"]  # hours required by method 1 per furnace
    b = params["b"]  # hours required by method 2 per furnace
    m = params["m"]  # fuel cost of method 1 per furnace
    n = params["n"]  # fuel cost of method 2 per furnace
    k = params["k"]  # tons of steel produced per furnace
    d = params["d"]  # minimum total tons of steel required
    c = params["c"]  # total available hours

    model = gp.Model("steel_furnace")
    model.setParam("OutputFlag", 0)

    # x1: number of furnaces using method 1
    # x2: number of furnaces using method 2
    x1 = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x1")
    x2 = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x2")

    # Objective: minimize total fuel cost
    model.setObjective(m * x1 + n * x2, GRB.MINIMIZE)

    # Steel production constraint: total tons >= d
    model.addConstr(k * x1 + k * x2 >= d, name="steel_demand")

    # Time constraint: total hours <= c
    model.addConstr(a * x1 + b * x2 <= c, name="time_limit")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}