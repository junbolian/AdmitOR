import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    distance_cost = params["distance_cost"]
    num_neighborhoods = params["num_neighborhoods"]
    num_candidates = params["num_candidates"]

    neighborhoods = range(num_neighborhoods)
    candidates = range(num_candidates)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if neighborhood i is assigned to warehouse j
    x = model.addVars(neighborhoods, candidates, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if warehouse j is opened
    y = model.addVars(candidates, vtype=GRB.BINARY, name="y")

    # Objective: minimize fixed costs + delivery costs
    model.setObjective(
        gp.quicksum(fixed_cost[j] * y[j] for j in candidates) +
        gp.quicksum(distance_cost[i][j] * x[i, j] for i in neighborhoods for j in candidates),
        GRB.MINIMIZE
    )

    # Each neighborhood assigned to exactly one warehouse
    for i in neighborhoods:
        model.addConstr(gp.quicksum(x[i, j] for j in candidates) == 1, name=f"assign_{i}")

    # Assignment only to open warehouses
    for i in neighborhoods:
        for j in candidates:
            model.addConstr(x[i, j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}