# IR: {"sets":{"P":"0..22","R":"0..14","S[r]":"fixed package indices in route_packages[r]"},"params":{"revenue":"real[P], from params","demand_limit":"real[P], from params","route_capacity":"real[R], from params"},"variables":{"x[p]":"nonnegative integer units sold, p in P"},"constraints":["x[p] <= demand_limit[p] for p in P","sum(x[p] for p in S[r]) <= route_capacity[r] for r in R"],"objective":"maximize sum(revenue[p]*x[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    route_packages = {
        0: (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21),
        1: (1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 22),
        2: (2, 3, 4, 8, 9, 11, 12, 13, 15, 17, 18, 20, 21),
        3: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22),
        4: (1, 3, 4, 5, 7, 8, 9, 10, 13, 14, 15, 17, 18, 20, 21, 22),
        5: (0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 16, 17, 18, 20, 21, 22),
        6: (0, 1, 2, 3, 4, 5, 6, 8, 9, 13, 15, 16, 17, 18, 19, 21, 22),
        7: (0, 1, 2, 5, 7, 8, 10, 12, 14, 16, 19, 20, 21, 22),
        8: (2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22),
        9: (0, 1, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17, 18, 19, 20),
        10: (0, 1, 2, 3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 22),
        11: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21),
        12: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22),
        13: (0, 1, 2, 6, 7, 8, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22),
        14: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22),
    }

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 22)
    model.R = pyo.RangeSet(0, 14)

    model.revenue = pyo.Param(
        model.P,
        initialize={p: params["revenue"][p] for p in model.P},
        within=pyo.Reals,
    )
    model.demand_limit = pyo.Param(
        model.P,
        initialize={p: params["demand_limit"][p] for p in model.P},
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.R,
        initialize={r: params["route_capacity"][r] for r in model.R},
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(mdl, p):
        return mdl.x[p] <= mdl.demand_limit[p]

    model.demand_constraints = pyo.Constraint(model.P, rule=demand_rule)

    def route_rule(mdl, r):
        return (
            sum(mdl.x[p] for p in route_packages[r])
            <= mdl.route_capacity[r]
        )

    model.route_constraints = pyo.Constraint(model.R, rule=route_rule)

    model.total_revenue = pyo.Objective(
        expr=sum(model.revenue[p] * model.x[p] for p in model.P),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}