import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_v1 = params["cost_v1"]
    cost_v2 = params["cost_v2"]
    cost_v3 = params["cost_v3"]
    cost_v4 = params["cost_v4"]
    cost_v5 = params["cost_v5"]

    model = gp.Model("vehicle_deployment")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: deploy vehicle i or not
    x1 = model.addVar(vtype=GRB.BINARY, name="x1")
    x2 = model.addVar(vtype=GRB.BINARY, name="x2")
    x3 = model.addVar(vtype=GRB.BINARY, name="x3")
    x4 = model.addVar(vtype=GRB.BINARY, name="x4")
    x5 = model.addVar(vtype=GRB.BINARY, name="x5")

    # Objective: minimize total deployment cost
    model.setObjective(
        cost_v1 * x1 + cost_v2 * x2 + cost_v3 * x3 + cost_v4 * x4 + cost_v5 * x5,
        GRB.MINIMIZE
    )

    # Coverage constraints
    # e1, e2: Vehicle 4 or Vehicle 5
    model.addConstr(x4 + x5 >= 1, name="e1")
    model.addConstr(x4 + x5 >= 1, name="e2")
    # e3: Vehicle 3
    model.addConstr(x3 >= 1, name="e3")
    # e4: Vehicle 1 or Vehicle 2
    model.addConstr(x1 + x2 >= 1, name="e4")
    # e5: Vehicle 1, 2, or 4
    model.addConstr(x1 + x2 + x4 >= 1, name="e5")
    # e6: Vehicle 1, 3, or 4
    model.addConstr(x1 + x3 + x4 >= 1, name="e6")
    # e7: Vehicle 3, 4, or 5
    model.addConstr(x3 + x4 + x5 >= 1, name="e7")
    # e8: Vehicle 3 or 4
    model.addConstr(x3 + x4 >= 1, name="e8")
    # e9: Vehicle 1, 2, or 3
    model.addConstr(x1 + x2 + x3 >= 1, name="e9")
    # e10: Vehicle 3, 4, or 5
    model.addConstr(x3 + x4 + x5 >= 1, name="e10")
    # e11: Vehicle 3 or 5
    model.addConstr(x3 + x5 >= 1, name="e11")
    # e12: Vehicle 1
    model.addConstr(x1 >= 1, name="e12")
    # e13: Vehicle 1, 4, or 5
    model.addConstr(x1 + x4 + x5 >= 1, name="e13")
    # e14: Vehicle 3 or 4
    model.addConstr(x3 + x4 >= 1, name="e14")
    # e15: Vehicle 1, 2, or 5
    model.addConstr(x1 + x2 + x5 >= 1, name="e15")
    # e16: Vehicle 1 or 2
    model.addConstr(x1 + x2 >= 1, name="e16")
    # e17: Vehicle 2
    model.addConstr(x2 >= 1, name="e17")
    # e18: Vehicle 5
    model.addConstr(x5 >= 1, name="e18")
    # e19: Vehicle 1 or 4
    model.addConstr(x1 + x4 >= 1, name="e19")
    # e20: Vehicle 2
    model.addConstr(x2 >= 1, name="e20")
    # e21: Vehicle 3, 4, or 5
    model.addConstr(x3 + x4 + x5 >= 1, name="e21")
    # e22: Vehicle 5
    model.addConstr(x5 >= 1, name="e22")
    # e23: Vehicle 1 or 4
    model.addConstr(x1 + x4 >= 1, name="e23")
    # e24: Vehicle 2 or 5
    model.addConstr(x2 + x5 >= 1, name="e24")
    # e25: Vehicle 1, 3, or 5
    model.addConstr(x1 + x3 + x5 >= 1, name="e25")
    # e26: Vehicle 1, 2, or 3
    model.addConstr(x1 + x2 + x3 >= 1, name="e26")
    # e27: Vehicle 5
    model.addConstr(x5 >= 1, name="e27")
    # e28: Vehicle 2 or 4
    model.addConstr(x2 + x4 >= 1, name="e28")
    # e29: Vehicle 1 or 3
    model.addConstr(x1 + x3 >= 1, name="e29")
    # e30: Vehicle 5
    model.addConstr(x5 >= 1, name="e30")
    # e31: Vehicle 1 or 3
    model.addConstr(x1 + x3 >= 1, name="e31")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}