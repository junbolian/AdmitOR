# IR: {"sets":{"item_set":"0..42"},"params":{"profit_margins":"real[item_set]","resource_consumption":"nonnegative_real[item_set]","resource_budget":"real","production_capacities":"real[item_set]"},"variables":{"production":"nonnegative_real[item_set]"},"constraints":["sum(resource_consumption[i]*production[i] for i in item_set) <= resource_budget","production[i] <= production_capacities[i] for each i in item_set"],"objective":"maximize sum(profit_margins[i]*production[i] for i in item_set)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 42)

    model.profit_margins = pyo.Param(
        model.item_set,
        initialize={i: params["profit_margins"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_consumption = pyo.Param(
        model.item_set,
        initialize={
            i: params["resource_consumption"][i] for i in model.item_set
        },
        within=pyo.NonNegativeReals,
    )
    model.resource_budget = pyo.Param(
        initialize=params["resource_budget"],
        within=pyo.Reals,
    )
    model.production_capacities = pyo.Param(
        model.item_set,
        initialize={
            i: params["production_capacities"][i] for i in model.item_set
        },
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
        )
        <= model.resource_budget
    )

    def capacity_rule(model, i):
        return model.production[i] <= model.production_capacities[i]

    model.capacity_limits = pyo.Constraint(
        model.item_set,
        rule=capacity_rule,
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
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}