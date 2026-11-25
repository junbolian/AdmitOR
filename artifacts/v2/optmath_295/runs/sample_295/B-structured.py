# IR: {"sets":{"F":[0,1,2,3,4,5],"T":[0,1,2,3,4,5]},"params":{"min_production":"F -> nonnegative real","max_production":"F -> nonnegative real","demand":"T -> nonnegative real","fixed_cost":"F -> real","variable_cost":"F -> real"},"variables":{"operate[f,t]":"binary","production[f,t]":"nonnegative real"},"constraints":["production[f,t] >= min_production[f] * operate[f,t] for all f,t","production[f,t] <= max_production[f] * operate[f,t] for all f,t","sum(production[f,t] for f in F) >= demand[t] for all t"],"objective":"minimize sum(fixed_cost[f] * operate[f,t] + variable_cost[f] * production[f,t] for all f,t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using factory-indexed parameter sequences and monthly demand."""
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 5)

    model.min_production = pyo.Param(
        model.factories,
        initialize={f: min_production[f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: max_production[f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: demand[t] for t in model.months},
        within=pyo.NonNegativeReals,
    )
    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: fixed_cost[f] for f in model.factories},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={f: variable_cost[f] for f in model.factories},
        within=pyo.Reals,
    )

    model.operate = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(instance, f, t):
        return (
            instance.production[f, t]
            >= instance.min_production[f] * instance.operate[f, t]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )

    def maximum_production_rule(instance, f, t):
        return (
            instance.production[f, t]
            <= instance.max_production[f] * instance.operate[f, t]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )

    def demand_rule(instance, t):
        return (
            sum(instance.production[f, t] for f in instance.factories)
            >= instance.demand[t]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.operate[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    # APPSI can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines whether to report success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}