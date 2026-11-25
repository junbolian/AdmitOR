import gurobipy as gp
from gurobipy import GRB

def solve(params):
    flow = params["flow"]
    distance = params["distance"]

    n = 4
    workstations = range(n)
    locations = range(n)

    model = gp.Model("QAP")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if workstation i is assigned to location j
    x = model.addVars(workstations, locations, vtype=GRB.BINARY, name="x")

    # Each workstation assigned to exactly one location
    for i in workstations:
        model.addConstr(gp.quicksum(x[i, j] for j in locations) == 1)

    # Each location holds exactly one workstation
    for j in locations:
        model.addConstr(gp.quicksum(x[i, j] for i in workstations) == 1)

    # Linearize the quadratic objective using auxiliary variables
    # y[i, k, j, l] = x[i,j] * x[k,l], cost = flow[i,k] * distance[j,l]
    y = model.addVars(workstations, workstations, locations, locations,
                      vtype=GRB.BINARY, name="y")

    for i in workstations:
        for k in workstations:
            for j in locations:
                for l in locations:
                    model.addConstr(y[i, k, j, l] <= x[i, j])
                    model.addConstr(y[i, k, j, l] <= x[k, l])
                    model.addConstr(y[i, k, j, l] >= x[i, j] + x[k, l] - 1)

    obj = gp.quicksum(
        flow[i][k] * distance[j][l] * y[i, k, j, l]
        for i in workstations
        for k in workstations
        for j in locations
        for l in locations
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}