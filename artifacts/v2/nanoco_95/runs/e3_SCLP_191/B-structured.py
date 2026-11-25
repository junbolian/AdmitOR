# IR: {"sets":{"I":"1..29","J":"1..10","N[i]":"{j in J: distance_matrix[i,j] <= coverage_radius}"},"params":{"establishment_costs":"length-10 array from params","coverage_radius":"scalar from params","distance_matrix":"29x10 array from params"},"variables":{"open_station[j]":"binary for j in J"},"constraints":["For each i in I: sum(open_station[j] for j in N[i]) >= 1"],"objective":"Minimize sum(establishment_costs[j] * open_station[j] for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the station covering problem using zero-based input arrays."""
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()
    model.zones = pyo.RangeSet(1, 29)
    model.candidates = pyo.RangeSet(1, 10)

    model.station_cost = pyo.Param(
        model.candidates,
        initialize=lambda mdl, j: establishment_costs[j - 1],
        within=pyo.Reals,
    )
    model.radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.travel_distance = pyo.Param(
        model.zones,
        model.candidates,
        initialize=lambda mdl, i, j: distance_matrix[i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )

    def covering_candidates_rule(mdl, i):
        return [
            j
            for j in mdl.candidates
            if pyo.value(mdl.travel_distance[i, j]) <= pyo.value(mdl.radius)
        ]

    model.covering_candidates = pyo.Set(
        model.zones,
        within=model.candidates,
        initialize=covering_candidates_rule,
    )
    model.open_station = pyo.Var(model.candidates, domain=pyo.Binary)

    def coverage_rule(mdl, i):
        # Tuple form also represents an infeasible row when this set is empty.
        return (
            1,
            pyo.quicksum(
                mdl.open_station[j] for j in mdl.covering_candidates[i]
            ),
            None,
        )

    model.coverage_requirement = pyo.Constraint(
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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}