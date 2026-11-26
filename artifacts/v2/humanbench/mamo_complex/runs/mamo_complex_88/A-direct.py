import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = params["polygon_vertices"]
    scale = params["area_scale_factor"]

    model = pyo.ConcreteModel()

    n = len(vertices)

    # Signed area to determine polygon orientation (CCW if positive).
    signed_area = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        signed_area += x1 * y2 - x2 * y1
    orient = 1.0 if signed_area >= 0 else -1.0

    model.cx = pyo.Var()
    model.cy = pyo.Var()
    model.r = pyo.Var(bounds=(0, None))

    model.edges = pyo.ConstraintList()
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        dx = x2 - x1
        dy = y2 - y1
        edge_len = (dx * dx + dy * dy) ** 0.5
        # Inward signed distance (orient handles orientation):
        #   orient * (dx*(py - y1) - dy*(px - x1)) / edge_len >= r
        model.edges.add(
            orient * (dx * (model.cy - y1) - dy * (model.cx - x1))
            >= model.r * edge_len
        )

    model.obj = pyo.Objective(expr=model.r, sense=pyo.maximize)

    Highs().solve(model)

    r_val = pyo.value(model.r)
    area = 3.141592653589793 * r_val * r_val * scale
    obj_val = float(area)
    return {"objective": obj_val, "status": "optimal"}