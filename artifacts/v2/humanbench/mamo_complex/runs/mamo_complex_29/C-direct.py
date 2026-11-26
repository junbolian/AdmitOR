import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    regions = range(n)

    model = gp.Model("medical_supply_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units shipped from region i to region j
    x = [[model.addVar(lb=0, name=f"x_{i}_{j}") for j in regions] for i in regions]

    # Self-shipping forced to 0
    for i in regions:
        x[i][i].ub = 0

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i][j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Supply constraint: units shipped out of i <= supply[i] + units shipped in
    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in regions:
        inflow = gp.quicksum(x[j][i] for j in regions if j != i)
        outflow = gp.quicksum(x[i][j] for j in regions if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"demand_{i}")
        model.addConstr(outflow <= supply[i] + inflow, name=f"supply_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}