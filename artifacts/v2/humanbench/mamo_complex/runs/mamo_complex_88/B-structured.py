# IR: {"sets":{"V":"ordered polygon vertices","E":"consecutive vertex pairs, cyclic"},"params":{"polygon_vertices":"params['polygon_vertices']","area_scale_factor":"params['area_scale_factor']","s":"sign of polygon signed area","dx_i,dy_i,L_i":"edge displacement and Euclidean length"},"variables":{"center_x":"real","center_y":"real","radius":"nonnegative real"},"constraints":["For each edge i: s*(dx_i*(center_y-y_i)-dy_i*(center_x-x_i)) >= L_i*radius."],"objective":"LP: maximize radius; report area_scale_factor*pi*optimal_radius^2 rounded to four significant digits."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = [
        (float(point[0]), float(point[1]))
        for point in params["polygon_vertices"]
    ]
    area_scale_factor = float(params["area_scale_factor"])

    if len(vertices) < 3:
        raise ValueError("The polygon must contain at least three vertices.")
    if not all(math.isfinite(value) for point in vertices for value in point):
        raise ValueError("Polygon coordinates must be finite.")
    if not math.isfinite(area_scale_factor):
        raise ValueError("area_scale_factor must be finite.")

    vertex_count = len(vertices)
    signed_double_area = sum(
        vertices[edge_index][0]
        * vertices[(edge_index + 1) % vertex_count][1]
        - vertices[(edge_index + 1) % vertex_count][0]
        * vertices[edge_index][1]
        for edge_index in range(vertex_count)
    )
    if signed_double_area == 0:
        raise ValueError("The polygon must have positive geometric area.")

    orientation = 1 if signed_double_area > 0 else -1
    edges = []

    for edge_index in range(vertex_count):
        start_x, start_y = vertices[edge_index]
        end_x, end_y = vertices[(edge_index + 1) % vertex_count]
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        edge_length = math.hypot(delta_x, delta_y)

        if edge_length == 0:
            raise ValueError("Consecutive polygon vertices must be distinct.")

        # This half-plane formulation requires a convex polygon.
        for vertex_x, vertex_y in vertices:
            inward_cross_product = orientation * (
                delta_x * (vertex_y - start_y)
                - delta_y * (vertex_x - start_x)
            )
            if inward_cross_product < 0:
                raise ValueError("The polygon must be convex and ordered.")

        edges.append((start_x, start_y, delta_x, delta_y, edge_length))

    model = pyo.ConcreteModel()
    model.edge_set = pyo.RangeSet(0, vertex_count - 1)
    model.center_x = pyo.Var(domain=pyo.Reals)
    model.center_y = pyo.Var(domain=pyo.Reals)
    model.radius = pyo.Var(domain=pyo.NonNegativeReals)

    def containment_rule(instance, edge_index):
        start_x, start_y, delta_x, delta_y, edge_length = edges[edge_index]
        return orientation * (
            delta_x * (instance.center_y - start_y)
            - delta_y * (instance.center_x - start_x)
        ) >= edge_length * instance.radius

    model.containment = pyo.Constraint(
        model.edge_set, rule=containment_rule
    )
    # Area increases with radius, so maximizing radius is an exact LP
    # formulation for the largest inscribed circle.
    model.objective = pyo.Objective(
        expr=model.radius, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(
        format(area_scale_factor * math.pi * obj_val**2, ".4g")
    )
    return {"objective": obj_val, "status": "optimal"}