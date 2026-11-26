# IR: {"sets":{"I":[0,1,2]},"params":{"days":"nonnegative scalar","max_demand":"nonnegative vector indexed by I","price":"nonnegative vector indexed by I","cost":"nonnegative vector indexed by I","quota":"positive vector indexed by I","activation_cost":"nonnegative vector indexed by I","min_batch":"nonnegative vector indexed by I"},"variables":{"production[i]":"continuous nonnegative, in 100 kg units","line_enabled[i]":"binary"},"constraints":["sum(production[i]/quota[i] for i in I) <= days","production[i] <= max_demand[i]*line_enabled[i] for i in I","production[i] >= min_batch[i]*line_enabled[i] for i in I"],"objective":"maximize sum((price[i]-cost[i])*production[i]-activation_cost[i]*line_enabled[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Vector inputs use indices 0, 1, 2 for products A1, A2, A3."""
    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=range(3), ordered=True)

    model.available_days = pyo.Param(
        initialize=params["days"],
        within=pyo.NonNegativeReals,
    )
    model.demand_limit = pyo.Param(
        model.products,
        initialize={i: params["max_demand"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize={i: params["price"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.products,
        initialize={i: params["cost"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.daily_quota = pyo.Param(
        model.products,
        initialize={i: params["quota"][i] for i in model.products},
        within=pyo.PositiveReals,
    )
    model.fixed_cost = pyo.Param(
        model.products,
        initialize={i: params["activation_cost"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.minimum_batch = pyo.Param(
        model.products,
        initialize={i: params["min_batch"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.line_enabled = pyo.Var(model.products, domain=pyo.Binary)

    model.time_capacity = pyo.Constraint(
        expr=sum(
            model.production[i] / model.daily_quota[i]
            for i in model.products
        ) <= model.available_days
    )
    model.demand_and_activation = pyo.Constraint(
        model.products,
        rule=lambda mod, i: (
            mod.production[i] <= mod.demand_limit[i] * mod.line_enabled[i]
        ),
    )
    model.minimum_production = pyo.Constraint(
        model.products,
        rule=lambda mod, i: (
            mod.production[i] >= mod.minimum_batch[i] * mod.line_enabled[i]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (model.selling_price[i] - model.unit_cost[i]) * model.production[i]
            - model.fixed_cost[i] * model.line_enabled[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}