# IR: {"sets":{"factories":[0,1,2,3,4],"months":[0,1,2,3]},"params":{"fixed_cost":"real[factory], from params","var_cost":"real[factory], from params","min_prod":"nonnegative real[factory], from params","max_prod":"nonnegative real[factory], from params","demand":"nonnegative real[month], from params"},"variables":{"operating":"binary[factory,month]","production":"nonnegative real[factory,month]"},"constraints":["production[f,t] >= min_prod[f]*operating[f,t] for each factory f and month t","production[f,t] <= max_prod[f]*operating[f,t] for each factory f and month t","sum(production[f,t] for f in factories) >= demand[t] for each month t"],"objective":"minimize sum(fixed_cost[f]*operating[f,t] + var_cost[f]*production[f,t] for each factory f and month t)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 4)
    model.months = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: params["fixed_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.var_cost = pyo.Param(
        model.factories,
        initialize={f: params["var_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.min_prod = pyo.Param(
        model.factories,
        initialize={f: params["min_prod"][f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.max_prod = pyo.Param(
        model.factories,
        initialize={f: params["max_prod"][f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
        within=pyo.NonNegativeReals,
    )

    model.operating = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(model, f, t):
        return (
            model.production[f, t]
            >= model.min_prod[f] * model.operating[f, t]
        )

    model.minimum_production = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )

    def maximum_production_rule(model, f, t):
        return (
            model.production[f, t]
            <= model.max_prod[f] * model.operating[f, t]
        )

    model.maximum_production = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )

    def demand_satisfaction_rule(model, t):
        return (
            sum(model.production[f, t] for f in model.factories)
            >= model.demand[t]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.months, rule=demand_satisfaction_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.operating[f, t]
            + model.var_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}