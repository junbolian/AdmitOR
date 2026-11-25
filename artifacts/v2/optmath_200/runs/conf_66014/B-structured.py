# IR: {"sets":{"I":"0..48"},"params":{"profit_margins":"real[I]","resource_capacities":"real[I]","resource_budget":"real","production_limits":"real[I]"},"variables":{"production":"nonnegative continuous[I]"},"constraints":["sum(resource_capacities[i]*production[i] for i in I) <= resource_budget","production[i] <= production_limits[i] for i in I"],"objective":"maximize sum(profit_margins[i]*production[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 48)

    model.profit_margins = pyo.Param(
        model.item_set,
        initialize={i: params["profit_margins"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_capacities = pyo.Param(
        model.item_set,
        initialize={i: params["resource_capacities"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_budget = pyo.Param(
        initialize=params["resource_budget"],
        within=pyo.Reals,
    )
    model.production_limits = pyo.Param(
        model.item_set,
        initialize={i: params["production_limits"][i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.production = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_capacities[i] * model.production[i]
            for i in model.item_set
        ) <= model.resource_budget
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.production_limits[i]

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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}