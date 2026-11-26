import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_supplies = params["initial_supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = 4
    cities = range(n)

    model = gp.Model("vaccine_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = vaccines transported from city i to city j
    x = [[model.addVar(lb=0, name=f"x_{i}_{j}") for j in cities] for i in cities]

    # Diagonal must be zero (no self-transport)
    for i in cities:
        model.addConstr(x[i][i] == 0)

    # Flow balance: each city's supply + inflow - outflow >= demand
    for i in cities:
        inflow = gp.quicksum(x[j][i] for j in cities if j != i)
        outflow = gp.quicksum(x[i][j] for j in cities if j != i)
        model.addConstr(
            initial_supplies[i] + inflow - outflow >= demands[i],
            name=f"demand_{i}"
        )

    # Objective: minimize total transport cost
    obj = gp.quicksum(
        transport_costs[i][j] * x[i][j]
        for i in cities for j in cities if i != j
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