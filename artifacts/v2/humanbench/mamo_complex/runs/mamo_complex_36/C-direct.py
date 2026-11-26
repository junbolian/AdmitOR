import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = 6
    regions = range(n)

    model = gp.Model("food_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units shipped from region i to region j
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: total outflow from region i <= supply[i]
    # (a region can keep surplus; it just can't ship more than it has)
    for i in regions:
        model.addConstr(
            gp.quicksum(x[i, j] for j in regions if i != j) <= supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: each region must receive enough to cover its needs
    # inflow + own supply >= demand  =>  inflow >= demand - supply (if positive)
    for j in regions:
        model.addConstr(
            gp.quicksum(x[i, j] for i in regions if i != j) >= max(0, demand[j] - supply[j]),
            name=f"demand_{j}"
        )

    # Also ensure a region does not ship out more than what it has after covering its own demand
    # Tighter: outflow from i <= supply[i] - demand[i] when supply[i] >= demand[i],
    # but we also allow receiving and re-shipping. Use a combined flow constraint:
    # outflow[i] <= supply[i] - demand[i] + inflow[i]
    for i in regions:
        outflow = gp.quicksum(x[i, j] for j in regions if i != j)
        inflow = gp.quicksum(x[j, i] for j in regions if i != j)
        model.addConstr(outflow <= supply[i] - demand[i] + inflow, name=f"capacity_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}