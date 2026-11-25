# IR: {"sets":{"packages":"0..22","routes":"0..14","route_packages":[[0,1,2,3,4,5,6,7,8,10,11,12,15,16,17,18,19,20,21],[1,2,4,5,6,8,9,10,11,12,14,15,16,17,18,19,22],[2,3,4,8,9,11,12,13,15,17,18,20,21],[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20,21,22],[1,3,4,5,7,8,9,10,13,14,15,17,18,20,21,22],[0,1,2,4,5,6,8,9,10,11,12,13,16,17,18,20,21,22],[0,1,2,3,4,5,6,8,9,13,15,16,17,18,19,21,22],[0,1,2,5,7,8,10,12,14,16,19,20,21,22],[2,3,4,5,6,7,9,10,12,13,14,15,16,17,18,19,20,21,22],[0,1,5,6,7,8,9,10,13,14,15,17,18,19,20],[0,1,2,3,4,6,8,9,10,12,13,14,15,16,17,22],[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21],[0,1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22],[0,1,2,6,7,8,10,11,13,15,16,17,18,19,20,22],[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22]]},"params":{"revenue":"params['revenue'][i]","demand_limit":"params['demand_limit'][i]","route_capacity":"params['route_capacity'][r]"},"variables":{"units[i]":"nonnegative integer"},"constraints":["units[i] <= demand_limit[i] for each package i","sum(units[i] for i in route_packages[r]) <= route_capacity[r] for each route r"],"objective":"maximize sum(revenue[i] * units[i] for each package i)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    route_packages = (
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21),
        (1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 22),
        (2, 3, 4, 8, 9, 11, 12, 13, 15, 17, 18, 20, 21),
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22),
        (1, 3, 4, 5, 7, 8, 9, 10, 13, 14, 15, 17, 18, 20, 21, 22),
        (0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 16, 17, 18, 20, 21, 22),
        (0, 1, 2, 3, 4, 5, 6, 8, 9, 13, 15, 16, 17, 18, 19, 21, 22),
        (0, 1, 2, 5, 7, 8, 10, 12, 14, 16, 19, 20, 21, 22),
        (2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22),
        (0, 1, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17, 18, 19, 20),
        (0, 1, 2, 3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 22),
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21),
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22),
        (0, 1, 2, 6, 7, 8, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22),
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22),
    )

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 22)
    model.routes = pyo.RangeSet(0, 14)

    model.revenue = pyo.Param(
        model.packages,
        initialize={i: params["revenue"][i] for i in model.packages},
    )
    model.demand_limit = pyo.Param(
        model.packages,
        initialize={i: params["demand_limit"][i] for i in model.packages},
    )
    model.route_capacity = pyo.Param(
        model.routes,
        initialize={r: params["route_capacity"][r] for r in model.routes},
    )

    model.units = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    model.demand_constraints = pyo.Constraint(
        model.packages,
        rule=lambda mdl, i: mdl.units[i] <= mdl.demand_limit[i],
    )
    model.route_constraints = pyo.Constraint(
        model.routes,
        rule=lambda mdl, r: (
            sum(mdl.units[i] for i in route_packages[r])
            <= mdl.route_capacity[r]
        ),
    )
    model.total_revenue = pyo.Objective(
        expr=sum(model.revenue[i] * model.units[i] for i in model.packages),
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