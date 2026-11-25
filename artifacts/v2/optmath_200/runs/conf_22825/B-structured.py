# IR: {"sets":{"products":"0..9"},"params":{"profit_per_unit":"real[products]","time_per_unit":"nonnegative_real[products]","total_capacity_hours":"nonnegative_real","min_demand":"nonnegative_real[products]","max_demand":"nonnegative_real[products]"},"variables":{"quantity":"nonnegative_real[products] (continuous)"},"constraints":["sum(time_per_unit[i]*quantity[i] for i in products) <= total_capacity_hours","quantity[i] >= min_demand[i] for i in products","quantity[i] <= max_demand[i] for i in products"],"objective":"maximize sum(profit_per_unit[i]*quantity[i] for i in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 9)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={i: params["profit_per_unit"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.total_capacity_hours = pyo.Param(
        initialize=params["total_capacity_hours"],
        within=pyo.NonNegativeReals,
    )
    model.min_demand = pyo.Param(
        model.products,
        initialize={i: params["min_demand"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.max_demand = pyo.Param(
        model.products,
        initialize={i: params["max_demand"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )

    model.quantity = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.production_capacity = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.quantity[i]
            for i in model.products
        ) <= model.total_capacity_hours
    )

    def minimum_demand_rule(instance, i):
        return instance.quantity[i] >= instance.min_demand[i]

    def maximum_demand_rule(instance, i):
        return instance.quantity[i] <= instance.max_demand[i]

    model.minimum_demand_constraints = pyo.Constraint(
        model.products, rule=minimum_demand_rule
    )
    model.maximum_demand_constraints = pyo.Constraint(
        model.products, rule=maximum_demand_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[i] * model.quantity[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}