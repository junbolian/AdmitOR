import pyomo.environ as pyo
import math
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    field_vertices = params["field_vertices"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(within=pyo.Reals)
    model.y = pyo.Var(within=pyo.Reals)
    model.r = pyo.Var(within=pyo.Reals, bounds=(0, None))

    n = len(field_vertices)
    model.constraints = pyo.ConstraintList()

    # Compute signed area to determine orientation
    area2 = 0.0
    for i in range(n):
        x1, y1 = field_vertices[i]
        x2, y2 = field_vertices[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1
    ccw = area2 > 0

    for i in range(n):
        x1, y1 = field_vertices[i]
        x2, y2 = field_vertices[(i + 1) % n]

        dx = x2 - x1
        dy = y2 - y1
        norm = math.sqrt(dx * dx + dy * dy)
        if ccw:
            nx = -dy / norm
            ny = dx / norm
        else:
            nx = dy / norm
            ny = -dx / norm

        model.constraints.add(
            nx * (model.x - x1) + ny * (model.y - y1) >= model.r
        )

    model.obj = pyo.Objective(expr=model.r, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    area = math.pi * obj_val * obj_val
    return {"objective": round(area, 4), "status": "optimal"}