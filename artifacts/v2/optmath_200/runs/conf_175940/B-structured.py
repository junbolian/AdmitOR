# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3,4,5]},"params":{"fixed_cost":{"index":"F","domain":"Reals"},"variable_cost":{"index":"F","domain":"Reals"},"min_production":{"index":"F","domain":"NonNegativeReals"},"max_production":{"index":"F","domain":"NonNegativeReals"},"demand":{"index":"T","domain":"NonNegativeReals"}},"variables":{"activated":{"index":"F x T","type":"Binary"},"production":{"index":"F x T","type":"NonNegativeReals"}},"constraints":["production[f,t] >= min_production[f] * activated[f,t] for f in F, t in T","production[f,t] <= max_production[f] * activated[f,t] for f in F, t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":{"sense":"minimize","expression":"sum(fixed_cost[f] * activated[f,t] + variable_cost[f] * production[f,t] for f in F, t in T)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, f: params["fixed_cost"][f],
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, f: params["variable_cost"][f],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.F,
        initialize=lambda mdl, f: params["min_production"][f],
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.F,
        initialize=lambda mdl, f: params["max_production"][f],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=lambda mdl, t: params["demand"][t],
        within=pyo.NonNegativeReals,
    )

    model.activated = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t]
            >= mdl.min_production[f] * mdl.activated[f, t]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t]
            <= mdl.max_production[f] * mdl.activated[f, t]
        ),
    )
    model.demand_satisfaction = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.production[f, t] for f in mdl.F) >= mdl.demand[t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.activated[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.F
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}