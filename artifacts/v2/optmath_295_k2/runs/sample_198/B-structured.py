# IR: {"sets":{"item_set":"0..19"},"params":{"profit_margin":"real[item_set], from params","resource_consumption":"real[item_set], from params","resource_capacity":"real scalar, from params","production_limit":"real[item_set], from params"},"variables":{"quantity":"NonNegativeReals[item_set]"},"constraints":["sum(resource_consumption[i]*quantity[i] for i in item_set) <= resource_capacity","quantity[i] <= production_limit[i] for each i in item_set"],"objective":"maximize sum(profit_margin[i]*quantity[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 19)

    model.profit_margin = pyo.Param(
        model.item_set,
        initialize={
            item: params["profit_margin"][item] for item in model.item_set
        },
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize={
            item: params["resource_consumption"][item]
            for item in model.item_set
        },
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.item_set,
        initialize={
            item: params["production_limit"][item] for item in model.item_set
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption[item] * model.quantity[item]
            for item in model.item_set
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, item):
        return instance.quantity[item] <= instance.production_limit[item]

    model.production_constraints = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margin[item] * model.quantity[item]
            for item in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}