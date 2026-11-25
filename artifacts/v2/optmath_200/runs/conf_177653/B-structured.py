# IR: {"sets":{"factories":[0,1,2,3],"months":[0,1,2]},"params":{"fixed_cost":"factories -> real","variable_cost":"factories -> real","min_production":"factories -> nonnegative real","max_production":"factories -> nonnegative real","demand":"months -> nonnegative real"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for all f,t","production[f,t] <= max_production[f] * run[f,t] for all f,t","sum_f production[f,t] >= demand[t] for all t"],"objective":"minimize sum_{f,t}(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 3)
    model.months = pyo.RangeSet(0, 2)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: params["fixed_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={f: params["variable_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={f: params["min_production"][f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: params["max_production"][f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
        within=pyo.NonNegativeReals,
    )

    model.run = pyo.Var(model.factories, model.months, domain=pyo.Binary)
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(model, f, t):
        return model.production[f, t] >= model.min_production[f] * model.run[f, t]

    model.minimum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )

    def maximum_production_rule(model, f, t):
        return model.production[f, t] <= model.max_production[f] * model.run[f, t]

    model.maximum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )

    def demand_rule(model, t):
        return (
            sum(model.production[f, t] for f in model.factories)
            >= model.demand[t]
        )

    model.demand_constraint = pyo.Constraint(model.months, rule=demand_rule)

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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}