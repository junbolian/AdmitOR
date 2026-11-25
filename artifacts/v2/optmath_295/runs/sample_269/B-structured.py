# IR: {"sets":{"item_set":"0..14"},"params":{"profit":"indexed by item_set","resource_consumption":"indexed by item_set","resource_capacity":"scalar","production_upper_limits":"indexed by item_set"},"decision_variables":{"quantity":{"index":"item_set","type":"continuous nonnegative"}},"constraints":["sum(resource_consumption[i]*quantity[i] for i in item_set) <= resource_capacity","quantity[i] <= production_upper_limits[i] for each i in item_set"],"objective":{"sense":"maximize","expression":"sum(profit[i]*quantity[i] for i in item_set)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_upper_limits = params["production_upper_limits"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 14)

    model.profit = pyo.Param(
        model.item_set,
        initialize={i: profit[i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize={i: resource_consumption[i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=resource_capacity,
        within=pyo.Reals,
    )
    model.production_upper_limits = pyo.Param(
        model.item_set,
        initialize={i: production_upper_limits[i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.quantity[i]
            for i in model.item_set
        )
        <= model.resource_capacity
    )

    def production_limit_rule(model, i):
        return model.quantity[i] <= model.production_upper_limits[i]

    model.production_limits = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.item_set
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