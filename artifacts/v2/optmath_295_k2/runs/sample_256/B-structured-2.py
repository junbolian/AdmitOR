# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3]},"params":{"activation_cost":"F -> real","production_cost":"F -> real","min_production":"F -> real","max_production":"F -> real","demand":"T -> real"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"min sum(activation_cost[f]*run[f,t] + production_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 3)

    model.activation_cost = pyo.Param(
        model.F,
        initialize={f: params["activation_cost"][f] for f in model.F},
        within=pyo.Reals,
    )
    model.production_cost = pyo.Param(
        model.F,
        initialize={f: params["production_cost"][f] for f in model.F},
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.F,
        initialize={f: params["min_production"][f] for f in model.F},
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.F,
        initialize={f: params["max_production"][f] for f in model.F},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize={t: params["demand"][t] for t in model.T},
        within=pyo.Reals,
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    def minimum_rule(mdl, f, t):
        return (
            mdl.production[f, t]
            >= mdl.min_production[f] * mdl.run[f, t]
        )

    def maximum_rule(mdl, f, t):
        return (
            mdl.production[f, t]
            <= mdl.max_production[f] * mdl.run[f, t]
        )

    def demand_rule(mdl, t):
        return sum(mdl.production[f, t] for f in mdl.F) >= mdl.demand[t]

    model.minimum_output = pyo.Constraint(
        model.F, model.T, rule=minimum_rule
    )
    model.maximum_output = pyo.Constraint(
        model.F, model.T, rule=maximum_rule
    )
    model.demand_requirement = pyo.Constraint(model.T, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[f] * model.run[f, t]
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