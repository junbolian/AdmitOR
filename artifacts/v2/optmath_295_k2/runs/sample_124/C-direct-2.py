import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]
    costs = params["costs"]

    num_individuals = 8
    num_projects = 8
    individuals = range(num_individuals)
    projects = range(num_projects)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_individuals, num_projects, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(costs[i][j] * x[i, j] for i in individuals for j in projects),
        GRB.MINIMIZE
    )

    for i in individuals:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == supply[i],
            name=f"supply_{i}"
        )

    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in individuals) == demand[j],
            name=f"demand_{j}"
        )

    for i in individuals:
        for j in projects:
            model.addConstr(
                x[i, j] <= capacity_limits[i][j],
                name=f"cap_{i}_{j}"
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