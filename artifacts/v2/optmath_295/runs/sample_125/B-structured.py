# IR: {"sets":{"products":"0..11"},"params":{"profit_margin":"real[products]","time_per_unit":"real[products]","capacity_hours":"real","min_production":"real[products]","max_production":"real[products]"},"variables":{"quantity":"nonnegative real[products]"},"constraints":["sum(time_per_unit[i]*quantity[i] for i in products) <= capacity_hours","quantity[i] >= min_production[i] for i in products","quantity[i] <= max_production[i] for i in products"],"objective":"maximize sum(profit_margin[i]*quantity[i] for i in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 11)

    model.profit_margin = pyo.Param(
        model.products,
        initialize={i: params["profit_margin"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.capacity_hours = pyo.Param(
        initialize=params["capacity_hours"],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={i: params["min_production"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.products,
        initialize={i: params["max_production"][i] for i in model.products},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.quantity[i]
            for i in model.products
        ) <= model.capacity_hours
    )

    def minimum_rule(current_model, i):
        return current_model.quantity[i] >= current_model.min_production[i]

    def maximum_rule(current_model, i):
        return current_model.quantity[i] <= current_model.max_production[i]

    model.minimum_requirement = pyo.Constraint(
        model.products, rule=minimum_rule
    )
    model.maximum_requirement = pyo.Constraint(
        model.products, rule=maximum_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margin[i] * model.quantity[i]
            for i in model.products
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
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}