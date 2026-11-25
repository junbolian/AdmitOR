# IR: {"sets":{"zones":"0..28","candidates":"0..9"},"params":{"establishment_costs":"length-10 cost array from params","coverage_radius":"scalar from params","distance_matrix":"29x10 distance array from params"},"variables":{"open_station[j]":"binary for each candidate j"},"constraints":["For each zone i: sum(open_station[j] for j with distance_matrix[i][j] <= coverage_radius) >= 1."],"objective":"Minimize sum(establishment_costs[j] * open_station[j] for all candidates j)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()
    model.zones = pyo.RangeSet(0, 28)
    model.candidates = pyo.RangeSet(0, 9)

    covering_candidates = {
        zone: [
            candidate
            for candidate in model.candidates
            if distance_matrix[zone][candidate] <= coverage_radius
        ]
        for zone in model.zones
    }

    model.open_station = pyo.Var(model.candidates, domain=pyo.Binary)

    def coverage_rule(instance, zone):
        # Tuple form also represents infeasibility when no station covers a zone.
        return (
            1,
            pyo.quicksum(
                instance.open_station[candidate]
                for candidate in covering_candidates[zone]
            ),
            None,
        )

    model.coverage_requirement = pyo.Constraint(
        model.zones, rule=coverage_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            establishment_costs[candidate] * model.open_station[candidate]
            for candidate in model.candidates
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