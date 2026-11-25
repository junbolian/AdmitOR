import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    pair_cap = params["pair_cap"]

    n_persons = len(availability)
    n_projects = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: hours person i assigns to project j
    x = {}
    for i in range(n_persons):
        for j in range(n_projects):
            x[i, j] = model.addVar(lb=0.0, ub=pair_cap[i][j], name=f"x_{i}_{j}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_persons) for j in range(n_projects)),
        GRB.MINIMIZE
    )

    # Availability constraints: total hours per person <= availability
    for i in range(n_persons):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_projects)) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total hours per project >= demand
    for j in range(n_projects):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_persons)) >= demand[j],
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