# IR: {"sets":{"I":"0..44"},"params":{"profit_margins":"real[I]","resource_coefficients":"real[I]","resource_capacity":"real","production_capacities":"real[I]"},"variables":{"production":{"type":"continuous","domain":"nonnegative","index":"I"}},"constraints":["sum(resource_coefficients[i]*production[i] for i in I) <= resource_capacity","production[i] <= production_capacities[i] for i in I"],"objective":{"sense":"maximize","expression":"sum(profit_margins[i]*production[i] for i in I)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_coefficients = params["resource_coefficients"]
    resource_capacity = params["resource_capacity"]
    production_capacities = params["production_capacities"]

    model = pyo.ConcreteModel()
    model.item_indices = pyo.RangeSet(0, 44)

    model.profit_margins = pyo.Param(
        model.item_indices,
        initialize={i: profit_margins[i] for i in model.item_indices},
        within=pyo.Reals,
    )
    model.resource_coefficients = pyo.Param(
        model.item_indices,
        initialize={i: resource_coefficients[i] for i in model.item_indices},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=resource_capacity,
        within=pyo.Reals,
    )
    model.production_capacities = pyo.Param(
        model.item_indices,
        initialize={i: production_capacities[i] for i in model.item_indices},
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_indices,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_coefficients[i] * model.production[i]
            for i in model.item_indices
        )
        <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.production_capacities[i]

    model.production_limits = pyo.Constraint(
        model.item_indices,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margins[i] * model.production[i]
            for i in model.item_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}