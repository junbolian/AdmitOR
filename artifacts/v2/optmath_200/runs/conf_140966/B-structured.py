# IR: {"sets":{"F":[0,1,2,3,4],"T":[0,1,2,3,4]},"params":{"fixed_cost":"F -> real","variable_cost":"F -> real","min_production":"F -> real","max_production":"F -> real","demand":"T -> real"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for all f,t","production[f,t] <= max_production[f]*run[f,t] for all f,t","sum_f production[f,t] >= demand[t] for all t"],"objective":"minimize sum_{f,t}(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 4)
    model.T = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={f: params["fixed_cost"][f] for f in model.F},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.F,
        initialize={f: params["variable_cost"][f] for f in model.F},
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

    def minimum_production_rule(mod, f, t):
        return (
            mod.production[f, t]
            >= mod.min_production[f] * mod.run[f, t]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.F, model.T, rule=minimum_production_rule
    )

    def maximum_production_rule(mod, f, t):
        return (
            mod.production[f, t]
            <= mod.max_production[f] * mod.run[f, t]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.F, model.T, rule=maximum_production_rule
    )

    def demand_rule(mod, t):
        return sum(mod.production[f, t] for f in mod.F) >= mod.demand[t]

    model.demand_constraint = pyo.Constraint(model.T, rule=demand_rule)

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