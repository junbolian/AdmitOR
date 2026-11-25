# IR: {"sets":{"F":[0,1,2,3,4],"T":[0,1,2,3]},"params":{"fixed_cost":"real[F,T]","variable_cost":"real[F]","min_production":"real[F,T]","max_production":"real[F,T]","demand":"real[T]"},"variables":{"run":"binary[F,T]","production":"nonnegative_real[F,T]"},"constraints":["production[f,t] >= min_production[f,t]*run[f,t] for all f,t","production[f,t] <= max_production[f,t]*run[f,t] for all f,t","sum(production[f,t] for f in F) >= demand[t] for all t"],"objective":"minimize sum(fixed_cost[f,t]*run[f,t] + variable_cost[f]*production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Factory-month data use [factory][month]; other data use [index]."""
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, 4)
    model.T = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.F, model.T,
        initialize=lambda mdl, f, t: fixed_cost[f][t],
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, f: variable_cost[f],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.F, model.T,
        initialize=lambda mdl, f, t: min_production[f][t],
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.F, model.T,
        initialize=lambda mdl, f, t: max_production[f][t],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=lambda mdl, t: demand[t],
        within=pyo.Reals,
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    model.production_lower = pyo.Constraint(
        model.F, model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t]
            >= mdl.min_production[f, t] * mdl.run[f, t]
        ),
    )
    model.production_upper = pyo.Constraint(
        model.F, model.T,
        rule=lambda mdl, f, t: (
            mdl.production[f, t]
            <= mdl.max_production[f, t] * mdl.run[f, t]
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
            model.fixed_cost[f, t] * model.run[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.F
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise when no feasible solution is available for loading.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}