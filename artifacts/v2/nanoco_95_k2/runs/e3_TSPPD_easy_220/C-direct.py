import gurobipy as gp
from gurobipy import GRB


def solve(params):
    D = params["distance_matrix"]
    n = params["num_nodes"]
    num_pairs = params["num_pairs"]
    pairs = params["pickup_delivery_pairs"]

    model = gp.Model("pd_tsp")
    model.Params.OutputFlag = 0

    # x[i, j] = 1 if arc i->j is used in the tour
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # MTZ position variables for nodes 1..n-1 (depot 0 is implicitly position 0)
    u = {}
    for i in range(1, n):
        u[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=1.0, ub=float(n - 1), name=f"u_{i}")

    model.update()

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(D[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE,
    )

    # Degree constraints: each node is entered and left exactly once
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if j != i) == 1, name=f"out_{i}"
        )
        model.addConstr(
            gp.quicksum(x[j, i] for j in range(n) if j != i) == 1, name=f"in_{i}"
        )

    # MTZ subtour elimination among non-depot nodes
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2, name=f"mtz_{i}_{j}"
                )

    # Precedence: pickup must be visited before delivery for each pair
    for k in range(num_pairs):
        pu = pairs[k][0]
        dv = pairs[k][1]
        if pu == 0:
            # Pickup at depot (always first) -> precedence automatically satisfied
            continue
        if dv == 0:
            # Delivery at depot (always last) -> cannot satisfy pickup-before-delivery
            return {"objective": None, "status": "infeasible_precedence"}
        model.addConstr(u[pu] + 1.0 <= u[dv], name=f"prec_{k}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}