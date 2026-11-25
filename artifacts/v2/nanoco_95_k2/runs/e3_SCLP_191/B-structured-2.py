# IR: {"sets":{"zones":"1..29","candidates":"1..10"},"params":{"establishment_costs":"params['establishment_costs'][j-1]","coverage_radius":"params['coverage_radius']","distance_matrix":"params['distance_matrix'][i-1][j-1]","covers[i,j]":"1 if distance_matrix[i,j] <= coverage_radius else 0"},"variables":{"open_station[j]":"Binary"},"constraints":["For each zone i: sum(covers[i,j] * open_station[j] for j in candidates) >= 1"],"objective":"Minimize sum(establishment_costs[j] * open_station[j] for j in candidates)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    if len(establishment_costs) != 10:
        raise ValueError("establishment_costs must contain 10 values.")
    if len(distance_matrix) != 29 or any(
        len(row) != 10 for row in distance_matrix
    ):
        raise ValueError("distance_matrix must have 29 rows and 10 columns.")

    model = pyo.ConcreteModel()
    model.zones = pyo.RangeSet(1, 29)
    model.candidates = pyo.RangeSet(1, 10)

    model.station_cost = pyo.Param(
        model.candidates,
        initialize=lambda _, j: establishment_costs[j - 1],
        within=pyo.Reals,
    )
    model.response_radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.travel_distance = pyo.Param(
        model.zones,
        model.candidates,
        initialize=lambda _, i, j: distance_matrix[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.covers = pyo.Param(
        model.zones,
        model.candidates,
        initialize=lambda _, i, j: int(
            pyo.value(model.travel_distance[i, j])
            <= pyo.value(model.response_radius)
        ),
        within=pyo.Binary,
    )

    model.open_station = pyo.Var(model.candidates, domain=pyo.Binary)

    def coverage_rule(_, i):
        return pyo.quicksum(
            model.covers[i, j] * model.open_station[j]
            for j in model.candidates
        ) >= 1

    model.zone_coverage = pyo.Constraint(
        model.zones,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.station_cost[j] * model.open_station[j]
            for j in model.candidates
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}