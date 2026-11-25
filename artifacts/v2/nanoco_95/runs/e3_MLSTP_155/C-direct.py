import gurobipy as gp
from gurobipy import GRB

def solve(params):
    D = params["distance_matrix"]
    n = 15

    raw_edges = [(4,6),(12,13),(3,10),(5,10),(2,5),(1,3),(0,14),(0,11),
                 (10,12),(11,14),(1,12),(6,11),(6,8),(6,14),(4,5),(3,9),
                 (4,8),(3,12),(9,10),(2,4),(2,7),(1,5),(2,13),(4,7),
                 (4,10),(0,6),(1,13),(1,10),(6,9),(7,8)]

    E = []
    for (a, b) in raw_edges:
        E.append((a, b) if a < b else (b, a))
    E = list(dict.fromkeys(E))
    num_edges = len(E)

    model = gp.Model("sensor_tree")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_edges, vtype=GRB.BINARY, name="x")
    f = model.addVars(num_edges, vtype=GRB.CONTINUOUS, lb=-(n - 1), ub=(n - 1), name="f")
    y = model.addVars(n, vtype=GRB.BINARY, name="y")

    # Spanning tree: exactly n-1 edges
    model.addConstr(gp.quicksum(x[k] for k in range(num_edges)) == n - 1)

    # Single-commodity flow to enforce connectivity.
    # f[k] is signed flow on edge E[k]=(i,j): positive => i -> j.
    root = 0
    for v in range(n):
        out_terms = gp.quicksum(f[k] for k in range(num_edges) if E[k][0] == v)
        in_terms = gp.quicksum(f[k] for k in range(num_edges) if E[k][1] == v)
        if v == root:
            model.addConstr(out_terms - in_terms == n - 1)
        else:
            model.addConstr(out_terms - in_terms == -1)

    # Flow can only use selected edges
    for k in range(num_edges):
        model.addConstr(f[k] <= (n - 1) * x[k])
        model.addConstr(f[k] >= -(n - 1) * x[k])

    # Degree / peripheral indicator
    # y[v] = 1  =>  deg[v] = 1; maximize sum y
    for v in range(n):
        deg = gp.quicksum(x[k] for k in range(num_edges) if E[k][0] == v or E[k][1] == v)
        model.addConstr(y[v] <= deg)
        model.addConstr(deg - 1 <= (n - 1) * (1 - y[v]))

    model.setObjective(gp.quicksum(y[v] for v in range(n)), GRB.MAXIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no_solution"}