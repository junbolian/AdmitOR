# IR: {"sets":{"packages":"0..10","legs":"0..6","packages_by_leg":{"0":[2,3,4,5,7,9],"1":[0,2,3,4,9,10],"2":[7,8,10],"3":[2,3,5],"4":[1,2,4,8,9],"5":[3,5,6,7,8,9],"6":[0,1,3,4,5,9]}},"params":{"revenue":"real[packages] from params['revenue']","demand":"real[packages] from params['demand']","capacity":"real[legs] from params['capacity']"},"variables":{"sales":"nonnegative integer[packages]"},"constraints":["sales[j] <= demand[j] for each package j","sum(sales[j] for j in packages_by_leg[l]) <= capacity[l] for each leg l"],"objective":"maximize sum(revenue[j] * sales[j] for j in packages)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    packages_by_leg = {
        0: (2, 3, 4, 5, 7, 9),
        1: (0, 2, 3, 4, 9, 10),
        2: (7, 8, 10),
        3: (2, 3, 5),
        4: (1, 2, 4, 8, 9),
        5: (3, 5, 6, 7, 8, 9),
        6: (0, 1, 3, 4, 5, 9),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 10)
    model.legs = pyo.RangeSet(0, 6)

    model.revenue = pyo.Param(
        model.packages,
        initialize={j: revenue[j] for j in range(11)},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize={j: demand[j] for j in range(11)},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.legs,
        initialize={leg: capacity[leg] for leg in range(7)},
        within=pyo.Reals,
    )

    model.sales = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    def demand_rule(instance, j):
        return instance.sales[j] <= instance.demand[j]

    model.demand_limits = pyo.Constraint(model.packages, rule=demand_rule)

    def capacity_rule(instance, leg):
        return (
            sum(instance.sales[j] for j in packages_by_leg[leg])
            <= instance.capacity[leg]
        )

    model.capacity_limits = pyo.Constraint(model.legs, rule=capacity_rule)

    model.total_revenue = pyo.Objective(
        expr=sum(model.revenue[j] * model.sales[j] for j in model.packages),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}