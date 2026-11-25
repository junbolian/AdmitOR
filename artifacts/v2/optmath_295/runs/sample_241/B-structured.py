# IR: {"sets":{"P":"1..17","T":"1..37","C[t]":"program indices in topic_programs[t] below"},"params":{"program_costs":"params['program_costs']; length-17 sequence in program order or mapping keyed by program indices 1..17"},"variables":{"selected[p]":"Binary for p in P"},"constraints":["For each t in T: sum(selected[p] for p in C[t]) >= 1"],"objective":"Minimize sum(program_costs[p] * selected[p] for p in P)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_costs = params["program_costs"]

    if isinstance(raw_costs, Mapping):
        costs = {program: raw_costs[program] for program in range(1, 18)}
    else:
        if len(raw_costs) != 17:
            raise ValueError("program_costs must contain exactly 17 costs.")
        costs = {
            program: raw_costs[program - 1]
            for program in range(1, 18)
        }

    topic_programs = {
        1: (1, 2, 4, 6, 9, 10, 13, 14, 15, 17),
        2: (4, 5, 7, 8, 13, 17),
        3: (4, 5, 7, 8, 10, 11, 12, 15, 16, 17),
        4: (5, 6, 7, 11, 13, 16, 17),
        5: (2, 3, 4, 6, 8, 9, 10, 16),
        6: (2, 3, 4, 7, 11, 17),
        7: (4, 5, 9, 13, 17),
        8: (1, 4, 6, 7, 8, 10, 12, 13, 15, 17),
        9: (1, 7, 8, 12, 15, 16),
        10: (2, 3, 4, 5, 6, 9, 13, 16),
        11: (3, 7, 9, 11, 14, 15),
        12: (5, 7, 10, 12, 14),
        13: (1, 3, 5, 9, 10, 11, 13),
        14: (2, 7, 8, 13, 14, 15, 16),
        15: (2, 5, 8, 13, 16),
        16: (2, 3, 9),
        17: (2, 3, 4, 5, 7, 10, 13, 16),
        18: (3, 6, 7, 8, 9, 15, 16),
        19: (7, 9, 10, 13, 14, 15),
        20: (2, 3, 4, 5, 6, 11, 12, 14, 17),
        21: (1, 2, 7, 9, 12, 14, 16),
        22: (3, 4, 6, 9, 11, 16),
        23: (2, 6, 10, 11, 14),
        24: (1, 3, 6, 7, 11, 12, 13, 15, 16),
        25: (1, 3, 7, 8, 11, 12, 15),
        26: (3, 5, 10, 11, 12, 16),
        27: (6, 7, 9, 10, 11, 12, 16),
        28: (3, 4, 6, 7, 11, 12),
        29: (3, 6, 7, 10, 13, 16, 17),
        30: (2, 6, 9, 10, 13, 15, 16, 17),
        31: (2, 6, 7, 8, 9, 11, 12, 13, 17),
        32: (1, 7, 9, 13, 15),
        33: (1, 3, 6, 9, 13, 14),
        34: (2, 3, 6, 13, 14, 15, 17),
        35: (1, 2, 3, 6, 10, 11, 12, 17),
        36: (4, 5, 7, 12, 13),
        37: (2, 8, 11, 16),
    }

    model = pyo.ConcreteModel()
    model.programs = pyo.RangeSet(1, 17)
    model.topics = pyo.RangeSet(1, 37)
    model.program_cost = pyo.Param(
        model.programs,
        initialize=costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.programs, domain=pyo.Binary)

    def coverage_rule(block, topic):
        return sum(
            block.selected[program]
            for program in topic_programs[topic]
        ) >= 1

    model.topic_coverage = pyo.Constraint(
        model.topics,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.program_cost[program] * model.selected[program]
            for program in model.programs
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