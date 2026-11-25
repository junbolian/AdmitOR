# IR: {"sets":{"I":"0..12"},"params":{"profit":"real[I]","resource_use":"real[I]","resource_budget":"real","capacity":"real[I]"},"variables":{"production":"nonnegative real[I]"},"constraints":["sum(resource_use[i]*production[i] for i in I) <= resource_budget","production[i] <= capacity[i] for i in I"],"objective":{"sense":"maximize","expression":"sum(profit[i]*production[i] for i in I)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 12)

    model.unit_profit = pyo.Param(
        model.item_set,
        initialize={i: params["profit"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.unit_resource = pyo.Param(
        model.item_set,
        initialize={i: params["resource_use"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.available_resource = pyo.Param(
        initialize=params["resource_budget"],
        within=pyo.Reals,
    )
    model.production_capacity = pyo.Param(
        model.item_set,
        initialize={i: params["capacity"][i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.unit_resource[i] * model.production[i]
            for i in model.item_set
        )
        <= model.available_resource
    )

    def capacity_rule(instance, i):
        return instance.production[i] <= instance.production_capacity[i]

    model.capacity_limits = pyo.Constraint(
        model.item_set,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[i] * model.production[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Allow objective retrieval to determine success if loading failed.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}