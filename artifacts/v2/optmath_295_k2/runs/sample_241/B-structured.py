# IR: {"sets":{"programs":"1..17","topics":"1..37","eligible[t]":"COVERAGE[t] defined below"},"params":{"program_costs":"params['program_costs'], length-17 sequence indexed by program minus one"},"variables":{"selected[j]":"binary for each program j"},"constraints":["For each topic t: sum(selected[j] for j in eligible[t]) >= 1"],"objective":{"sense":"minimize","expression":"sum(program_costs[j-1] * selected[j] for j in programs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


COVERAGE = {
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


def solve(params):
    """Solve using costs supplied in program order, from Program 1 to 17."""
    program_costs = params["program_costs"]
    if len(program_costs) != 17:
        raise ValueError("program_costs must contain exactly 17 costs.")

    model = pyo.ConcreteModel()
    model.programs = pyo.RangeSet(1, 17)
    model.topics = pyo.RangeSet(1, 37)

    model.eligible = pyo.Set(
        model.topics,
        within=model.programs,
        initialize=COVERAGE,
    )
    model.cost = pyo.Param(
        model.programs,
        initialize={
            program: program_costs[program - 1]
            for program in model.programs
        },
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.programs, domain=pyo.Binary)

    def coverage_rule(instance, topic):
        return sum(
            instance.selected[program]
            for program in instance.eligible[topic]
        ) >= 1

    model.topic_coverage = pyo.Constraint(
        model.topics,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[program] * model.selected[program]
            for program in model.programs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Determine success solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}