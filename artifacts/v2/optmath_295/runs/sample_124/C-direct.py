import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]

    n_persons = 8
    n_projects = 8
    persons = range(n_persons)
    projects = range(n_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_persons, n_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(costs[i][j] * x[i, j] for i in persons for j in projects),
        GRB.MINIMIZE
    )

    for i in persons:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == supply[i],
            name=f"supply_{i}"
        )

    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in persons) == demand[j],
            name=f"demand_{j}"
        )

    for i in persons:
        for j in projects:
            model.addConstr(x[i, j] <= capacity_limits[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}