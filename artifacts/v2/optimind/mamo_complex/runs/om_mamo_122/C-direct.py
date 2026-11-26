import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    cities = range(n)

    model = gp.Model()
    model.Params.OutputFlag = 0

    # x[i][j] = tons transported from city i to city j
    x = [[None] * n for _ in cities]
    for i in cities:
        for j in cities:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Each city's net outflow must not exceed its surplus (supply - demand)
    # Equivalently: supply[i] + sum_j x[j][i] >= demand[i] + sum_j x[i][j]
    # Rearranged: sum_j x[i][j] - sum_j x[j][i] <= supply[i] - demand[i]
    for i in cities:
        outflow = gp.quicksum(x[i][j] for j in cities if i != j)
        inflow = gp.quicksum(x[j][i] for j in cities if j != i)
        net_supply = supply[i] - demand[i]
        model.addConstr(outflow - inflow <= net_supply, name=f"balance_{i}")

    # Each city must meet its demand:
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    # i.e. inflow[i] - outflow[i] >= demand[i] - supply[i]
    for i in cities:
        outflow = gp.quicksum(x[i][j] for j in cities if i != j)
        inflow = gp.quicksum(x[j][i] for j in cities if j != i)
        model.addConstr(inflow - outflow >= demand[i] - supply[i], name=f"demand_{i}")

    # Objective: minimize total transportation cost
    obj = gp.quicksum(
        cost[i][j] * x[i][j]
        for i in cities
        for j in cities
        if i != j
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}