# IR: {"sets":{"packages":[0,1,2,3,4,5,6,7,8,9,10],"legs":[0,1,2,3,4],"leg_packages":{"0":[1,2,4,5,6,7],"1":[0,2,4,6,8,9,10],"2":[2,3,4,10],"3":[1,6,7,10],"4":[1,3,6,7,8,9]}},"params":{"revenue":"indexed by packages","demand_limit":"indexed by packages","flight_capacity":"indexed by legs"},"variables":{"units[p]":"nonnegative integer"},"constraints":["units[p] <= demand_limit[p] for each package p","sum(units[p] for p in leg_packages[l]) <= flight_capacity[l] for each leg l"],"objective":"maximize sum(revenue[p] * units[p] for each package p)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    flight_capacity = params["flight_capacity"]

    leg_packages = {
        0: (1, 2, 4, 5, 6, 7),
        1: (0, 2, 4, 6, 8, 9, 10),
        2: (2, 3, 4, 10),
        3: (1, 6, 7, 10),
        4: (1, 3, 6, 7, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 10)
    model.legs = pyo.RangeSet(0, 4)

    model.revenue = pyo.Param(
        model.packages,
        initialize={pkg: revenue[pkg] for pkg in model.packages},
    )
    model.demand_limit = pyo.Param(
        model.packages,
        initialize={pkg: demand_limit[pkg] for pkg in model.packages},
    )
    model.flight_capacity = pyo.Param(
        model.legs,
        initialize={leg: flight_capacity[leg] for leg in model.legs},
    )

    model.units = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    def demand_rule(instance, pkg):
        return instance.units[pkg] <= instance.demand_limit[pkg]

    model.demand_constraints = pyo.Constraint(
        model.packages, rule=demand_rule
    )

    def capacity_rule(instance, leg):
        return (
            sum(instance.units[pkg] for pkg in leg_packages[leg])
            <= instance.flight_capacity[leg]
        )

    model.capacity_constraints = pyo.Constraint(
        model.legs, rule=capacity_rule
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[pkg] * model.units[pkg]
            for pkg in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}