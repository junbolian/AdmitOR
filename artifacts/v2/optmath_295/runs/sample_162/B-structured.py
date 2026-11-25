# IR: {"sets":{"T":[0,1,2,3],"F":[0,1,2,3,4,5]},"params":{"fixed_cost":"F -> real, from params","variable_cost":"F -> real, from params","min_production":"F -> nonnegative real, from params","max_production":"F -> nonnegative real, from params","demand":"T -> nonnegative real, from params"},"variables":{"run[t,f]":"binary","production[t,f]":"nonnegative continuous"},"constraints":["production[t,f] >= min_production[f] * run[t,f] for all t,f","production[t,f] <= max_production[f] * run[t,f] for all t,f","sum(production[t,f] for f in F) >= demand[t] for all t"],"objective":"minimize sum(fixed_cost[f]*run[t,f] + variable_cost[f]*production[t,f] for t in T for f in F)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using factory-indexed cost/capacity data and month-indexed demand."""
    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(0, 3)
    model.F = pyo.RangeSet(0, 5)

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

    model.run = pyo.Var(model.T, model.F, domain=pyo.Binary)
    model.production = pyo.Var(
        model.T, model.F, domain=pyo.NonNegativeReals
    )

    model.minimum_production_constraint = pyo.Constraint(
        model.T,
        model.F,
        rule=lambda mdl, t, f: (
            mdl.production[t, f] >= mdl.min_production[f] * mdl.run[t, f]
        ),
    )
    model.maximum_production_constraint = pyo.Constraint(
        model.T,
        model.F,
        rule=lambda mdl, t, f: (
            mdl.production[t, f] <= mdl.max_production[f] * mdl.run[t, f]
        ),
    )
    model.demand_constraint = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.production[t, f] for f in mdl.F) >= mdl.demand[t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[t, f]
            + model.variable_cost[f] * model.production[t, f]
            for t in model.T
            for f in model.F
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