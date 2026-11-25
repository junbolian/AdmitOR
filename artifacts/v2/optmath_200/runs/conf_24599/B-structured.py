# IR: {"sets":{"factories":[0,1,2,3],"months":[0,1,2,3,4,5]},"params":{"fixed_cost":"params['fixed_cost'][factory]","var_cost":"params['var_cost'][factory]","min_prod":"params['min_prod'][factory]","max_prod":"params['max_prod'][factory]","demand":"params['demand'][month]"},"variables":{"run[factory,month]":"Binary","production[factory,month]":"NonNegativeReals"},"constraints":["production[f,t] >= min_prod[f] * run[f,t] for each factory f and month t","production[f,t] <= max_prod[f] * run[f,t] for each factory f and month t","sum(production[f,t] for f in factories) >= demand[t] for each month t"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + var_cost[f]*production[f,t] for f in factories and t in months)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 3)
    model.months = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["fixed_cost"][factory]
            for factory in model.factories
        },
    )
    model.var_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["var_cost"][factory]
            for factory in model.factories
        },
    )
    model.min_prod = pyo.Param(
        model.factories,
        initialize={
            factory: params["min_prod"][factory]
            for factory in model.factories
        },
    )
    model.max_prod = pyo.Param(
        model.factories,
        initialize={
            factory: params["max_prod"][factory]
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
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(problem, factory, month):
        return (
            problem.production[factory, month]
            >= problem.min_prod[factory] * problem.run[factory, month]
        )

    model.minimum_production = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(problem, factory, month):
        return (
            problem.production[factory, month]
            <= problem.max_prod[factory] * problem.run[factory, month]
        )

    model.maximum_production = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_satisfaction_rule(problem, month):
        return (
            sum(
                problem.production[factory, month]
                for factory in problem.factories
            )
            >= problem.demand[month]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=demand_satisfaction_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.run[factory, month]
            + model.var_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}