import gurobipy as gp
from gurobipy import GRB

def solve(params):
    flow_raw = params["flow"]
    distance_raw = params["distance"]
    n_departments = params["n_departments"]
    n_zones = params["n_zones"]

    # Normalize flow and distance to callable f(i,j) regardless of input shape
    def to_matrix(raw, n):
        # If it's a list of lists, return as-is accessor
        if hasattr(raw, '__getitem__'):
            first = raw[0] if len(raw) > 0 else None
            if hasattr(first, '__getitem__') and not isinstance(first, (int, float)):
                # list of lists
                return lambda i, j: raw[i][j]
            else:
                # flat list, row-major
                return lambda i, j: raw[i * n + j]
        raise ValueError("Unrecognized matrix format")

    flow = to_matrix(flow_raw, n_departments)
    distance = to_matrix(distance_raw, n_zones)

    departments = range(n_departments)
    zones = range(n_zones)

    model = gp.Model("mall_layout")
    model.setParam("OutputFlag", 0)

    # x[i, k] = 1 if department i is assigned to zone k
    x = model.addVars(departments, zones, vtype=GRB.BINARY, name="x")

    # Each department assigned to exactly one zone
    for i in departments:
        model.addConstr(gp.quicksum(x[i, k] for k in zones) == 1, name=f"dept_{i}")

    # Each zone holds exactly one department
    for k in zones:
        model.addConstr(gp.quicksum(x[i, k] for i in departments) == 1, name=f"zone_{k}")

    # Linearize x[i,k] * x[j,l] with binary y[i,j,k,l]
    pairs = [(i, j, k, l)
             for i in departments
             for j in departments
             for k in zones
             for l in zones]

    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    for i in departments:
        for j in departments:
            for k in zones:
                for l in zones:
                    model.addConstr(y[i, j, k, l] <= x[i, k])
                    model.addConstr(y[i, j, k, l] <= x[j, l])
                    model.addConstr(y[i, j, k, l] >= x[i, k] + x[j, l] - 1)

    obj = gp.quicksum(
        flow(i, j) * distance(k, l) * y[i, j, k, l]
        for i in departments
        for j in departments
        for k in zones
        for l in zones
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