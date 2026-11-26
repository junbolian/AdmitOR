import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    num_cities = params["num_cities"]
    source = params["source"]
    destination = params["destination"]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    nodes = range(num_cities)

    # Flow variables for each directed edge
    flow = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                flow[i, j] = model.addVar(lb=0.0, ub=capacity[i][j], name=f"flow_{i}_{j}")

    # Maximize flow into destination
    model.setObjective(
        gp.quicksum(flow[i, destination] for i in nodes if i != destination),
        GRB.MAXIMIZE
    )

    # Flow conservation constraints for all nodes except source and destination
    for k in nodes:
        if k == source or k == destination:
            continue
        model.addConstr(
            gp.quicksum(flow[i, k] for i in nodes if i != k) ==
            gp.quicksum(flow[k, j] for j in nodes if j != k),
            name=f"conservation_{k}"
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