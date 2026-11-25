import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Parse distance matrix from params
    n = 8  # nodes 0..7
    dist = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                dist[i, j] = 0
            elif i < j:
                dist[i, j] = params[f"dist_{i}_to_{j}"]
                dist[j, i] = params[f"dist_{i}_to_{j}"]

    # Time windows
    tw_lower = {i: params[f"tw{i}_lower"] for i in range(n)}
    tw_upper = {i: params[f"tw{i}_upper"] for i in range(n)}

    max_shelf_life = params["max_shelf_life"]
    service_time = params["service_time"]

    # Big-M for time propagation constraints
    M = max_shelf_life + max(dist[i, j] for i in range(n) for j in range(n)) + service_time

    model = gp.Model("vrptw_single_route")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if truck travels directly from i to j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # t[i] = arrival time at node i
    t = model.addVars(n, lb=0.0, ub=M, vtype=GRB.CONTINUOUS, name="t")

    # No self-loops
    for i in range(n):
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in range(n) for j in range(n)),
        GRB.MINIMIZE
    )

    # Each store (1..7) must be visited exactly once: exactly one incoming arc
    for j in range(1, n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n)) == 1,
            name=f"visit_in_{j}"
        )

    # Each store (1..7) must be departed exactly once: exactly one outgoing arc
    for i in range(1, n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n)) == 1,
            name=f"visit_out_{i}"
        )

    # Warehouse: exactly one departure and exactly one return
    model.addConstr(
        gp.quicksum(x[0, j] for j in range(1, n)) == 1,
        name="depot_out"
    )
    model.addConstr(
        gp.quicksum(x[i, 0] for i in range(1, n)) == 1,
        name="depot_in"
    )

    # Time window constraints at all nodes
    for i in range(n):
        model.addConstr(t[i] >= tw_lower[i], name=f"tw_lo_{i}")
        model.addConstr(t[i] <= tw_upper[i], name=f"tw_hi_{i}")

    # Departure from warehouse
    model.addConstr(t[0] == tw_lower[0], name="depot_start")

    # Time propagation: if x[i,j]=1 then t[j] >= t[i] + service_time + dist[i,j]
    for i in range(n):
        for j in range(1, n):  # j != 0 (can't propagate back to depot via this)
            if i != j:
                model.addConstr(
                    t[j] >= t[i] + service_time + dist[i, j] - M * (1 - x[i, j]),
                    name=f"time_prop_{i}_{j}"
                )

    # Return to depot time feasibility
    for i in range(1, n):
        model.addConstr(
            t[0] + max_shelf_life >= t[i] + service_time + dist[i, 0] - M * (1 - x[i, 0]),
            name=f"return_time_{i}"
        )

    # Subtour elimination via MTZ formulation
    # u[i] = position of node i in the tour (for nodes 1..7)
    u = model.addVars(range(1, n), lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}