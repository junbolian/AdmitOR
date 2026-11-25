# IR: {"sets":{"item_set":"0..14"},"params":{"profit_per_unit":"real[item_set]","resource_consumption":"real[item_set]","resource_capacity":"real","max_production":"real[item_set]"},"decision_variables":{"production":"nonnegative continuous real[item_set]"},"constraints":["sum(resource_consumption[i]*production[i] for i in item_set) <= resource_capacity","production[i] <= max_production[i] for each i in item_set"],"objective":"maximize sum(profit_per_unit[i]*production[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    max_production = params["max_production"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 14)

    model.profit_per_unit = pyo.Param(
        model.item_set,
        initialize=lambda instance, i: profit_per_unit[i],
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize=lambda instance, i: resource_consumption[i],
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=resource_capacity,
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.item_set,
        initialize=lambda instance, i: max_production[i],
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.production[i]
            for i in model.item_set
        ) <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.max_production[i]

    model.production_limits = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[i] * model.production[i]
            for i in model.item_set
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