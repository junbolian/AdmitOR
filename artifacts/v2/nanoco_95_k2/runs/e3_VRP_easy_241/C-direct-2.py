import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    dist = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]

    n_customers = 8  # nodes 1..8
    all_nodes = list(range(9))  # 0..8
    customers = list(range(1, 9))  # 1..8

    model = gp.Model()
    model.Params.OutputFlag = 0

    # x[k,i,j] = 1 if vehicle k travels from i to j
    x = {}
    for k in range(num_vehicles):
        for i in all_nodes:
            for j in all_nodes:
                if i != j:
                    x[k, i, j] = model.addVar(vtype=GRB.BINARY,
                                               name=f"x_{k}_{i}_{j}")

    # u[k,i] = position of node i in route of vehicle k (MTZ subtour elimination)
    u = {}
    for k in range(num_vehicles):
        for i in customers:
            u[k, i] = model.addVar(lb=1, ub=n_customers, vtype=GRB.CONTINUOUS,
                                   name=f"u_{k}_{i}")

    # y[k,i] = 1 if vehicle k visits customer i
    y = {}
    for k in range(num_vehicles):
        for i in customers:
            y[k, i] = model.addVar(vtype=GRB.BINARY, name=f"y_{k}_{i}")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[k, i, j]
                    for k in range(num_vehicles)
                    for i in all_nodes
                    for j in all_nodes
                    if i != j),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for i in customers:
        model.addConstr(
            gp.quicksum(y[k, i] for k in range(num_vehicles)) == 1,
            name=f"visit_{i}"
        )

    # Flow conservation at each customer node
    for k in range(num_vehicles):
        for i in customers:
            # inflow equals y[k,i]
            model.addConstr(
                gp.quicksum(x[k, j, i] for j in all_nodes if j != i) == y[k, i],
                name=f"inflow_{k}_{i}"
            )
            # outflow equals y[k,i]
            model.addConstr(
                gp.quicksum(x[k, i, j] for j in all_nodes if j != i) == y[k, i],
                name=f"outflow_{k}_{i}"
            )

    # Flow conservation at depot: each vehicle departs and returns exactly once
    for k in range(num_vehicles):
        model.addConstr(
            gp.quicksum(x[k, 0, j] for j in customers) == 1,
            name=f"depot_out_{k}"
        )
        model.addConstr(
            gp.quicksum(x[k, i, 0] for i in customers) == 1,
            name=f"depot_in_{k}"
        )

    # MTZ subtour elimination constraints
    for k in range(num_vehicles):
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[k, i] - u[k, j] + n_customers * x[k, i, j] <= n_customers - 1,
                        name=f"mtz_{k}_{i}_{j}"
                    )

    # Link x and y: if vehicle k visits customer i, its arc must be used
    # (already enforced via flow conservation, but guard against depot-depot)
    # No direct arc from depot to depot
    for k in range(num_vehicles):
        x[k, 0, 0] = None  # not in dict (never added)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}