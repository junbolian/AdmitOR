# IR: {"sets":{"F":"1..21","A":"1..36","C[a]":"fixed facility coverage lists defined below"},"params":{"activation_cost[f]":"params['activation_cost'], indexed by facility"},"variables":{"x[f]":"binary"},"constraints":["For each a in A: sum(x[f] for f in C[a]) >= 1"],"objective":"minimize sum(activation_cost[f] * x[f] for f in F)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the facility set-cover problem.

    activation_cost may be a length-21 sequence in facility order,
    or a mapping keyed by facility numbers (integers or strings).
    """
    raw_costs = params["activation_cost"]
    if isinstance(raw_costs, Mapping):
        costs = {
            facility: (
                raw_costs[facility]
                if facility in raw_costs
                else raw_costs[str(facility)]
            )
            for facility in range(1, 22)
        }
    else:
        if len(raw_costs) != 21:
            raise ValueError("activation_cost must contain 21 costs")
        costs = {
            facility: raw_costs[facility - 1]
            for facility in range(1, 22)
        }

    coverage = {
        1: [1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 18, 21],
        2: [1, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 19, 20],
        3: [4, 5, 6, 7, 8, 10, 18, 20, 21],
        4: [4, 5, 6, 9, 10, 11, 13, 14, 16, 17, 18, 19, 20, 21],
        5: [1, 2, 4, 9, 10, 11, 12, 13, 14, 15, 20],
        6: [1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 14, 15, 16, 18, 19, 21],
        7: [4, 5, 9, 10, 12, 14, 16, 17, 18, 20, 21],
        8: [2, 3, 4, 5, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20],
        9: [1, 2, 6, 11, 13, 14, 18, 20, 21],
        10: [1, 3, 5, 8, 11, 13, 14, 16, 17, 21],
        11: [1, 2, 3, 7, 8, 9, 10, 12, 15, 16, 17, 18, 19],
        12: [1, 2, 3, 4, 5, 13, 14, 15, 16, 17, 19, 21],
        13: [4, 5, 6, 7, 8, 12, 14, 15, 17, 18, 19, 21],
        14: [1, 2, 4, 5, 7, 9, 10, 11, 16, 17, 20, 21],
        15: [1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 16, 17, 21],
        16: [3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21],
        17: [4, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21],
        18: [3, 4, 5, 7, 8, 9, 13, 15, 18, 19, 20],
        19: [2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        20: [3, 6, 7, 8, 9, 10, 11, 12, 15, 16, 19, 21],
        21: [1, 2, 3, 4, 6, 7, 9, 11, 14, 17, 19],
        22: [1, 2, 4, 5, 6, 8, 10, 11, 14, 17, 18, 19, 20],
        23: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 21],
        24: [1, 2, 3, 4, 5, 8, 10, 11, 13, 14, 15, 16, 18, 20, 21],
        25: [2, 3, 8, 9, 10, 11, 13, 14, 15, 17, 18, 20],
        26: [1, 2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 18, 20, 21],
        27: [7, 8, 10, 12, 13, 14, 15, 16, 17, 18, 20],
        28: [4, 7, 8, 10, 11, 13, 14, 16, 17, 20, 21],
        29: [1, 4, 5, 6, 7, 10, 11, 12, 13, 15, 16, 18, 19, 21],
        30: [3, 6, 9, 11, 12, 15, 16, 21],
        31: [1, 3, 4, 10, 13, 14, 15, 18, 19, 21],
        32: [1, 2, 4, 10, 11, 13, 15, 16, 18, 20],
        33: [2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 17, 18, 19, 20, 21],
        34: [1, 4, 11, 12, 13, 14, 15, 16, 18, 20, 21],
        35: [2, 3, 5, 7, 9, 11, 13, 15, 16, 17, 18, 19, 20],
        36: [1, 3, 4, 5, 6, 7, 8, 9, 11, 13, 15, 16, 17, 19, 20, 21],
    }

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(1, 21)
    model.areas = pyo.RangeSet(1, 36)
    model.activation_cost = pyo.Param(
        model.facilities, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.facilities, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return sum(instance.x[facility] for facility in coverage[area]) >= 1

    model.coverage_requirement = pyo.Constraint(
        model.areas, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[facility] * model.x[facility]
            for facility in model.facilities
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