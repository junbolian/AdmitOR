# IR: {"sets":{"V":"vertex indices","E":"consecutive vertex pairs, cyclic"},"params":{"field_vertices":"ordered vertices of a convex polygon"},"derived":{"orientation":"sign of polygon signed area","edge_length[i]":"Euclidean length of edge i"},"variables":{"center_x":"Real","center_y":"Real","radius":"NonNegativeReal"},"constraints":["For each edge i=(u,v): orientation*((v.x-u.x)*(center_y-u.y)-(v.y-u.y)*(center_x-u.x)) >= edge_length[i]*radius"],"objective":"maximize radius (linear; equivalent to maximizing circular area)","report":"objective = pi*optimal_radius**2, rounded to four significant digits"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = [
        (float(point[0]), float(point[1]))
        for point in params["field_vertices"]
    ]

    # Accept either an open vertex sequence or one repeating its first vertex.
    if len(vertices) > 1 and vertices[0] == vertices[-1]:
        vertices = vertices[:-1]

    vertex_count = len(vertices)
    if vertex_count < 3:
        return {"objective": None, "status": "invalid_polygon"}

    if not all(
        math.isfinite(coordinate)
        for point in vertices
        for coordinate in point
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    signed_twice_area = sum(
        vertices[idx][0] * vertices[(idx + 1) % vertex_count][1]
        - vertices[(idx + 1) % vertex_count][0] * vertices[idx][1]
        for idx in range(vertex_count)
    )
    if signed_twice_area == 0:
        return {"objective": None, "status": "degenerate_polygon"}

    orientation = 1 if signed_twice_area > 0 else -1
    edge_data = []
    for idx in range(vertex_count):
        start_x, start_y = vertices[idx]
        end_x, end_y = vertices[(idx + 1) % vertex_count]
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        edge_length = math.hypot(delta_x, delta_y)
        if edge_length == 0:
            return {"objective": None, "status": "degenerate_edge"}
        edge_data.append(
            (start_x, start_y, delta_x, delta_y, edge_length)
        )

    model = pyo.ConcreteModel()
    model.edge_ids = pyo.RangeSet(0, vertex_count - 1)
    model.center_x = pyo.Var(domain=pyo.Reals)
    model.center_y = pyo.Var(domain=pyo.Reals)
    model.radius = pyo.Var(domain=pyo.NonNegativeReals)

    def containment_rule(problem, idx):
        start_x, start_y, delta_x, delta_y, edge_length = edge_data[idx]
        return (
            orientation
            * (
                delta_x * (problem.center_y - start_y)
                - delta_y * (problem.center_x - start_x)
            )
            >= edge_length * problem.radius
        )

    model.containment = pyo.Constraint(
        model.edge_ids, rule=containment_rule
    )
    model.radius_objective = pyo.Objective(
        expr=model.radius, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.radius_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # The LP maximizes radius; report the requested maximal area in m².
    obj_val = float(format(math.pi * obj_val**2, ".4g"))
    return {"objective": obj_val, "status": "optimal"}