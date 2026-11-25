# IR: {"sets":{"F":[0,1,2,3,4,5],"T":[0,1,2,3]},"params":{"fixed_cost[f,t]":"params[fixed_cost_f{f}_month{t}]","variable_cost[f]":"params[var_cost_f{f}]","minimum_output[f]":"params[min_prod_f{f}]","maximum_output[f]":"params[max_prod_f{f}]","demand[t]":"params[demand_month{t}]"},"variables":{"running[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= minimum_output[f]*running[f,t] for f in F,t in T","production[f,t] <= maximum_output[f]*running[f,t] for f in F,t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f,t]*running[f,t] + variable_cost[f]*production[f,t] for f in F,t in T)"}

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
    model.variable_cost = pyo.Param(
        model.F,
        initialize={
            factory: params[f"var_cost_f{factory}"]
            for factory in model.F
        },
        within=pyo.Reals,
    )
    model.minimum_output = pyo.Param(
        model.F,
        initialize={
            factory: params[f"min_prod_f{factory}"]
            for factory in model.F
        },
        within=pyo.Reals,
    )
    model.maximum_output = pyo.Param(
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

    def minimum_production_rule(mod, factory, month):
        return (
            mod.production[factory, month]
            >= mod.minimum_output[factory] * mod.running[factory, month]
        )

    model.minimum_production = pyo.Constraint(
        model.F, model.T, rule=minimum_production_rule
    )

    def maximum_production_rule(mod, factory, month):
        return (
            mod.production[factory, month]
            <= mod.maximum_output[factory] * mod.running[factory, month]
        )

    model.maximum_production = pyo.Constraint(
        model.F, model.T, rule=maximum_production_rule
    )

    def demand_satisfaction_rule(mod, month):
        return (
            sum(mod.production[factory, month] for factory in mod.F)
            >= mod.demand[month]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.T, rule=demand_satisfaction_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory, month] * model.running[factory, month]
            + model.variable_cost[factory] * model.production[factory, month]
            for factory in model.F
            for month in model.T
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}