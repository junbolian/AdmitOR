# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3,4]},"params":{"activation_cost":"factory-indexed real","production_cost":"factory-indexed real","min_production":"factory-indexed nonnegative real","max_production":"factory-indexed nonnegative real","demand":"month-indexed nonnegative real"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative real"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for all f,t","production[f,t] <= max_production[f] * run[f,t] for all f,t","sum(production[f,t] for f in factories) >= demand[t] for all t"],"objective":"minimize sum(activation_cost[f] * run[f,t] + production_cost[f] * production[f,t] for all f,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 4)

    model.activation_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["activation_cost"][factory]
            for factory in model.factories
        },
        within=pyo.Reals,
    )
    model.production_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["production_cost"][factory]
            for factory in model.factories
        },
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["min_production"][factory]
            for factory in model.factories
        },
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["max_production"][factory]
            for factory in model.factories
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={
            month: params["demand"][month]
            for month in model.months
        },
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
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            <= instance.max_production[factory] * instance.run[factory, month]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_rule(instance, month):
        return (
            sum(
                instance.production[factory, month]
                for factory in instance.factories
            )
            >= instance.demand[month]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
    )

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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}