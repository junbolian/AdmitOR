# IR: {"sets":{"F":[0,1,2,3,4,5],"T":[0,1,2,3,4,5]},"params":{"min_production":"indexed by F","max_production":"indexed by F","demand":"indexed by T","fixed_cost":"indexed by F","variable_cost":"indexed by F"},"variables":{"run[F,T]":"binary","production[F,T]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for f in F, t in T","production[f,t] <= max_production[f] * run[f,t] for f in F, t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()
    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 5)

    model.minimum_output = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: min_production[f],
    )
    model.maximum_output = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: max_production[f],
    )
    model.monthly_demand = pyo.Param(
        model.months,
        initialize=lambda mdl, t: demand[t],
    )
    model.operating_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: fixed_cost[f],
    )
    model.unit_cost = pyo.Param(
        model.factories,
        initialize=lambda mdl, f: variable_cost[f],
    )

    model.run = pyo.Var(model.factories, model.months, domain=pyo.Binary)
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] >= mdl.minimum_output[f] * mdl.run[f, t]
        ),
    )
    model.maximum_production_constraint = pyo.Constraint(
        model.factories,
        model.months,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] <= mdl.maximum_output[f] * mdl.run[f, t]
        ),
    )
    model.demand_constraint = pyo.Constraint(
        model.months,
        rule=lambda mdl, t: (
            sum(mdl.production[f, t] for f in mdl.factories)
            >= mdl.monthly_demand[t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[f] * model.run[f, t]
            + model.unit_cost[f] * model.production[f, t]
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