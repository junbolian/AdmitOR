# IR: {"sets":{"factories":[0,1,2,3,4,5],"months":[0,1,2,3,4,5]},"params":{"fixed_cost":"factory-indexed","variable_cost":"factory-indexed","min_production":"factory-indexed","max_production":"factory-indexed","demand":"month-indexed"},"variables":{"running[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f] * running[f,t] for every factory f and month t","production[f,t] <= max_production[f] * running[f,t] for every factory f and month t","sum(production[f,t] for f in factories) >= demand[t] for every month t"],"objective":"minimize sum(fixed_cost[f] * running[f,t] + variable_cost[f] * production[f,t] for every factory f and month t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: fixed_cost[factory],
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: variable_cost[factory],
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: min_production[factory],
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize=lambda mdl, factory: max_production[factory],
    )
    model.demand = pyo.Param(
        model.months,
        initialize=lambda mdl, month: demand[month],
    )

    model.running = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.running[factory, month]
        )

    def maximum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.running[factory, month]
        )

    def demand_satisfaction_rule(mdl, month):
        return (
            sum(mdl.production[factory, month] for factory in mdl.factories)
            >= mdl.demand[month]
        )

    model.minimum_production_limit = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )
    model.maximum_production_limit = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )
    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=demand_satisfaction_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.running[factory, month]
            + model.variable_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # No solution was loaded; objective retrieval below determines success.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}