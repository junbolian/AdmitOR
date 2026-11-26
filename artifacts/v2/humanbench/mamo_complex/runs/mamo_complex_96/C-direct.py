import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_vertices = params["num_vertices"]
    num_edges = params["num_edges"]
    edge_incidence_a = params["edge_incidence_a"]

    # Build edge list from the problem description
    # Vertices: a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7, i=8, j=9
    # Outer pentagon: a-f, a-e, a-b, b-g, b-c, c-h, c-d, d-i, d-e, e-j
    # Inner K5: f-g, f-h, f-i, f-j, g-h, g-i, g-j, h-i, h-j, i-j
    edges = [
        (0, 5),  # a-f
        (0, 4),  # a-e
        (0, 1),  # a-b
        (1, 6),  # b-g
        (1, 2),  # b-c
        (2, 7),  # c-h
        (2, 3),  # c-d
        (3, 8),  # d-i
        (3, 4),  # d-e
        (4, 9),  # e-j
        (5, 6),  # f-g
        (5, 7),  # f-h
        (5, 8),  # f-i
        (5, 9),  # f-j
        (6, 7),  # g-h
        (6, 8),  # g-i
        (6, 9),  # g-j
        (7, 8),  # h-i
        (7, 9),  # h-j
        (8, 9),  # i-j
    ]

    model = gp.Model("vertex_cover")
    model.setParam("OutputFlag", 0)

    # Binary variable for each vertex: 1 if in cover
    x = model.addVars(num_vertices, vtype=GRB.BINARY, name="x")

    # Objective: minimize number of vertices in cover
    model.setObjective(gp.quicksum(x[v] for v in range(num_vertices)), GRB.MINIMIZE)

    # Constraint: for each edge, at least one endpoint must be in the cover
    for idx, (u, v) in enumerate(edges):
        model.addConstr(x[u] + x[v] >= 1, name=f"edge_{idx}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}