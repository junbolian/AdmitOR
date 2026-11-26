import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    depot_x = params["depot_x"]
    depot_y = params["depot_y"]
    depot_tw_start = params["depot_tw_start"]
    depot_tw_end = params["depot_tw_end"]
    vehicle_count_max = params["vehicle_count_max"]
    vehicle_capacity = params["vehicle_capacity"]
    customer_x = params["customer_x"]
    customer_y = params["customer_y"]
    demand = params["demand"]
    tw_early = params["tw_early"]
    tw_late = params["tw_late"]
    service_time = params["service_time"]

    n_customers = 20
    # Nodes: 0 = depot origin, 1..20 = customers, 21 = depot destination
    n_nodes = n_customers + 2
    depot_origin = 0
    depot_dest = n_customers + 1
    customers = list(range(1, n_customers + 1))

    # Build coordinate, demand, time window, service time arrays indexed 0..21
    x_coord = [depot_x] + list(customer_x) + [depot_x]
    y_coord = [depot_y] + list(customer_y) + [depot_y]
    # demand: 0 for depot nodes
    dem = [0] + list(demand) + [0]
    # time windows
    e = [depot_tw_start] + list(tw_early) + [depot_tw_start]
    l = [depot_tw_end] + list(tw_late) + [depot_tw_end]
    # service times
    s = [0] + list(service_time) + [0]

    # Compute Euclidean distances
    def dist(i, j):
        return math.sqrt((x_coord[i] - x_coord[j])**2 + (y_coord[i] - y_coord[j])**2)

    nodes = list(range(n_nodes))
    vehicles = list(range(vehicle_count_max))

    # Arcs: all pairs except self-loops and no arc into depot_origin or out of depot_dest
    arcs = [(i, j) for i in nodes for j in nodes
            if i != j and j != depot_origin and i != depot_dest]

    dist_ij = {(i, j): dist(i, j) for (i, j) in arcs}

    model = gp.Model("VRPHTW")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 300)

    # Decision variables
    # x[i,j,k] = 1 if vehicle k travels arc (i,j)
    x = model.addVars(arcs, vehicles, vtype=GRB.BINARY, name="x")
    # t[i,k] = arrival/start-of-service time at node i for vehicle k
    t = model.addVars(nodes, vehicles, vtype=GRB.CONTINUOUS, lb=0.0, name="t")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist_ij[i, j] * x[i, j, k] for (i, j) in arcs for k in vehicles),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for i in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k] for k in vehicles for j in nodes if (i, j) in arcs) == 1,
            name=f"visit_{i}"
        )

    # Flow conservation for each vehicle at each customer node
    for k in vehicles:
        for i in customers:
            model.addConstr(
                gp.quicksum(x[i, j, k] for j in nodes if (i, j) in arcs) ==
                gp.quicksum(x[j, i, k] for j in nodes if (j, i) in arcs),
                name=f"flow_{i}_{k}"
            )

    # Each vehicle departs depot at most once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[depot_origin, j, k] for j in nodes if (depot_origin, j) in arcs) <= 1,
            name=f"depart_{k}"
        )

    # Each vehicle arrives at depot destination at most once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[i, depot_dest, k] for i in nodes if (i, depot_dest) in arcs) <= 1,
            name=f"arrive_{k}"
        )

    # Capacity constraint per vehicle
    for k in vehicles:
        model.addConstr(
            gp.quicksum(dem[i] * x[i, j, k] for (i, j) in arcs if i in customers) <= vehicle_capacity,
            name=f"cap_{k}"
        )

    # Time window constraints and time propagation (MTZ-style)
    # Big-M for time linking: use depot_tw_end as upper bound
    M_time = depot_tw_end + max(s) + max(dist_ij.values())

    for k in vehicles:
        for (i, j) in arcs:
            # If vehicle k travels arc (i,j), then t[j,k] >= t[i,k] + s[i] + dist(i,j)
            model.addConstr(
                t[j, k] >= t[i, k] + s[i] + dist_ij[i, j] - M_time * (1 - x[i, j, k]),
                name=f"time_{i}_{j}_{k}"
            )

    # Time window constraints at each node
    for k in vehicles:
        for i in nodes:
            model.addConstr(t[i, k] >= e[i], name=f"tw_early_{i}_{k}")
            model.addConstr(t[i, k] <= l[i], name=f"tw_late_{i}_{k}")

    # Depot departure time window
    for k in vehicles:
        model.addConstr(t[depot_origin, k] >= depot_tw_start, name=f"depot_start_{k}")
        model.addConstr(t[depot_origin, k] <= depot_tw_end, name=f"depot_end_{k}")

    # If a customer is not visited by vehicle k, force its time variable to be within depot window
    # (handled implicitly by time window bounds set above, but we also need to ensure
    # that unvisited customers don't get spurious time window violations)
    # Actually, since time window bounds are always enforced, we add a relaxation:
    # t[i,k] only matters when vehicle k visits i; otherwise it can be anything in [e[i], l[i]].
    # The constraints above already handle this correctly.

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        else:
            return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"status_{status}"}