# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3]},"params":{"activation_cost":"F -> real","production_cost":"F -> real","min_production":"F -> real","max_production":"F -> real","demand":"T -> real"},"variables":{"run[F,T]":"binary","production[F,T]":"nonnegative real"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(activation_cost[f]*run[f,t] + production_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 3)

    model.activation_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["activation_cost"][factory],
        within=pyo.Reals,
    )
    model.production_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["production_cost"][factory],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["min_production"][factory],
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["max_production"][factory],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=lambda mdl, month: params["demand"][month],
        within=pyo.Reals,
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.run[factory, month]
        ),
    )

    model.maximum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.run[factory, month]
        ),
    )

    model.demand_satisfaction = pyo.Constraint(
        model.T,
        rule=lambda mdl, month: (
            sum(mdl.production[factory, month] for factory in mdl.F)
            >= mdl.demand[month]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[factory] * model.run[factory, month]
            + model.production_cost[factory] * model.production[factory, month]
            for factory in model.F
            for month in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}