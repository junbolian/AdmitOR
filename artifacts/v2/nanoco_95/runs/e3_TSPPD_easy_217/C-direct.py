import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    pickup_delivery_pairs = params["pickup_delivery_pairs"]
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]

    nodes = list(range(num_nodes))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if vehicle travels from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # u[i] = position of node i in the tour (MTZ subtour elimination), 1-indexed among non-depot nodes
    # We'll use u over all nodes 1..n-1 for MTZ
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
    )

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Each node has exactly one incoming arc
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes) == 1, name=f"in_{j}")

    # Each node has exactly one outgoing arc
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes) == 1, name=f"out_{i}")

    # MTZ subtour elimination
    # u[0] = 0 (depot fixed at position 0)
    model.addConstr(u[0] == 0, name="u_depot")

    for i in nodes:
        if i != 0:
            model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
            model.addConstr(u[i] <= num_nodes - 1, name=f"u_ub_{i}")

    M = num_nodes  # big-M for MTZ
    for i in nodes:
        for j in nodes:
            if i != 0 and j != 0 and i != j:
                model.addConstr(
                    u[j] >= u[i] + 1 - M * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}"
                )

    # Pickup before delivery precedence constraints
    for k in range(num_pairs):
        pickup = pickup_delivery_pairs[k][0]
        delivery = pickup_delivery_pairs[k][1]
        # u[pickup] < u[delivery], i.e. pickup visited before delivery
        model.addConstr(u[pickup] + 1 <= u[delivery], name=f"prec_{k}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}