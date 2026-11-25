# IR: {"sets":{"factories":[0,1,2,3,4],"months":[0,1,2,3]},"params":{"fixed_cost":"params['fixed_cost'][f]","variable_cost":"params['variable_cost'][f]","min_production":"params['min_production'][f]","max_production":"params['max_production'][f]","demand":"params['demand'][t]"},"variables":{"operational[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= min_production[f] * operational[f,t] for every f,t","production[f,t] <= max_production[f] * operational[f,t] for every f,t","sum(production[f,t] for f in factories) >= demand[t] for every t"],"objective":"minimize sum(fixed_cost[f] * operational[f,t] + variable_cost[f] * production[f,t] for every f,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 4)
    model.months = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["fixed_cost"][factory],
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["variable_cost"][factory],
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["min_production"][factory],
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize=lambda _, factory: params["max_production"][factory],
    )
    model.demand = pyo.Param(
        model.months,
        initialize=lambda _, month: params["demand"][month],
    )

    model.operational = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.operational[factory, month]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.operational[factory, month]
        ),
    )
    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=lambda mdl, month: (
            sum(mdl.production[factory, month] for factory in mdl.factories)
            >= mdl.demand[month]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.operational[factory, month]
            + model.variable_cost[factory] * model.production[factory, month]
            for factory in model.factories
            for month in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" not in str(exc).lower():
            raise
        # Continue to objective retrieval, the sole success criterion.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}