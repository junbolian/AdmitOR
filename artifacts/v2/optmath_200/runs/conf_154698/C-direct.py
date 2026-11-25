import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]
    n_origins = params["n_origins"]
    n_destinations = params["n_destinations"]

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units shipped from facility i to center j
    x = [[model.addVar(lb=0.0, ub=capacity[i][j], vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
          for j in range(n_destinations)]
         for i in range(n_origins)]

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(n_origins)
                    for j in range(n_destinations)),
        GRB.MINIMIZE
    )

    # Supply constraints: each facility ships exactly its supply
    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_destinations)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: each center receives exactly its demand
    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(n_origins)) == demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}