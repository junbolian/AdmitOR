# {"sets":{"F":[0,1,2,3,4,5],"T":[0,1,2,3]},"params":{"fixed_cost[f,t]":"params[fixed_cost_f{f}_month{t}]","var_cost[f]":"params[var_cost_f{f}]","min_prod[f]":"params[min_prod_f{f}]","max_prod[f]":"params[max_prod_f{f}]","demand[t]":"params[demand_month{t}]"},"variables":{"running[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_prod[f]*running[f,t] for f in F,t in T","production[f,t] <= max_prod[f]*running[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f,t]*running[f,t] + var_cost[f]*production[f,t] for f in F,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 5)
    model.T = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.F,
        model.T,
        initialize={
            (factory, month): params[f"fixed_cost_f{factory}_month{month}"]
            for factory in model.F
            for month in model.T
        },
        within=pyo.Reals,
    )
    model.var_cost = pyo.Param(
        model.F,
        initialize={
            factory: params[f"var_cost_f{factory}"]
            for factory in model.F
        },
        within=pyo.Reals,
    )
    model.min_prod = pyo.Param(
        model.F,
        initialize={
            factory: params[f"min_prod_f{factory}"]
            for factory in model.F
        },
        within=pyo.Reals,
    )
    model.max_prod = pyo.Param(
        model.F,
        initialize={
            factory: params[f"max_prod_f{factory}"]
            for factory in model.F
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize={
            month: params[f"demand_month{month}"]
            for month in model.T
        },
        within=pyo.Reals,
    )

    model.running = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            >= mdl.min_prod[factory] * mdl.running[factory, month]
        )

    model.minimum_production = pyo.Constraint(
        model.F, model.T, rule=minimum_production_rule
    )

    def maximum_production_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            <= mdl.max_prod[factory] * mdl.running[factory, month]
        )

    model.maximum_production = pyo.Constraint(
        model.F, model.T, rule=maximum_production_rule
    )

    def demand_rule(mdl, month):
        return (
            sum(mdl.production[factory, month] for factory in mdl.F)
            >= mdl.demand[month]
        )

    model.demand_satisfaction = pyo.Constraint(model.T, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory, month] * model.running[factory, month]
            + model.var_cost[factory] * model.production[factory, month]
            for factory in model.F
            for month in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}