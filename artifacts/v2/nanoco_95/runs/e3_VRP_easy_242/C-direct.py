import gurobipy as gp
from gurobipy import GRB


def solve(params):
    coordinates = params["coordinates"]
    distance_matrix = params["distance_matrix"]
    num_vehicles = params["num_vehicles"]
    num_clinics = params["num_clinics"]

    # Nodes: 0 = warehouse, 1..num_clinics = clinics
    n_nodes = num_clinics + 1
    all_nodes = range(n_nodes)
    clinics = range(1, n_nodes)
    vehicles = range(num_vehicles)

    dist = {(i, j): distance_matrix[i][j] for i in all_nodes for j in all_nodes}

    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)

    # x[i, j, k] = 1 if vehicle k travels from node i to node j
    x = model.addVars(n_nodes, n_nodes, num_vehicles, vtype=GRB.BINARY, name="x")

    # Subtour elimination via MTZ formulation
    # u[i, k] = position of node i in the route of vehicle k (for i in clinics)
    u = model.addVars(n_nodes, num_vehicles, lb=0.0, ub=num_clinics, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j, k] for i in all_nodes for j in all_nodes for k in vehicles),
        GRB.MINIMIZE
    )

    # No self-loops
    for k in vehicles:
        for i in all_nodes:
            model.addConstr(x[i, i, k] == 0, name=f"no_self_{i}_{k}")

    # Each clinic visited exactly once across all vehicles
    for j in clinics:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in all_nodes for k in vehicles) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation at each clinic for each vehicle
    for k in vehicles:
        for node in clinics:
            model.addConstr(
                gp.quicksum(x[i, node, k] for i in all_nodes) ==
                gp.quicksum(x[node, j, k] for j in all_nodes),
                name=f"flow_{node}_{k}"
            )

    # Each vehicle departs warehouse exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in clinics) == 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to warehouse exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[i, 0, k] for i in clinics) == 1,
            name=f"return_{k}"
        )

    # MTZ subtour elimination constraints (applied per vehicle)
    for k in vehicles:
        for i in clinics:
            for j in clinics:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + num_clinics * x[i, j, k] <= num_clinics - 1,
                        name=f"mtz_{i}_{j}_{k}"
                    )

    # u bounds for clinic nodes
    for k in vehicles:
        for i in clinics:
            model.addConstr(u[i, k] >= 1, name=f"u_lb_{i}_{k}")
            model.addConstr(u[i, k] <= num_clinics, name=f"u_ub_{i}_{k}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}