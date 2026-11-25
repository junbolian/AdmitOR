# IR: {"sets":{"factories":[0,1,2,3],"months":[0,1,2,3,4]},"params":{"fixed_cost":"factory-indexed","variable_cost":"factory-indexed","min_production":"factory-indexed","max_production":"factory-indexed","demand":"month-indexed"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for each factory f and month t","production[f,t] <= max_production[f] * run[f,t] for each factory f and month t","sum(production[f,t] for f in factories) >= demand[t] for each month t"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in factories and t in months)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 3)
    model.months = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: params["fixed_cost"][f],
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: params["variable_cost"][f],
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: params["min_production"][f],
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: params["max_production"][f],
    )
    model.demand = pyo.Param(
        model.months,
        initialize=lambda mdl, t: params["demand"][t],
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(mdl, f, t):
        return (
            mdl.production[f, t]
            >= mdl.min_production[f] * mdl.run[f, t]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=minimum_production_rule,
    )

    def maximum_production_rule(mdl, f, t):
        return (
            mdl.production[f, t]
            <= mdl.max_production[f] * mdl.run[f, t]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=maximum_production_rule,
    )

    def demand_rule(mdl, t):
        return (
            sum(mdl.production[f, t] for f in mdl.factories)
            >= mdl.demand[t]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
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