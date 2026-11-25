# IR: {"sets":{"teams":[1,2,3,4,5,6,7,8,9,10,11,12,13,14],"requirements":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],"coverage":{"1":[4,5,9,12,13,14],"2":[4,5,8],"3":[1,4,8,10,12],"4":[3,7,8,11,12,14],"5":[4,5,9,14],"6":[4,5,9,10,11,12,13],"7":[2,4,6,7,11],"8":[1,4,6,7,11,12],"9":[1,3,5,6,7,12],"10":[1,7,8,9,10,13],"11":[1,5,7,10,13,14],"12":[1,2,8,10,12,13,14],"13":[4,5,6,7,8,11],"14":[1,3,6,7,10],"15":[3,4,9,12,13,14],"16":[1,2,3,8,10,11],"17":[1,2,3,4,13],"18":[1,2,3,7,12,14],"19":[1,2,3,5,7,9,12]}},"params":{"cost[i]":"params['team_cost_'+str(i)] for i in teams","required[r]":"params['coverage_req_'+str(r)] for r in requirements"},"variables":{"selected[i]":{"type":"binary","index":"teams"}},"constraints":["For each r in requirements: sum(selected[i] for i in coverage[r]) >= required[r]"],"objective":{"sense":"minimize","expression":"sum(cost[i]*selected[i] for i in teams)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = {
        1: (4, 5, 9, 12, 13, 14),
        2: (4, 5, 8),
        3: (1, 4, 8, 10, 12),
        4: (3, 7, 8, 11, 12, 14),
        5: (4, 5, 9, 14),
        6: (4, 5, 9, 10, 11, 12, 13),
        7: (2, 4, 6, 7, 11),
        8: (1, 4, 6, 7, 11, 12),
        9: (1, 3, 5, 6, 7, 12),
        10: (1, 7, 8, 9, 10, 13),
        11: (1, 5, 7, 10, 13, 14),
        12: (1, 2, 8, 10, 12, 13, 14),
        13: (4, 5, 6, 7, 8, 11),
        14: (1, 3, 6, 7, 10),
        15: (3, 4, 9, 12, 13, 14),
        16: (1, 2, 3, 8, 10, 11),
        17: (1, 2, 3, 4, 13),
        18: (1, 2, 3, 7, 12, 14),
        19: (1, 2, 3, 5, 7, 9, 12),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 14)
    model.requirements = pyo.RangeSet(1, 19)

    model.cost = pyo.Param(
        model.teams,
        initialize={i: params[f"team_cost_{i}"] for i in model.teams},
        within=pyo.Reals,
    )
    model.required = pyo.Param(
        model.requirements,
        initialize={
            r: params[f"coverage_req_{r}"] for r in model.requirements
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, r):
        return (
            sum(instance.selected[i] for i in coverage[r])
            >= instance.required[r]
        )

    model.coverage_constraints = pyo.Constraint(
        model.requirements, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.selected[i] for i in model.teams),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Success is still determined exclusively by objective retrieval.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}