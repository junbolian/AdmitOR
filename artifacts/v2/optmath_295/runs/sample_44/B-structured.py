# IR: {"sets":{"F":[0,1,2,3,4],"T":[0,1,2,3,4,5]},"params":{"fixed_costs":"real[F]","variable_costs":"real[F]","min_production":"real[F]","max_production":"real[F]","demand":"real[T]"},"variables":{"run":"binary[F,T]","production":"nonnegative_real[F,T]"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_costs[f]*run[f,t] + variable_costs[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 4)
    model.months = pyo.RangeSet(0, 5)

    model.fixed_costs = pyo.Param(
        model.factories,
        initialize={
            factory_idx: params["fixed_costs"][factory_idx]
            for factory_idx in model.factories
        },
        within=pyo.Reals,
    )
    model.variable_costs = pyo.Param(
        model.factories,
        initialize={
            factory_idx: params["variable_costs"][factory_idx]
            for factory_idx in model.factories
        },
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={
            factory_idx: params["min_production"][factory_idx]
            for factory_idx in model.factories
        },
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={
            factory_idx: params["max_production"][factory_idx]
            for factory_idx in model.factories
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={
            month_idx: params["demand"][month_idx]
            for month_idx in model.months
        },
        within=pyo.Reals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(problem, factory_idx, month_idx):
        return (
            problem.production[factory_idx, month_idx]
            >= problem.min_production[factory_idx]
            * problem.run[factory_idx, month_idx]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(problem, factory_idx, month_idx):
        return (
            problem.production[factory_idx, month_idx]
            <= problem.max_production[factory_idx]
            * problem.run[factory_idx, month_idx]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_rule(problem, month_idx):
        return (
            sum(
                problem.production[factory_idx, month_idx]
                for factory_idx in problem.factories
            )
            >= problem.demand[month_idx]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_costs[factory_idx]
            * model.run[factory_idx, month_idx]
            + model.variable_costs[factory_idx]
            * model.production[factory_idx, month_idx]
            for factory_idx in model.factories
            for month_idx in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}