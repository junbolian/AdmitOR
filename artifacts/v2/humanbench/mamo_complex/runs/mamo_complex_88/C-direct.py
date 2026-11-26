import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    polygon_vertices = params["polygon_vertices"]
    area_scale_factor = params["area_scale_factor"]

    # Build the list of edges from polygon vertices
    n = len(polygon_vertices)
    
    # For each edge of the polygon, we derive the half-plane constraint:
    # The circle center (cx, cy) with radius r must satisfy:
    #   a*cx + b*cy + c >= r
    # where a*x + b*y + c >= 0 is the inward-facing half-plane for edge i->j
    # (assuming vertices are listed in counter-clockwise order)
    
    # We need to ensure the polygon is CCW; compute signed area
    signed_area = 0.0
    for i in range(n):
        x1, y1 = polygon_vertices[i]
        x2, y2 = polygon_vertices[(i + 1) % n]
        signed_area += (x1 * y2 - x2 * y1)
    signed_area /= 2.0
    
    # If CW, reverse the order
    if signed_area < 0:
        polygon_vertices = list(reversed(polygon_vertices))
    
    # For each edge from vertex i to vertex i+1 (CCW), the inward normal constraint:
    # edge vector: (dx, dy) = (x2-x1, y2-y1)
    # inward normal (CCW polygon): (-dy, dx) normalized
    # constraint: (-dy)*(cx - x1) + dx*(cy - y1) >= r * norm
    # i.e., (-dy)*cx + dx*cy + (dy*x1 - dx*y1) >= r * sqrt(dy^2 + dx^2)
    # normalized: (-dy/L)*cx + (dx/L)*cy + (dy*x1 - dx*y1)/L >= r
    
    edges = []
    for i in range(n):
        x1, y1 = polygon_vertices[i]
        x2, y2 = polygon_vertices[(i + 1) % n]
        dx = x2 - x1
        dy = y2 - y1
        L = math.sqrt(dx * dx + dy * dy)
        # inward normal components (normalized)
        a = -dy / L
        b = dx / L
        c = (dy * x1 - dx * y1) / L
        edges.append((a, b, c))
    
    # Build Gurobi model
    model = gp.Model("largest_inscribed_circle")
    model.setParam("OutputFlag", 0)
    
    # Variables: center coordinates and radius
    cx = model.addVar(lb=-GRB.INFINITY, name="cx")
    cy = model.addVar(lb=-GRB.INFINITY, name="cy")
    r = model.addVar(lb=0.0, name="r")
    
    # Constraints: for each edge, distance from center to edge >= r
    for idx, (a, b, c) in enumerate(edges):
        model.addConstr(a * cx + b * cy + c >= r, name=f"edge_{idx}")
    
    # Objective: maximize radius (area = pi * r^2, maximizing r maximizes area)
    model.setObjective(r, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        r_val = r.X
        area = math.pi * r_val * r_val * area_scale_factor
        return {"objective": area, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}