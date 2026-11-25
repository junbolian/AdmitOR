# IR: {"sets":{"F":"0..5","T":"0..4"},"params":{"fixed_cost":"real[F], params['fixed_cost']","variable_cost":"real[F], params['variable_cost']","min_production":"real[F], params['min_production']","max_production":"real[F], params['max_production']","demand":"real[T], params['demand']"},"variables":{"run":"binary[F,T]","production":"nonnegative real[F,T]"},"constraints":["forall f,t: production[f,t] >= min_production[f]*run[f,t]","forall f,t: production[f,t] <= max_production[f]*run[f,t]","forall t: sum(f in F, production[f,t]) >= demand[t]"],"objective":"minimize sum(f in F,t in T, fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 4)

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
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: params["max_production"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
        within=pyo.Reals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] >= mdl.min_production[f] * mdl.run[f, t]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] <= mdl.max_production[f] * mdl.run[f, t]
        ),
    )
    model.demand_satisfaction = pyo.Constraint(
        model.months,
        rule=lambda mdl, t: (
            sum(mdl.production[f, t] for f in mdl.factories)
            >= mdl.demand[t]
        ),
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}