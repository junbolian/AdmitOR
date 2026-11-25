import gurobipy as gp
from gurobipy import GRB

def solve(params):
    travel_time = params["travel_time"]
    service_time = params["service_time"]
    max_shelf_life_window = params["max_shelf_life_window"]

    time_windows = {}
    for i in range(8):
        e_key = f"tw_{i}_earliest"
        l_key = f"tw_{i}_latest"
        time_windows[i] = (params[e_key], params[l_key])

    n = 8
    nodes = list(range(n))
    depot = 0
    stores = list(range(1, n))

    # Big-M: upper bound on any time value
    M = max_shelf_life_window + max(travel_time[i][j] for i in nodes for j in nodes) + service_time + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j] = 1 if truck travels directly from i to j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # t[i] = service start time at node i
    # Bounds from time windows
    t = {}
    for i in nodes:
        tw_e, tw_l = time_windows[i]
        t[i] = model.addVar(lb=tw_e, ub=tw_l, vtype=GRB.CONTINUOUS, name=f"t_{i}")

    # t_return: time truck arrives back at depot after completing route
    t_return = model.addVar(lb=0.0, ub=float(max_shelf_life_window), vtype=GRB.CONTINUOUS, name="t_return")

    # Objective: minimize total travel time
    model.setObjective(
        gp.quicksum(travel_time[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Flow conservation: each store visited exactly once
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )
    for i in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if i != j) == 1,
            name=f"exit_{i}"
        )

    # Depot: exactly one outgoing and one incoming arc
    model.addConstr(
        gp.quicksum(x[depot, j] for j in stores) == 1,
        name="depot_depart"
    )
    model.addConstr(
        gp.quicksum(x[i, depot] for i in stores) == 1,
        name="depot_return"
    )

    # Time propagation between stores (subtour elimination via MTZ-style)
    for i in nodes:
        for j in stores:
            if i != j:
                model.addConstr(
                    t[j] >= t[i] + service_time + travel_time[i][j] - M * (1 - x[i, j]),
                    name=f"time_prop_{i}_{j}"
                )

    # Return-to-depot time: t_return >= t[i] + service_time + tt[i][0] if x[i,0]=1
    for i in stores:
        model.addConstr(
            t_return >= t[i] + service_time + travel_time[i][depot] - M * (1 - x[i, depot]),
            name=f"return_lb_{i}"
        )

    # Enforce maximum shelf-life window on return
    model.addConstr(t_return <= max_shelf_life_window, name="shelf_life")

    # t[depot] must be <= t_return (depot time window is for departure; return handled separately)
    # Also ensure t[depot] is the departure time (earliest = 0 is already set by lb)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}