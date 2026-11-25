import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distances = params["distances"]

    nodes = list(range(5))
    n = len(nodes)

    # distances is a flat list of length 20 (5*4 directed pairs, row-major, skipping i==i)
    # or length 25 (5x5 including diagonal). Determine access pattern by length.
    # 20 values: directed pairs (i,j) with i!=j, indexed as i*(n-1)+j if j<i else i*(n-1)+(j-1)
    # 25 values: full 5x5 matrix, index i*5+j
    # Use length to decide.

    def get_dist(i, j):
        if len(distances) == n * n:
            return distances[i * n + j]
        else:
            # 20 directed pairs, row i has (n-1) entries for j != i
            # position of j in row i: j if j < i else j-1
            col = j if j < i else j - 1
            return distances[i * (n - 1) + col]

    pairs = [(i, j) for i in nodes for j in nodes if i < j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    # For each unordered pair (i,j), dispersion = d(i,j) + d(j,i)
    model.setObjective(
        gp.quicksum(
            (get_dist(i, j) + get_dist(j, i)) * y[i, j]
            for (i, j) in pairs
        ),
        GRB.MAXIMIZE
    )

    model.addConstr(gp.quicksum(x[i] for i in nodes) == 3, name="select_3")

    for (i, j) in pairs:
        model.addConstr(y[i, j] <= x[i], name=f"y_xi_{i}_{j}")
        model.addConstr(y[i, j] <= x[j], name=f"y_xj_{i}_{j}")
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}