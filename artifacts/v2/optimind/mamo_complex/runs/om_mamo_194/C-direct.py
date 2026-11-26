import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    vertices = params["field_vertices"]
    n = len(vertices)

    # Build edge constraints for Chebyshev center LP
    # For each edge of the polygon, the distance from center (cx, cy) to the edge >= r
    # Edge from v[i] to v[i+1]: ax + by <= c, with (a,b) unit normal pointing inward
    # We need to determine the inward-pointing normal for each edge.

    # Compute polygon area sign to determine orientation (CCW or CW)
    area_sign = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        area_sign += (x1 * y2 - x2 * y1)
    # area_sign > 0 => CCW, < 0 => CW

    edges = []
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        # Edge vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        # Outward normal for CCW polygon: (dy, -dx) / length
        # Inward normal: (-dy, dx) / length
        if area_sign > 0:
            # CCW: inward normal is (-dy, dx) / length
            nx = -dy / length
            ny = dx / length
        else:
            # CW: inward normal is (dy, -dx) / length
            nx = dy / length
            ny = -dx / length
        # The constraint: nx*(cx - x1) + ny*(cy - y1) >= r
        # i.e., nx*cx + ny*cy - r >= nx*x1 + ny*y1
        rhs = nx * x1 + ny * y1
        edges.append((nx, ny, rhs))

    try:
        model = gp.Model()
        model.setParam("OutputFlag", 0)

        cx = model.addVar(lb=-GRB.INFINITY, name="cx")
        cy = model.addVar(lb=-GRB.INFINITY, name="cy")
        r = model.addVar(lb=0.0, name="r")

        for idx, (nx, ny, rhs) in enumerate(edges):
            model.addConstr(nx * cx + ny * cy - r >= rhs, name=f"edge_{idx}")

        model.setObjective(r, GRB.MAXIMIZE)
        model.optimize()

        if model.Status == GRB.OPTIMAL:
            radius = r.X
            area = math.pi * radius * radius
            return {"objective": float(area), "status": "optimal"}
        elif model.Status == GRB.INFEASIBLE:
            return {"objective": None, "status": "infeasible"}
        else:
            return {"objective": None, "status": f"gurobi_status_{model.Status}"}

    except gp.GurobiError as e:
        return {"objective": None, "status": f"gurobi_error: {str(e)}"}