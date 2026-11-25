# {"sets":{"F":[0,1,2],"T":[0,1,2,3]},"params":{"fixed_cost":"F-indexed","variable_cost":"F-indexed","min_production":"F-indexed","max_production":"F-indexed","monthly_demand":"T-indexed"},"variables":{"run[F,T]":"binary","production[F,T]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= monthly_demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=range(3), ordered=True)
    model.T = pyo.Set(initialize=range(4), ordered=True)

    model.fixed_cost = pyo.Param(
        model.F, initialize=lambda mdl, f: params["fixed_cost"][f]
    )
    model.variable_cost = pyo.Param(
        model.F, initialize=lambda mdl, f: params["variable_cost"][f]
    )
    model.min_production = pyo.Param(
        model.F, initialize=lambda mdl, f: params["min_production"][f]
    )
    model.max_production = pyo.Param(
        model.F, initialize=lambda mdl, f: params["max_production"][f]
    )
    model.monthly_demand = pyo.Param(
        model.T, initialize=lambda mdl, t: params["monthly_demand"][t]
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] >= mdl.min_production[f] * mdl.run[f, t]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t] <= mdl.max_production[f] * mdl.run[f, t]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            sum(mdl.production[f, t] for f in mdl.F)
            >= mdl.monthly_demand[t]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[f, t]
            + model.variable_cost[f] * model.production[f, t]
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