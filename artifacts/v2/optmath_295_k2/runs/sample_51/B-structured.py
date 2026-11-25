# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3,4,5]},"params":{"fixed_cost":"factory-indexed","variable_cost":"factory-indexed","min_production":"factory-indexed","max_production":"factory-indexed","demand":"month-indexed"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for each factory f and month t","production[f,t] <= max_production[f]*run[f,t] for each factory f and month t","sum(production[f,t] for f in factories) >= demand[t] for each month t"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for each factory f and month t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["fixed_cost"][factory]
            for factory in model.factories
        },
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["variable_cost"][factory]
            for factory in model.factories
        },
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["min_production"][factory]
            for factory in model.factories
        },
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["max_production"][factory]
            for factory in model.factories
        },
    )
    model.demand = pyo.Param(
        model.months,
        initialize={
            month: params["demand"][month]
            for month in model.months
        },
    )

    model.run = pyo.Var(
        model.factories,
        model.months,
        domain=pyo.Binary,
    )
    model.production = pyo.Var(
        model.factories,
        model.months,
        domain=pyo.NonNegativeReals,
    )

    def minimum_production_rule(current_model, factory, month):
        return (
            current_model.production[factory, month]
            >= current_model.min_production[factory]
            * current_model.run[factory, month]
        )

    model.minimum_production_limit = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(current_model, factory, month):
        return (
            current_model.production[factory, month]
            <= current_model.max_production[factory]
            * current_model.run[factory, month]
        )

    model.maximum_production_limit = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_rule(current_model, month):
        return (
            sum(
                current_model.production[factory, month]
                for factory in current_model.factories
            )
            >= current_model.demand[month]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.run[factory, month]
            + model.variable_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}