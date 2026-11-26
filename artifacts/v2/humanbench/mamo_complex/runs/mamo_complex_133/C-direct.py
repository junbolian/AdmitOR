import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    cities = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = tons transported from city i to city j
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{j}") for j in cities] for i in cities]

    # No self-transport
    for i in cities:
        model.addConstr(x[i][i] == 0, name=f"no_self_{i}")

    # Each city's net outflow <= surplus (can't ship more than available)
    # Supply balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in cities:
        inflow = gp.quicksum(x[j][i] for j in cities if j != i)
        outflow = gp.quicksum(x[i][j] for j in cities if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"demand_{i}")

    # Objective: minimize total transportation cost
    obj = gp.quicksum(cost[i][j] * x[i][j] for i in cities for j in cities if i != j)
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