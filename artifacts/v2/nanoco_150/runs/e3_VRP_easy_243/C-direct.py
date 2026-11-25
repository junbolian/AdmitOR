import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    coordinates = params["coordinates"]
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    num_nodes = params["num_nodes"]
    num_collection_points = params["num_collection_points"]

    # Node sets
    depot = 0
    customers = list(range(1, num_collection_points + 1))
    all_nodes = list(range(num_nodes))

    # Build distance lookup
    d = {(i, j): distance_matrix[i][j] for i in all_nodes for j in all_nodes}

    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)

    # x[k,i,j] = 1 if vehicle k travels from node i to node j
    x = model.addVars(
        num_vehicles, all_nodes, all_nodes,
        vtype=GRB.BINARY,
        name="x"
    )

    # u[k,i] = position of node i in vehicle k's route (MTZ subtour elimination)
    u = model.addVars(
        num_vehicles, customers,
        vtype=GRB.CONTINUOUS,
        lb=1.0,
        ub=float(num_collection_points),
        name="u"
    )

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(d[i, j] * x[k, i, j]
                    for k in range(num_vehicles)
                    for i in all_nodes
                    for j in all_nodes),
        GRB.MINIMIZE
    )

    # No self-loops
    for k in range(num_vehicles):
        for i in all_nodes:
            model.addConstr(x[k, i, i] == 0, name=f"no_self_{k}_{i}")

    # Each customer visited exactly once across all vehicles
    for j in customers:
        model.addConstr(
            gp.quicksum(x[k, i, j] for k in range(num_vehicles) for i in all_nodes if i != j) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation: for each vehicle and each customer,
    # number of times entering equals number of times leaving
    for k in range(num_vehicles):
        for i in customers:
            model.addConstr(
                gp.quicksum(x[k, i, j] for j in all_nodes if j != i) ==
                gp.quicksum(x[k, j, i] for j in all_nodes if j != i),
                name=f"flow_{k}_{i}"
            )

    # Each vehicle departs depot at most once
    for k in range(num_vehicles):
        model.addConstr(
            gp.quicksum(x[k, depot, j] for j in customers) <= 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to depot at most once
    for k in range(num_vehicles):
        model.addConstr(
            gp.quicksum(x[k, i, depot] for i in customers) <= 1,
            name=f"return_{k}"
        )

    # If vehicle k visits customer j, it must have departed from depot
    for k in range(num_vehicles):
        for j in customers:
            model.addConstr(
                gp.quicksum(x[k, i, j] for i in all_nodes if i != j) <=
                gp.quicksum(x[k, depot, c] for c in customers),
                name=f"active_{k}_{j}"
            )

    # MTZ subtour elimination constraints
    big_M = num_collection_points
    for k in range(num_vehicles):
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[k, i] - u[k, j] + big_M * x[k, i, j] <= big_M - 1,
                        name=f"mtz_{k}_{i}_{j}"
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