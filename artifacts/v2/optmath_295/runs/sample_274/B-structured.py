# IR: {"sets":{"packages":"0..10","legs":"0..4","leg_packages":{"0":[1,2,4,5,6,7],"1":[0,2,4,6,8,9,10],"2":[2,3,4,10],"3":[1,6,7,10],"4":[1,3,6,7,8,9]}},"params":{"revenues":"params['revenues'][package]","demand_limits":"params['demand_limits'][package]","leg_capacities":"params['leg_capacities'][leg]"},"variables":{"sales[package]":"nonnegative integer"},"constraints":["sales[package] <= demand_limits[package] for each package","sum(sales[package] for package in leg_packages[leg]) <= leg_capacities[leg] for each leg"],"objective":"maximize sum(revenues[package] * sales[package] for each package)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenues = params["revenues"]
    demand_limits = params["demand_limits"]
    leg_capacities = params["leg_capacities"]

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
        initialize=lambda mdl, package: revenues[package],
    )
    model.demand_limit = pyo.Param(
        model.packages,
        initialize=lambda mdl, package: demand_limits[package],
    )
    model.leg_capacity = pyo.Param(
        model.legs,
        initialize=lambda mdl, leg: leg_capacities[leg],
    )

    model.sales = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    model.demand_constraints = pyo.Constraint(
        model.packages,
        rule=lambda mdl, package: (
            mdl.sales[package] <= mdl.demand_limit[package]
        ),
    )

    model.capacity_constraints = pyo.Constraint(
        model.legs,
        rule=lambda mdl, leg: (
            sum(mdl.sales[package] for package in leg_packages[leg])
            <= mdl.leg_capacity[leg]
        ),
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
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}