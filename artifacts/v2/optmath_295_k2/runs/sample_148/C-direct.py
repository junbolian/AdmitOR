import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]

    # Support both "capacity"/"capacities" and "cost"/"costs" key names,
    # and both nested-dict and flat {(a,r): val} structures.
    capacity_raw = params.get("capacity") or params.get("capacities") or params.get("cap")
    cost_raw = params.get("cost") or params.get("costs") or params.get("obj") or params.get("objective_coeff")

    if capacity_raw is None:
        raise KeyError("No capacity matrix found in params. Available keys: " + str(list(params.keys())))
    if cost_raw is None:
        raise KeyError("No cost matrix found in params. Available keys: " + str(list(params.keys())))

    aircraft_types = list(availability.keys())
    routes = list(demand.keys())

    # Normalize capacity and cost to nested dict: data[a][r]
    def normalize_matrix(raw, aircraft_types, routes):
        # Already nested dict keyed by aircraft then route
        if isinstance(raw, dict):
            first_val = next(iter(raw.values()))
            if isinstance(first_val, dict):
                return raw
            # Flat dict keyed by (a, r) tuples
            if isinstance(next(iter(raw.keys())), tuple):
                nested = {a: {} for a in aircraft_types}
                for (a, r), val in raw.items():
                    nested[a][r] = val
                return nested
            # Flat dict keyed by "aircraft_X_route_Y" strings or similar
            nested = {a: {} for a in aircraft_types}
            for key, val in raw.items():
                for a in aircraft_types:
                    for r in routes:
                        if key == f"{a}_{r}" or key == f"{a},{r}":
                            nested[a][r] = val
            return nested
        # List of lists: rows = aircraft, cols = routes
        if isinstance(raw, list):
            nested = {}
            for i, a in enumerate(aircraft_types):
                nested[a] = {}
                for j, r in enumerate(routes):
                    nested[a][r] = raw[i][j]
            return nested
        raise ValueError("Unrecognized matrix structure: " + str(type(raw)))

    capacity = normalize_matrix(capacity_raw, aircraft_types, routes)
    cost = normalize_matrix(cost_raw, aircraft_types, routes)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: number of aircraft of type a assigned to route r
    x = {}
    for a in aircraft_types:
        for r in routes:
            x[a, r] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{a}_{r}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[a][r] * x[a, r] for a in aircraft_types for r in routes),
        GRB.MINIMIZE
    )

    # Aircraft availability constraints
    for a in aircraft_types:
        model.addConstr(
            gp.quicksum(x[a, r] for r in routes) <= availability[a],
            name=f"avail_{a}"
        )

    # Route demand constraints
    for r in routes:
        model.addConstr(
            gp.quicksum(capacity[a][r] * x[a, r] for a in aircraft_types) >= demand[r],
            name=f"demand_{r}"
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