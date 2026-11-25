import gurobipy as gp
from gurobipy import GRB

def solve(params):
    resource_weights = params["resource_weights"]
    facility_capacity = params["facility_capacity"]

    n_resources = len(resource_weights)
    n_facilities = len(resource_weights)  # 7 facilities

    model = gp.Model("resource_allocation")
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if resource i is assigned to facility j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(n_facilities)]
         for i in range(n_resources)]

    # y[j] = 1 if facility j is used
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}")
         for j in range(n_facilities)]

    # Objective: minimize number of facilities used
    model.setObjective(gp.quicksum(y[j] for j in range(n_facilities)), GRB.MINIMIZE)

    # Each resource must be assigned to exactly one facility
    for i in range(n_resources):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_facilities)) == 1,
            name=f"assign_{i}"
        )

    # Capacity constraints: total weight at facility j <= capacity * y[j]
    for j in range(n_facilities):
        model.addConstr(
            gp.quicksum(resource_weights[i] * x[i][j] for i in range(n_resources)) <= facility_capacity * y[j],
            name=f"capacity_{j}"
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