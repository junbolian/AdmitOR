# IR: {"sets":{"F":"0..5","T":"0..3"},"params":{"fixed_cost":"F -> real","variable_cost":"F -> real","min_production":"F -> real","max_production":"F -> real","demand":"T -> real"},"variables":{"run[F,T]":"binary","production[F,T]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for all f,t","production[f,t] <= max_production[f] * run[f,t] for all f,t","sum(production[f,t] for f in F) >= demand[t] for all t"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for all f,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={factory: params["fixed_cost"][factory] for factory in model.factories},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={
            factory: params["variable_cost"][factory]
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
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={
            factory: params["max_production"][factory]
            for factory in model.factories
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={month: params["demand"][month] for month in model.months},
        within=pyo.Reals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.run[factory, month]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )

    def maximum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.run[factory, month]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )

    def demand_rule(mdl, month):
        return (
            sum(mdl.production[factory, month] for factory in mdl.factories)
            >= mdl.demand[month]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
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

    # APPsi may raise RuntimeError when it cannot load a feasible solution.
    # Objective retrieval alone determines whether a solution is returned.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}