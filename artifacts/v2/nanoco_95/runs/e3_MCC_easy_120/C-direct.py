import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coordinates = params["coordinates"]
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    costs = params["costs"]

    # Pipeline definitions: (from_unit, to_unit)
    pipelines = [
        (0, 1), (0, 3), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 6),
        (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 2), (4, 3), (4, 5),
        (5, 4), (5, 6),
        (6, 0), (6, 5),
    ]

    n_pipelines = len(pipelines)
    n_units = 7

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for idx in range(n_pipelines):
        lb = lower_bounds[idx]
        ub = upper_bounds[idx]
        flow[idx] = model.addVar(lb=lb, ub=ub, name=f"flow_{idx}")

    model.update()

    # Flow balance constraints: inflow == outflow at each unit
    for unit in range(n_units):
        inflow = gp.LinExpr()
        outflow = gp.LinExpr()
        for idx, (src, dst) in enumerate(pipelines):
            if dst == unit:
                inflow += flow[idx]
            if src == unit:
                outflow += flow[idx]
        model.addConstr(inflow == outflow, name=f"balance_{unit}")

    # Objective: minimize total pumping energy cost
    obj = gp.LinExpr()
    for idx in range(n_pipelines):
        obj += costs[idx] * flow[idx]
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