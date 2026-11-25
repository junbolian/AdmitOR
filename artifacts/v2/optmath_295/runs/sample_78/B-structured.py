# IR: {"sets":{"T":"1..12","L":"1..18","C":{"1":[4,8,10,11],"2":[2,3,7,8,10],"3":[1,4,6],"4":[8,10,12],"5":[1,3,4,8,11],"6":[1,2,6,7,8,12],"7":[1,2,4,6,9,11],"8":[2,7,8,11],"9":[2,3,4,6],"10":[2,3,5,6,9,10,11,12],"11":[2,3,4,10],"12":[4,5,9,10,11],"13":[7,9,12],"14":[1,7,9,11],"15":[6,7,8,9,10],"16":[1,4,6,7,9,10,12],"17":[4,5,7,8,10,12],"18":[1,5,8,9]}},"params":{"cost":"params['cost']; indexed by T","req":"params['req']; indexed by L"},"variables":{"deploy[t]":"Binary for t in T"},"constraints":["coverage[l]: sum(deploy[t] for t in C[l]) >= req[l], for l in L"],"objective":"minimize sum(cost[t] * deploy[t] for t in T)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, position):
    """Accept a mapping keyed by 1-based integers/strings or an ordered sequence."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[str(position)]
    return values[position - 1]


def solve(params):
    cost_data = params["cost"]
    req_data = params["req"]

    coverage = {
        1: (4, 8, 10, 11),
        2: (2, 3, 7, 8, 10),
        3: (1, 4, 6),
        4: (8, 10, 12),
        5: (1, 3, 4, 8, 11),
        6: (1, 2, 6, 7, 8, 12),
        7: (1, 2, 4, 6, 9, 11),
        8: (2, 7, 8, 11),
        9: (2, 3, 4, 6),
        10: (2, 3, 5, 6, 9, 10, 11, 12),
        11: (2, 3, 4, 10),
        12: (4, 5, 9, 10, 11),
        13: (7, 9, 12),
        14: (1, 7, 9, 11),
        15: (6, 7, 8, 9, 10),
        16: (1, 4, 6, 7, 9, 10, 12),
        17: (4, 5, 7, 8, 10, 12),
        18: (1, 5, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 12)
    model.locations = pyo.RangeSet(1, 18)

    model.cost = pyo.Param(
        model.teams,
        initialize={
            team: _indexed_value(cost_data, team)
            for team in model.teams
        },
        within=pyo.Reals,
    )
    model.req = pyo.Param(
        model.locations,
        initialize={
            location: _indexed_value(req_data, location)
            for location in model.locations
        },
        within=pyo.Reals,
    )

    model.deploy = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, location):
        return (
            sum(instance.deploy[team] for team in coverage[location])
            >= instance.req[location]
        )

    model.coverage_constraints = pyo.Constraint(
        model.locations, rule=coverage_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[team] * model.deploy[team]
            for team in model.teams
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}