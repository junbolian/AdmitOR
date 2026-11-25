import gurobipy as gp
from gurobipy import GRB


def solve(params):
    distance_matrix = params["distance_matrix"]
    coords = params["coords"]
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]
    pickup_delivery_pairs = params["pickup_delivery_pairs"]

    n = num_nodes
    depot = 0
    customers = list(range(1, n))  # branch nodes 1..n-1
    N = n - 1  # number of non-depot nodes (for MTZ constant)

    model = gp.Model("pdtsp")
    model.Params.OutputFlag = 0

    # x[i,j] = 1 if the van travels directly from node i to node j
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of branch node i within the tour (MTZ ordering variable)
    u = {}
    for i in customers:
        u[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=1, ub=N, name=f"u_{i}")

    model.setObjective(
        gp.quicksum(
            distance_matrix[i][j] * x[i, j]
            for i in range(n)
            for j in range(n)
            if i != j
        ),
        GRB.MINIMIZE,
    )

    # Each branch node has exactly one incoming and one outgoing arc
    for i in customers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if j != i) == 1, name=f"out_{i}"
        )
        model.addConstr(
            gp.quicksum(x[j, i] for j in range(n) if j != i) == 1, name=f"in_{i}"
        )

    # Depot: one outgoing arc to start the tour, one incoming arc to end it
    model.addConstr(
        gp.quicksum(x[depot, j] for j in range(n) if j != depot) == 1, name="depot_out"
    )
    model.addConstr(
        gp.quicksum(x[j, depot] for j in range(n) if j != depot) == 1, name="depot_in"
    )

    # MTZ subtour-elimination constraints (over branch nodes only)
    for i in customers:
        for j in customers:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + N * x[i, j] <= N - 1, name=f"mtz_{i}_{j}"
                )

    # Pickup-before-delivery precedence for each request pair
    for pair in pickup_delivery_pairs:
        p_node = pair[0]
        d_node = pair[1]
        model.addConstr(u[p_node] <= u[d_node] - 1, name=f"prec_{p_node}_{d_node}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}