import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define the graph structure
    vertices = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    
    # Edges from the problem description
    # Outer pentagon: a-b, b-c, c-d, d-e, e-a
    # Spokes: a-f, b-g, c-h, d-i, e-j
    # Inner K5 (f,g,h,i,j fully connected)
    edges = [
        ('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e'), ('e', 'a'),
        ('a', 'f'), ('b', 'g'), ('c', 'h'), ('d', 'i'), ('e', 'j'),
        ('f', 'g'), ('f', 'h'), ('f', 'i'), ('f', 'j'),
        ('g', 'h'), ('g', 'i'), ('g', 'j'),
        ('h', 'i'), ('h', 'j'),
        ('i', 'j')
    ]
    
    model = gp.Model("vertex_cover")
    model.setParam("OutputFlag", 0)
    
    # Binary variable for each vertex: 1 if in cover, 0 otherwise
    x = model.addVars(vertices, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize number of vertices in cover
    model.setObjective(gp.quicksum(x[v] for v in vertices), GRB.MINIMIZE)
    
    # Constraint: for each edge, at least one endpoint must be in cover
    for u, v in edges:
        model.addConstr(x[u] + x[v] >= 1, name=f"edge_{u}_{v}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}