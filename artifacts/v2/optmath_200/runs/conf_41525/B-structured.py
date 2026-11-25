# IR: {"sets":{"item_set":"0..20"},"params":{"profit":"real[item_set]","resource_rate":"real[item_set]","resource_capacity":"real","production_limit":"real[item_set]"},"variables":{"quantity":"nonnegative real[item_set]"},"constraints":["sum(resource_rate[i]*quantity[i] for i in item_set) <= resource_capacity","quantity[i] <= production_limit[i] for each i in item_set"],"objective":"maximize sum(profit[i]*quantity[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 20)

    model.profit = pyo.Param(
        model.item_set,
        initialize={i: profit[i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_rate = pyo.Param(
        model.item_set,
        initialize={i: resource_rate[i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=resource_capacity,
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.item_set,
        initialize={i: production_limit[i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_rate[i] * model.quantity[i]
            for i in model.item_set
        ) <= model.resource_capacity
    )

    def production_limit_rule(block, i):
        return block.quantity[i] <= block.production_limit[i]

    model.production_constraints = pyo.Constraint(
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}