# {"sets":{"I":"0..45"},"params":{"profit_margins":"real[I]","resource_consumption":"real[I]","resource_capacity":"real","production_limits":"real[I]"},"variables":{"production":"nonnegative continuous[I]"},"constraints":["sum(resource_consumption[i]*production[i] for i in I) <= resource_capacity","production[i] <= production_limits[i] for i in I"],"objective":"maximize sum(profit_margins[i]*production[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 45)

    model.profit_margins = pyo.Param(
        model.item_set,
        initialize={i: params["profit_margins"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize={i: params["resource_consumption"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_limits = pyo.Param(
        model.item_set,
        initialize={i: params["production_limits"][i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_consumption[i] * model.production[i]
            for i in model.item_set
        )
        <= model.resource_capacity
    )

    def production_limit_rule(model, i):
        return model.production[i] <= model.production_limits[i]

    model.production_limit_constraints = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margins[i] * model.production[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_profit))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}