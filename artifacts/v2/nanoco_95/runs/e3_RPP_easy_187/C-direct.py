import gurobipy as gp
from gurobipy import GRB
from itertools import combinations


def solve(params):
    D = params["distance_matrix"]
    n = params["num_nodes"]

    # Structural constants: mandatory service edges (required edge set, index structure)
    required_edges = [(0, 6), (0, 7), (1, 3), (2, 7), (4, 7), (4, 8), (5, 6), (5, 8)]

    model = gp.Model("rpp")
    model.Params.OutputFlag = 0

    # x[i, j] = number of directed traversals from i to j (service + deadhead combined)
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
    model.update()

    # Objective: minimize total travel cost (fuel + operational time)
    model.setObjective(gp.quicksum(D[i][j] * x[i, j] for (i, j) in x), GRB.MINIMIZE)

    # Each required edge must be serviced at least once (either direction)
    for (a, b) in required_edges:
        model.addConstr(x[a, b] + x[b, a] >= 1, name=f"req_{a}_{b}")

    # Flow conservation: arrivals == departures at every junction
    for k in range(n):
        model.addConstr(
            gp.quicksum(x[k, j] for j in range(n) if j != k) ==
            gp.quicksum(x[i, k] for i in range(n) if i != k),
            name=f"flow_{k}",
        )

    # Depot must have at least one departure (route starts at depot)
    model.addConstr(gp.quicksum(x[0, j] for j in range(1, n)) >= 1, name="depot_depart")

    # Connectivity cut constraints: every non-empty subset S of non-depot nodes
    # must have at least one arc leaving it. With flow conservation this also
    # forces an arc entering S, so S is connected to the depot's component.
    other_nodes = list(range(1, n))
    for r in range(1, n):
        for S in combinations(other_nodes, r):
            Sset = set(S)
            out_cut = gp.quicksum(x[i, j] for i in S for j in range(n) if j not in Sset)
            model.addConstr(out_cut >= 1, name=f"cut_{'_'.join(map(str, sorted(S)))}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}