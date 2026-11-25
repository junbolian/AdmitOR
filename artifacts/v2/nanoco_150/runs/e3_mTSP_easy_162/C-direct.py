import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_vehicles = params["num_vehicles"]
    num_customers = params["num_customers"]
    depot_x = params["depot_x"]
    depot_y = params["depot_y"]
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]
    dist = params["distance_matrix"]

    n_nodes = 1 + num_customers  # 0..8
    nodes = list(range(n_nodes))
    customers = list(range(1, n_nodes))
    vehicles = list(range(num_vehicles))

    model = gp.Model("VRP")
    model.setParam("OutputFlag", 0)

    # x[i,j,k] = 1 if vehicle k travels from node i to node j
    x = {}
    for k in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    x[i, j, k] = model.addVar(vtype=GRB.BINARY,
                                               name=f"x_{i}_{j}_{k}")

    # Subtour elimination via MTZ u[i,k] for customers
    u = {}
    for k in vehicles:
        for i in customers:
            u[i, k] = model.addVar(lb=1, ub=num_customers,
                                   vtype=GRB.CONTINUOUS,
                                   name=f"u_{i}_{k}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j, k]
                    for k in vehicles
                    for i in nodes
                    for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each customer visited exactly once across all vehicles
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k]
                        for k in vehicles
                        for i in nodes if i != j) == 1,
            name=f"visit_{j}"
        )

    # Flow conservation for each vehicle at each node
    for k in vehicles:
        for node in nodes:
            model.addConstr(
                gp.quicksum(x[node, j, k] for j in nodes if j != node) ==
                gp.quicksum(x[i, node, k] for i in nodes if i != node),
                name=f"flow_{node}_{k}"
            )

    # Each vehicle departs from depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in customers) == 1,
            name=f"depart_{k}"
        )

    # Each vehicle returns to depot exactly once
    for k in vehicles:
        model.addConstr(
            gp.quicksum(x[i, 0, k] for i in customers) == 1,
            name=f"return_{k}"
        )

    # MTZ subtour elimination
    for k in vehicles:
        for i in customers:
            for j in customers:
                if i != j:
                    model.addConstr(
                        u[i, k] - u[j, k] + num_customers * x[i, j, k]
                        <= num_customers - 1,
                        name=f"mtz_{i}_{j}_{k}"
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