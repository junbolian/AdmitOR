# IR {
#   "sets": {"P": "0..20", "F": "0..17", "U[f]": "fixed package incidence for flight f, as specified in the problem"},
#   "params": {"revenue[p]": "params['revenue'][p]", "demand[p]": "params['demand'][p]", "flight_capacity[f]": "params['flight_capacity'][f]"},
#   "variables": {"Sell[p]": "nonnegative integer, for every p in P"},
#   "constraints": [
#     "Sell[p] <= demand[p], for every p in P",
#     "sum(Sell[p] for p in U[f]) <= flight_capacity[f], for every f in F"
#   ],
#   "objective": "maximize sum(revenue[p] * Sell[p] for p in P)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    flight_packages = {
        0: (0, 2, 4, 7, 11, 12, 16, 17, 19),
        1: (0, 1, 7, 9, 10, 11, 15, 20),
        2: (0, 1, 3, 4, 7, 11, 13, 15, 17, 19),
        3: (6, 7, 9, 15, 16, 17, 18, 19),
        4: (2, 3, 4, 5, 7, 11, 12, 13, 15, 16, 17, 19, 20),
        5: (0, 1, 3, 4, 5, 6, 8, 9, 10, 12, 14, 18),
        6: (1, 4, 5, 7, 8, 10, 13, 14, 16, 17, 18, 19, 20),
        7: (0, 1, 2, 4, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20),
        8: (0, 5, 9, 10, 12, 14, 15, 16, 20),
        9: (2, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19),
        10: (2, 6, 12, 15, 17, 18),
        11: (1, 10, 13, 14, 15, 19),
        12: (1, 2, 4, 5, 6, 8, 9, 11, 13, 14, 17, 18, 20),
        13: (0, 1, 4, 5, 7, 8, 9, 10, 14, 16, 17, 19),
        14: (0, 1, 2, 3, 7, 9, 11, 14, 16, 18, 19),
        15: (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 15, 19),
        16: (2, 6, 8, 9, 12, 13, 16, 17, 19, 20),
        17: (1, 2, 3, 6, 7, 10, 11, 14, 18),
    }

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 20)
    model.F = pyo.RangeSet(0, 17)
    model.U = pyo.Set(
        model.F,
        within=model.P,
        initialize=flight_packages,
    )

    model.revenue = pyo.Param(
        model.P,
        initialize=lambda model, package: revenue[package],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.P,
        initialize=lambda model, package: demand[package],
        within=pyo.Reals,
    )
    model.flight_capacity = pyo.Param(
        model.F,
        initialize=lambda model, flight: flight_capacity[flight],
        within=pyo.Reals,
    )

    model.Sell = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    model.demand_limit = pyo.Constraint(
        model.P,
        rule=lambda model, package: (
            model.Sell[package] <= model.demand[package]
        ),
    )

    def flight_capacity_rule(model, flight):
        return (
            pyo.quicksum(model.Sell[package] for package in model.U[flight])
            <= model.flight_capacity[flight]
        )

    model.seat_limit = pyo.Constraint(
        model.F,
        rule=flight_capacity_rule,
    )

    model.total_revenue = pyo.Objective(
        expr=pyo.quicksum(
            model.revenue[package] * model.Sell[package]
            for package in model.P
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue, exception=True))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}