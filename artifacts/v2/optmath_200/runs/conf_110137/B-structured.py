# IR: {"sets":{"products":"0..10"},"params":{"profit":"indexed by products","time_per_unit":"indexed by products","time_capacity":"scalar","min_production":"indexed by products","max_production":"indexed by products"},"variables":{"quantity":{"index":"products","type":"NonNegativeReals"}},"constraints":["sum(time_per_unit[i]*quantity[i] for i in products) <= time_capacity","quantity[i] >= min_production[i] for each i in products","quantity[i] <= max_production[i] for each i in products"],"objective":{"sense":"maximize","expression":"sum(profit[i]*quantity[i] for i in products)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={i: params["profit"][i] for i in model.products},
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
    )
    model.time_capacity = pyo.Param(
        initialize=params["time_capacity"],
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={i: params["min_production"][i] for i in model.products},
    )
    model.max_production = pyo.Param(
        model.products,
        initialize={i: params["max_production"][i] for i in model.products},
    )

    model.quantity = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.time_limit = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.quantity[i]
            for i in model.products
        ) <= model.time_capacity
    )

    def minimum_rule(instance, i):
        return instance.quantity[i] >= instance.min_production[i]

    def maximum_rule(instance, i):
        return instance.quantity[i] <= instance.max_production[i]

    model.minimum_limits = pyo.Constraint(
        model.products, rule=minimum_rule
    )
    model.maximum_limits = pyo.Constraint(
        model.products, rule=maximum_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}