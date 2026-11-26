import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # list of 6 values
    demand = params["demand"]  # list of 6 values
    cost = params["cost"]      # 6x6 matrix (diagonal entries unused)

    n = 6
    regions = range(n)

    model = gp.Model("emergency_food_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units shipped from region i to region j
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: net outflow from region i <= surplus (supply[i] - demand[i] if positive)
    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in regions:
        inflow = gp.quicksum(x[j, i] for j in regions if j != i)
        outflow = gp.quicksum(x[i, j] for j in regions if j != i)
        # Each region must end up with at least its demand
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"demand_{i}")
        # Cannot ship out more than available (supply + inflow)
        # This is implicitly handled since x >= 0 and the demand constraint ensures
        # we don't send more than we have; add explicit supply capacity constraint:
        model.addConstr(outflow <= supply[i] + inflow, name=f"supply_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}