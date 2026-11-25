# IR: {"sets":{"F":[0,1,2,3,4,5],"T":[0,1,2,3,4]},"params":{"fixed_cost":"real[F]","variable_cost":"real[F]","min_production":"real[F]","max_production":"real[F]","demand":"real[T]"},"variables":{"run":"binary[F,T]","production":"nonnegative_real[F,T]"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F,t in T","production[f,t] <= max_production[f]*run[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 5)
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

    def minimum_output_rule(model, f, t):
        return (
            model.production[f, t]
            >= model.min_production[f] * model.run[f, t]
        )

    def maximum_output_rule(model, f, t):
        return (
            model.production[f, t]
            <= model.max_production[f] * model.run[f, t]
        )

    def demand_requirement_rule(model, t):
        return (
            sum(model.production[f, t] for f in model.F)
            >= model.demand[t]
        )

    model.minimum_output = pyo.Constraint(
        model.F, model.T, rule=minimum_output_rule
    )
    model.maximum_output = pyo.Constraint(
        model.F, model.T, rule=maximum_output_rule
    )
    model.demand_requirement = pyo.Constraint(
        model.T, rule=demand_requirement_rule
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