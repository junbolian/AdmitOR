# IR: {"sets":{"F":"0..5","T":"0..4"},"params":{"fixed_cost":"real[F]","variable_cost":"real[F]","min_production":"nonnegative_real[F]","max_production":"nonnegative_real[F]","demand":"nonnegative_real[T]"},"variables":{"run":"binary[F,T]","production":"nonnegative_real[F,T]"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F, t in T","production[f,t] <= max_production[f]*run[f,t] for f in F, t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 5)
    model.T = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={factory: params["fixed_cost"][factory] for factory in model.F},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.F,
        initialize={
            factory: params["variable_cost"][factory] for factory in model.F
        },
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.F,
        initialize={
            factory: params["min_production"][factory] for factory in model.F
        },
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.F,
        initialize={
            factory: params["max_production"][factory] for factory in model.F
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize={month: params["demand"][month] for month in model.T},
        within=pyo.NonNegativeReals,
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            >= instance.min_production[factory] * instance.run[factory, month]
        )

    def maximum_production_rule(instance, factory, month):
        return (
            instance.production[factory, month]
            <= instance.max_production[factory] * instance.run[factory, month]
        )

    def demand_satisfaction_rule(instance, month):
        return (
            sum(instance.production[factory, month] for factory in instance.F)
            >= instance.demand[month]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.F, model.T, rule=minimum_production_rule
    )
    model.maximum_production_constraint = pyo.Constraint(
        model.F, model.T, rule=maximum_production_rule
    )
    model.demand_satisfaction_constraint = pyo.Constraint(
        model.T, rule=demand_satisfaction_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.run[factory, month]
            + model.variable_cost[factory] * model.production[factory, month]
            for factory in model.F
            for month in model.T
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