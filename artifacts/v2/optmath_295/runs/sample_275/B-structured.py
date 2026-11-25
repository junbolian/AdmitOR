# IR: {"sets":{"F":"1..num_facilities (frozen at 21)","A":"1..num_service_areas (frozen at 36)","C[a]":"fixed coverage_data[a] below"},"params":{"facility_cost":"params['facility_cost']; sequence in facility order or mapping keyed by facility number","num_facilities":"params['num_facilities']","num_service_areas":"params['num_service_areas']","coverage_requirement":"params['coverage_requirement']"},"variables":{"x[f]":"Binary for f in F"},"constraints":["For every a in A: sum(x[f] for f in C[a]) >= coverage_requirement"],"objective":"Minimize sum(facility_cost[f] * x[f] for f in F)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    num_service_areas = params["num_service_areas"]
    facility_cost = params["facility_cost"]
    coverage_requirement = params["coverage_requirement"]

    # The coverage graph is fixed to the stated problem dimensions.
    if num_facilities != 21 or num_service_areas != 36:
        return {"objective": None, "status": "invalid_dimensions"}

    coverage_data = {
        1: (1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 18, 21),
        2: (1, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 19, 20),
        3: (4, 5, 6, 7, 8, 10, 18, 20, 21),
        4: (4, 5, 6, 9, 10, 11, 13, 14, 16, 17, 18, 19, 20, 21),
        5: (1, 2, 4, 9, 10, 11, 12, 13, 14, 15, 20),
        6: (1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 14, 15, 16, 18, 19, 21),
        7: (4, 5, 9, 10, 12, 14, 16, 17, 18, 20, 21),
        8: (2, 3, 4, 5, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20),
        9: (1, 2, 6, 11, 13, 14, 18, 20, 21),
        10: (1, 3, 5, 8, 11, 13, 14, 16, 17, 21),
        11: (1, 2, 3, 7, 8, 9, 10, 12, 15, 16, 17, 18, 19),
        12: (1, 2, 3, 4, 5, 13, 14, 15, 16, 17, 19, 21),
        13: (4, 5, 6, 7, 8, 12, 14, 15, 17, 18, 19, 21),
        14: (1, 2, 4, 5, 7, 9, 10, 11, 16, 17, 20, 21),
        15: (1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 16, 17, 21),
        16: (3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21),
        17: (4, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21),
        18: (3, 4, 5, 7, 8, 9, 13, 15, 18, 19, 20),
        19: (2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20),
        20: (3, 6, 7, 8, 9, 10, 11, 12, 15, 16, 19, 21),
        21: (1, 2, 3, 4, 6, 7, 9, 11, 14, 17, 19),
        22: (1, 2, 4, 5, 6, 8, 10, 11, 14, 17, 18, 19, 20),
        23: (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 21),
        24: (1, 2, 3, 4, 5, 8, 10, 11, 13, 14, 15, 16, 18, 20, 21),
        25: (2, 3, 8, 9, 10, 11, 13, 14, 15, 17, 18, 20),
        26: (1, 2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 18, 20, 21),
        27: (7, 8, 10, 12, 13, 14, 15, 16, 17, 18, 20),
        28: (4, 7, 8, 10, 11, 13, 14, 16, 17, 20, 21),
        29: (1, 4, 5, 6, 7, 10, 11, 12, 13, 15, 16, 18, 19, 21),
        30: (3, 6, 9, 11, 12, 15, 16, 21),
        31: (1, 3, 4, 10, 13, 14, 15, 18, 19, 21),
        32: (1, 2, 4, 10, 11, 13, 15, 16, 18, 20),
        33: (2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 17, 18, 19, 20, 21),
        34: (1, 4, 11, 12, 13, 14, 15, 16, 18, 20, 21),
        35: (2, 3, 5, 7, 9, 11, 13, 15, 16, 17, 18, 19, 20),
        36: (1, 3, 4, 5, 6, 7, 8, 9, 11, 13, 15, 16, 17, 19, 20, 21),
    }

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(1, num_facilities)
    model.service_areas = pyo.RangeSet(1, num_service_areas)

    # Accept a zero-based sequence or a mapping with integer/string labels.
    if isinstance(facility_cost, Mapping):
        costs = {
            facility: (
                facility_cost[facility]
                if facility in facility_cost
                else facility_cost[str(facility)]
            )
            for facility in model.facilities
        }
    else:
        costs = {
            facility: facility_cost[facility - 1]
            for facility in model.facilities
        }

    model.activation_cost = pyo.Param(
        model.facilities,
        initialize=costs,
        within=pyo.Reals,
    )
    model.required_coverage = pyo.Param(
        initialize=coverage_requirement,
        within=pyo.Reals,
    )
    model.covering_facilities = pyo.Set(
        model.service_areas,
        within=model.facilities,
        initialize=coverage_data,
    )
    model.x = pyo.Var(model.facilities, domain=pyo.Binary)

    def coverage_rule(problem, area):
        return (
            pyo.quicksum(
                problem.x[facility]
                for facility in problem.covering_facilities[area]
            )
            >= problem.required_coverage
        )

    model.coverage_constraints = pyo.Constraint(
        model.service_areas,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.activation_cost[facility] * model.x[facility]
            for facility in model.facilities
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}