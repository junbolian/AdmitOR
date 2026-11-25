# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3]},"params":{"activation_cost":"F","production_cost":"F","min_production":"F","max_production":"F","demand":"T"},"variables":{"factory_on[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*factory_on[f,t] for f in F,t in T","production[f,t] <= max_production[f]*factory_on[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(activation_cost[f]*factory_on[f,t] + production_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 3)

    model.activation_cost = pyo.Param(
        model.F, initialize=lambda mdl, f: params["activation_cost"][f]
    )
    model.production_cost = pyo.Param(
        model.F, initialize=lambda mdl, f: params["production_cost"][f]
    )
    model.min_production = pyo.Param(
        model.F, initialize=lambda mdl, f: params["min_production"][f]
    )
    model.max_production = pyo.Param(
        model.F, initialize=lambda mdl, f: params["max_production"][f]
    )
    model.demand = pyo.Param(
        model.T, initialize=lambda mdl, t: params["demand"][t]
    )

    model.factory_on = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t]
            >= mdl.min_production[f] * mdl.factory_on[f, t]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t]
            <= mdl.max_production[f] * mdl.factory_on[f, t]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.production[f, t] for f in mdl.F) >= mdl.demand[t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[f] * model.factory_on[f, t]
            + model.production_cost[f] * model.production[f, t]
            for f in model.F
            for t in model.T
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