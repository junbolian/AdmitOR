# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3]},"params":{"activation_cost":"F-indexed","production_cost":"F-indexed","min_production":"F-indexed","max_production":"F-indexed","demand":"T-indexed"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(activation_cost[f]*run[f,t] + production_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 3)

    model.activation_cost = pyo.Param(
        model.F,
        initialize={f: params["activation_cost"][f] for f in model.F},
    )
    model.production_cost = pyo.Param(
        model.F,
        initialize={f: params["production_cost"][f] for f in model.F},
    )
    model.min_production = pyo.Param(
        model.F,
        initialize={f: params["min_production"][f] for f in model.F},
    )
    model.max_production = pyo.Param(
        model.F,
        initialize={f: params["max_production"][f] for f in model.F},
    )
    model.demand = pyo.Param(
        model.T,
        initialize={t: params["demand"][t] for t in model.T},
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(model, f, t):
        return (
            model.production[f, t]
            >= model.min_production[f] * model.run[f, t]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.F, model.T, rule=minimum_production_rule
    )

    def maximum_production_rule(model, f, t):
        return (
            model.production[f, t]
            <= model.max_production[f] * model.run[f, t]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.F, model.T, rule=maximum_production_rule
    )

    def demand_rule(model, t):
        return (
            sum(model.production[f, t] for f in model.F)
            >= model.demand[t]
        )

    model.demand_constraint = pyo.Constraint(model.T, rule=demand_rule)

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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}