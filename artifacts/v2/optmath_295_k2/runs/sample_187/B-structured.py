# IR: {"sets":{"packages":"0..24","resources":"0..14","resource_packages":{"0":[2,4,5,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,24],"1":[0,1,2,4,6,7,8,9,10,11,12,14,16,17,19,20,21,22,23,24],"2":[0,1,5,6,8,9,13,14,15,16,17,19,23],"3":[0,2,3,4,5,6,8,9,10,11,12,13,15,17,18,19,20,21,22,23,24],"4":[1,2,3,5,7,8,9,10,11,12,13,14,15,17,19,20,22,23],"5":[1,2,6,9,10,12,14,15,16,17,18,19,21,22,23],"6":[0,1,2,3,4,5,7,9,10,11,12,14,15,16,17,19,20,22,23],"7":[0,1,2,5,6,8,9,11,12,13,14,15,16,17,18,20,21,22,24],"8":[1,2,4,5,6,8,10,12,13,14,16,17,18,19,20,22,23],"9":[0,1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,18,20,21,22],"10":[0,1,2,3,4,5,7,8,9,11,14,17,18,20,21,22,23,24],"11":[0,4,6,7,9,10,13,14,15,18,19,20,21,22,24],"12":[1,2,3,4,6,7,8,9,11,13,14,15,16,17,18,19,20,21,23,24],"13":[0,1,2,3,4,6,7,9,10,11,12,13,14,15,16,17,18,20,21,22,23,24],"14":[0,1,2,3,4,5,6,9,10,13,14,15,17,18,21,23]}},"params":{"revenue":"params['revenue'][p], p in packages","demand":"params['demand'][p], p in packages","capacity":"params['capacity'][r], r in resources"},"decision_variables":{"units[p]":"NonNegativeReals; continuous allocation because integrality is not explicitly required"},"constraints":["units[p] <= demand[p] for each package p","sum(units[p] for p in resource_packages[r]) <= capacity[r] for each resource r"],"objective":"maximize sum(revenue[p] * units[p] for p in packages)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous package-allocation model.

    Parameter arrays or mappings must support zero-based integer indexing.
    """
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    resource_packages = {
        0: (2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 24),
        1: (0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 19, 20, 21, 22, 23, 24),
        2: (0, 1, 5, 6, 8, 9, 13, 14, 15, 16, 17, 19, 23),
        3: (0, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24),
        4: (1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 20, 22, 23),
        5: (1, 2, 6, 9, 10, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23),
        6: (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19, 20, 22, 23),
        7: (0, 1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 24),
        8: (1, 2, 4, 5, 6, 8, 10, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23),
        9: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22),
        10: (0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 17, 18, 20, 21, 22, 23, 24),
        11: (0, 4, 6, 7, 9, 10, 13, 14, 15, 18, 19, 20, 21, 22, 24),
        12: (1, 2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24),
        13: (0, 1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24),
        14: (0, 1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 15, 17, 18, 21, 23),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 24)
    model.resources = pyo.RangeSet(0, 14)

    model.revenue = pyo.Param(
        model.packages,
        initialize={p: revenue[p] for p in model.packages},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize={p: demand[p] for p in model.packages},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.resources,
        initialize={r: capacity[r] for r in model.resources},
        within=pyo.Reals,
    )

    model.units = pyo.Var(model.packages, domain=pyo.NonNegativeReals)

    def demand_rule(instance, package):
        return instance.units[package] <= instance.demand[package]

    model.demand_limits = pyo.Constraint(model.packages, rule=demand_rule)

    def capacity_rule(instance, resource):
        return (
            sum(instance.units[p] for p in resource_packages[resource])
            <= instance.capacity[resource]
        )

    model.resource_limits = pyo.Constraint(model.resources, rule=capacity_rule)

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[p] * model.units[p]
            for p in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this specific error when no solution can be loaded.
        # Unexpected solver errors must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}