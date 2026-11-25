# IR: {"sets":{"F":"range(params['num_factories'])","T":"range(params['num_months'])"},"params":{"num_factories":"integer index-set size","num_months":"integer index-set size","activation_cost":"real[F]","production_cost":"real[F]","min_production":"nonnegative real[F]","max_production":"nonnegative real[F]","demand":"nonnegative real[T]"},"variables":{"run":"binary[F,T]","production":"nonnegative continuous[F,T]"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(activation_cost[f]*run[f,t] + production_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.Set(
        initialize=range(params["num_factories"]), ordered=True
    )
    model.months = pyo.Set(
        initialize=range(params["num_months"]), ordered=True
    )

    model.activation_cost = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["activation_cost"][factory],
        within=pyo.Reals,
    )
    model.production_cost = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["production_cost"][factory],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["min_production"][factory],
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["max_production"][factory],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize=lambda _, month: params["demand"][month],
        within=pyo.NonNegativeReals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            >= instance.min_production[factory] * instance.run[factory, month]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )

    def maximum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            <= instance.max_production[factory] * instance.run[factory, month]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )

    def demand_rule(instance, month):
        return (
            sum(
                instance.production[factory, month]
                for factory in instance.factories
            )
            >= instance.demand[month]
        )

    model.demand_constraint = pyo.Constraint(model.months, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[factory] * model.run[factory, month]
            + model.production_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}