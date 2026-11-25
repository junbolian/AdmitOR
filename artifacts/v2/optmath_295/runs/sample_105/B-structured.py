# IR: {"sets":{"packages":"0..21","legs":"0..19","leg_packages":[[1,2,3,5,7,8,9,12,13,14,16,19,21],[3,4,5,6,9,14,16,17,18,20],[0,2,3,4,5,6,8,9,11,12,13,14,15,18,19,20,21],[4,5,6,8,9,10,11,12,13,14,16,18,19,21],[3,4,8,9,10,12,15],[0,1,2,3,4,5,6,9,10,14,16,17,18,19,20,21],[0,5,7,8,10,11,14,17,18,20],[0,7,10,12,13,18,19,20,21],[3,7,8,9,10,13,15,17,19,20],[0,3,5,6,9,10,11,14,15,16],[0,1,5,6,9,11,12,19,20],[2,6,9,10,12,14,15,16,18,19],[0,1,2,3,5,8,9,10,12,15,17,18,19,21],[0,1,4,5,8,9,11,15,16,17,18],[5,6,8,11,12,14,15,16],[1,3,10,12,13,15,16,18],[1,4,5,6,7,8,11,12,15,18,20,21],[4,6,7,8,11,12,13,14,17,19,20,21],[4,8,10,11,12,16,20],[1,2,6,7,8,9,10,11,12,14,16,20,21]]},"params":{"revenue":{"index":"packages","type":"real","source":"params['revenue']"},"demand_limit":{"index":"packages","type":"real","source":"params['demand_limit']"},"seat_capacity":{"index":"legs","type":"real","source":"params['seat_capacity']"}},"decision_variables":{"sales":{"index":"packages","type":"nonnegative_integer"}},"constraints":["sales[p] <= demand_limit[p] for each package p","sum(sales[p] for p in leg_packages[l]) <= seat_capacity[l] for each leg l"],"objective":{"sense":"maximize","expression":"sum(revenue[p] * sales[p] for p in packages)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Build and solve the integer vacation-package revenue model."""
    leg_packages = (
        (1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 16, 19, 21),
        (3, 4, 5, 6, 9, 14, 16, 17, 18, 20),
        (0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 18, 19, 20, 21),
        (4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 21),
        (3, 4, 8, 9, 10, 12, 15),
        (0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 16, 17, 18, 19, 20, 21),
        (0, 5, 7, 8, 10, 11, 14, 17, 18, 20),
        (0, 7, 10, 12, 13, 18, 19, 20, 21),
        (3, 7, 8, 9, 10, 13, 15, 17, 19, 20),
        (0, 3, 5, 6, 9, 10, 11, 14, 15, 16),
        (0, 1, 5, 6, 9, 11, 12, 19, 20),
        (2, 6, 9, 10, 12, 14, 15, 16, 18, 19),
        (0, 1, 2, 3, 5, 8, 9, 10, 12, 15, 17, 18, 19, 21),
        (0, 1, 4, 5, 8, 9, 11, 15, 16, 17, 18),
        (5, 6, 8, 11, 12, 14, 15, 16),
        (1, 3, 10, 12, 13, 15, 16, 18),
        (1, 4, 5, 6, 7, 8, 11, 12, 15, 18, 20, 21),
        (4, 6, 7, 8, 11, 12, 13, 14, 17, 19, 20, 21),
        (4, 8, 10, 11, 12, 16, 20),
        (1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 21),
    )

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 21)
    model.legs = pyo.RangeSet(0, 19)

    model.revenue = pyo.Param(
        model.packages,
        initialize={
            package: params["revenue"][package]
            for package in model.packages
        },
        within=pyo.Reals,
    )
    model.demand_limit = pyo.Param(
        model.packages,
        initialize={
            package: params["demand_limit"][package]
            for package in model.packages
        },
        within=pyo.Reals,
    )
    model.seat_capacity = pyo.Param(
        model.legs,
        initialize={
            leg: params["seat_capacity"][leg]
            for leg in model.legs
        },
        within=pyo.Reals,
    )

    model.sales = pyo.Var(
        model.packages,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(instance, package):
        return instance.sales[package] <= instance.demand_limit[package]

    model.demand_constraints = pyo.Constraint(
        model.packages,
        rule=demand_rule,
    )

    def capacity_rule(instance, leg):
        return (
            sum(instance.sales[package] for package in leg_packages[leg])
            <= instance.seat_capacity[leg]
        )

    model.capacity_constraints = pyo.Constraint(
        model.legs,
        rule=capacity_rule,
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[package] * model.sales[package]
            for package in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Preserve unexpected RuntimeErrors for the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}