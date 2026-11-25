import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distances_raw = params["distances"]

    nodes = list(range(5))
    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    # distances may be a list of 20 values in row-major order (i*5+j),
    # or a dict keyed by (i,j). Handle both.
    def get_dist(i, j):
        if isinstance(distances_raw, dict):
            return distances_raw[(i, j)]
        else:
            # list indexed row-major: index = i*5 + j
            return distances_raw[i * 5 + j]

    # Symmetric dispersion for unordered pair: sum both directions
    d = {}
    for (i, j) in pairs:
        d[(i, j)] = get_dist(i, j) + get_dist(j, i)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(d[(i, j)] * y[(i, j)] for (i, j) in pairs),
        GRB.MAXIMIZE
    )

    model.addConstr(gp.quicksum(x[i] for i in nodes) == 3, name="select_k")

    for (i, j) in pairs:
        model.addConstr(y[(i, j)] <= x[i], name=f"y_xi_{i}_{j}")
        model.addConstr(y[(i, j)] <= x[j], name=f"y_xj_{i}_{j}")
        model.addConstr(y[(i, j)] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}