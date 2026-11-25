import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    aircraft_types = ["aircraft_0", "aircraft_1", "aircraft_2", "aircraft_3", "aircraft_4"]
    routes = ["route_0", "route_1", "route_2", "route_3", "route_4", "route_5"]

    # Normalize capacity and cost to nested dicts if they are not already.
    # They may arrive as lists-of-lists, dicts-of-dicts, or dicts keyed by
    # "aircraft_i" -> {"route_j": value}.
    def to_nested_dict(matrix, row_keys, col_keys):
        # Already a dict of dicts
        if isinstance(matrix, dict):
            return matrix
        # List of lists (row-major, len == len(row_keys))
        if isinstance(matrix, list):
            result = {}
            for ri, row in enumerate(matrix):
                rk = row_keys[ri]
                result[rk] = {}
                if isinstance(row, list):
                    for ci, val in enumerate(row):
                        result[rk][col_keys[ci]] = val
                elif isinstance(row, dict):
                    result[rk] = row
            return result
        return matrix

    capacity = to_nested_dict(capacity, aircraft_types, routes)
    cost = to_nested_dict(cost, aircraft_types, routes)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in aircraft_types:
        for j in routes:
            x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    obj_expr = gp.LinExpr()
    for i in aircraft_types:
        for j in routes:
            c = None
            if isinstance(cost, dict):
                row = cost.get(i, {})
                if isinstance(row, dict):
                    c = row.get(j)
                elif isinstance(row, list):
                    ji = routes.index(j)
                    c = row[ji] if ji < len(row) else None
            if c is not None:
                obj_expr += c * x[i, j]
    model.setObjective(obj_expr, GRB.MINIMIZE)

    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in routes) <= availability[i],
            name=f"avail_{i}"
        )

    for j in routes:
        cap_expr = gp.LinExpr()
        for i in aircraft_types:
            cap_val = None
            if isinstance(capacity, dict):
                row = capacity.get(i, {})
                if isinstance(row, dict):
                    cap_val = row.get(j)
                elif isinstance(row, list):
                    ji = routes.index(j)
                    cap_val = row[ji] if ji < len(row) else None
            if cap_val is not None:
                cap_expr += cap_val * x[i, j]
        model.addConstr(cap_expr >= demand[j], name=f"demand_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.objVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}