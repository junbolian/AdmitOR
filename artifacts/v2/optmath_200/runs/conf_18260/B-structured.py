# IR: {"sets":{"S":"1..22","R":"1..36","C[r]":"fixed service indices in coverage[r] below"},"params":{"service_costs":"params['service_costs']: length-22 sequence, ordered by service"},"variables":{"x[s]":"Binary, s in S"},"constraints":["sum(x[s] for s in C[r]) >= 1, for each r in R"],"objective":"minimize sum(service_costs[s-1] * x[s] for s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    service_costs = params["service_costs"]
    if len(service_costs) != 22:
        raise ValueError("service_costs must contain exactly 22 entries.")

    coverage = {
        1: (2, 3, 4, 5, 6, 7, 10, 11, 12, 17, 19, 20),
        2: (4, 6, 7, 9, 10, 11, 12, 14, 15, 17, 19),
        3: (1, 3, 6, 7, 9, 10, 11, 12, 13, 14, 15, 19, 21, 22),
        4: (1, 2, 3, 5, 6, 7, 10, 12, 13, 14, 15, 17, 18, 21),
        5: (1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 18, 19, 21),
        6: (1, 3, 5, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 20, 21),
        7: (1, 2, 3, 6, 9, 11, 12, 13, 14, 21),
        8: (2, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 20, 21),
        9: (2, 3, 5, 6, 7, 9, 10, 12, 13, 14, 16, 18, 20, 21, 22),
        10: (5, 6, 8, 10, 11, 12, 13, 14, 16),
        11: (2, 3, 4, 5, 9, 10, 12, 15, 16, 18, 19, 21),
        12: (4, 5, 9, 10, 12, 13, 14, 15, 16, 19),
        13: (1, 2, 3, 4, 8, 11, 12, 14, 15, 17, 18, 20),
        14: (1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19, 20),
        15: (2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 15, 16, 18, 19, 20, 21, 22),
        16: (1, 2, 3, 11, 12, 13, 15, 16, 18, 20, 22),
        17: (2, 5, 8, 9, 13, 14, 15, 16, 17, 19, 21),
        18: (3, 5, 6, 8, 12, 16, 17, 18, 19, 20),
        19: (1, 4, 5, 6, 9, 12, 14, 17, 18, 19, 20, 21, 22),
        20: (1, 2, 3, 4, 7, 8, 13, 14, 15, 16, 17, 18, 20),
        21: (1, 3, 4, 8, 12, 13, 16, 17, 18, 19, 21, 22),
        22: (1, 4, 6, 8, 10, 11, 12, 13, 14, 17, 18, 20, 22),
        23: (1, 3, 4, 9, 10, 14, 15, 16, 17, 20, 21),
        24: (1, 2, 3, 4, 5, 6, 10, 11, 13, 14, 15, 16, 17),
        25: (6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 19, 20, 22),
        26: (2, 4, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20, 21, 22),
        27: (1, 2, 3, 4, 5, 6, 9, 11, 14, 15, 16, 18, 19, 20, 21, 22),
        28: (3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20),
        29: (
            1, 2, 3, 4, 5, 6, 7, 8, 10, 11,
            12, 14, 15, 17, 18, 19, 20, 21, 22,
        ),
        30: (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 17, 21, 22),
        31: (1, 2, 4, 5, 7, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 22),
        32: (2, 4, 6, 9, 10, 11, 14, 15, 16, 19, 21, 22),
        33: (2, 6, 8, 11, 14, 15, 16, 17, 18, 20, 21),
        34: (1, 3, 4, 6, 8, 11, 12, 14, 15, 18, 19, 20),
        35: (1, 3, 4, 5, 6, 7, 8, 10, 12, 14, 15, 17, 18, 19, 20, 22),
        36: (1, 3, 4, 7, 8, 9, 11, 15, 16, 19, 20, 21, 22),
    }

    model = pyo.ConcreteModel()
    model.services = pyo.RangeSet(1, 22)
    model.requirements = pyo.RangeSet(1, 36)

    model.covering_services = pyo.Set(
        model.requirements,
        within=model.services,
        initialize=coverage,
    )
    model.activation_cost = pyo.Param(
        model.services,
        initialize={
            service: service_costs[service - 1]
            for service in model.services
        },
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.services, domain=pyo.Binary)

    def requirement_rule(instance, requirement):
        return sum(
            instance.x[service]
            for service in instance.covering_services[requirement]
        ) >= 1

    model.requirement_coverage = pyo.Constraint(
        model.requirements,
        rule=requirement_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[service] * model.x[service]
            for service in model.services
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}