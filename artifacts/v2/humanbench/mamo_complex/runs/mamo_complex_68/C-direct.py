import gurobipy as gp
from gurobipy import GRB

def solve(params):
    stock = params["stock"]
    demand = params["demand"]

    costs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (2, 1): params["cost_21"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (3, 1): params["cost_31"],
        (3, 2): params["cost_32"],
        (3, 4): params["cost_34"],
        (4, 1): params["cost_41"],
        (4, 2): params["cost_42"],
        (4, 3): params["cost_43"],
    }

    clinics = [1, 2, 3, 4]
    arcs = list(costs.keys())

    model = gp.Model("clinic_redistribution")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(costs[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    for c in clinics:
        outflow = gp.quicksum(x[i, j] for (i, j) in arcs if i == c)
        inflow = gp.quicksum(x[i, j] for (i, j) in arcs if j == c)
        model.addConstr(
            stock[c - 1] + inflow - outflow >= demand[c - 1],
            name=f"demand_{c}"
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