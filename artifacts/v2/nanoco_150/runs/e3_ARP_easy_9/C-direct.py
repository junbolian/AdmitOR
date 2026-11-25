import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    n = 8
    dist = {}
    for i in range(n):
        for j in range(i + 1, n):
            dist[(i, j)] = params[f"dist_{i}_{j}"]

    required_edges = [(0, 1), (0, 3), (0, 6), (1, 5), (1, 6), (2, 3), (2, 4), (5, 7)]
    all_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    nodes = list(range(n))

    model = gp.Model("rural_postman")
    model.Params.OutputFlag = 0

    x = {}
    for (i, j) in all_edges:
        x[(i, j)] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    y = {}
    for v in nodes:
        y[v] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"y_{v}")

    model.update()

    model.setObjective(
        gp.quicksum(dist[(i, j)] * x[(i, j)] for (i, j) in all_edges),
        GRB.MINIMIZE
    )

    for (i, j) in required_edges:
        model.addConstr(x[(i, j)] >= 1, name=f"req_{i}_{j}")

    for v in nodes:
        incident = [x[(i, j)] for (i, j) in all_edges if i == v or j == v]
        model.addConstr(gp.quicksum(incident) == 2 * y[v], name=f"even_deg_{v}")

    for size in range(1, n):
        for S_tuple in combinations(nodes, size):
            S = set(S_tuple)
            cut_edges = [x[(i, j)] for (i, j) in all_edges if (i in S) != (j in S)]
            if cut_edges:
                model.addConstr(
                    gp.quicksum(cut_edges) >= 2,
                    name=f"subtour_{'_'.join(str(v) for v in sorted(S))}"
                )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}