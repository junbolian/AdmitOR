import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = params["num_nodes"]  # 10
    dist = params["distance_matrix"]

    nodes = list(range(n))
    # All directed arcs excluding self-loops
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("tsp_waste")
    model.setParam("OutputFlag", 0)

    # Binary arc selection variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i, j in arcs),
        GRB.MINIMIZE
    )

    # Each node has exactly one outgoing arc
    model.addConstrs(
        (gp.quicksum(x[i, j] for j in nodes if j != i) == 1 for i in nodes),
        name="out"
    )

    # Each node has exactly one incoming arc
    model.addConstrs(
        (gp.quicksum(x[i, j] for i in nodes if i != j) == 1 for j in nodes),
        name="in"
    )

    # MTZ subtour elimination
    # u[i] is the position of node i in the tour (only for non-depot nodes)
    non_depot = list(range(1, n))
    u = model.addVars(non_depot, lb=1.0, ub=float(n - 1), vtype=GRB.CONTINUOUS, name="u")

    model.addConstrs(
        (u[i] - u[j] + (n - 1) * x[i, j] <= n - 2
         for i in non_depot for j in non_depot if i != j),
        name="mtz"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}