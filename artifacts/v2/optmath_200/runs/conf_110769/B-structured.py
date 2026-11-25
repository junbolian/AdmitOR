# IR: {"sets":{"T":[0,1,2,3],"F":[0,1,2,3]},"params":{"fixed_cost":"F -> nonnegative real","var_cost":"F -> nonnegative real","min_prod":"F -> nonnegative real","max_capacity":"F -> nonnegative real","demand":"T -> nonnegative real"},"variables":{"running[t,f]":"binary","production[t,f]":"nonnegative real"},"constraints":["production[t,f] >= min_prod[f] * running[t,f] for all t,f","production[t,f] <= max_capacity[f] * running[t,f] for all t,f","sum(production[t,f] for f in F) >= demand[t] for all t"],"objective":"minimize sum(fixed_cost[f]*running[t,f] + var_cost[f]*production[t,f] for all t,f)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(0, 3)
    model.F = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={factory: params["fixed_cost"][factory] for factory in model.F},
        within=pyo.NonNegativeReals,
    )
    model.var_cost = pyo.Param(
        model.F,
        initialize={factory: params["var_cost"][factory] for factory in model.F},
        within=pyo.NonNegativeReals,
    )
    model.min_prod = pyo.Param(
        model.F,
        initialize={factory: params["min_prod"][factory] for factory in model.F},
        within=pyo.NonNegativeReals,
    )
    model.max_capacity = pyo.Param(
        model.F,
        initialize={
            factory: params["max_capacity"][factory] for factory in model.F
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize={month: params["demand"][month] for month in model.T},
        within=pyo.NonNegativeReals,
    )

    model.running = pyo.Var(model.T, model.F, domain=pyo.Binary)
    model.production = pyo.Var(model.T, model.F, domain=pyo.NonNegativeReals)

    def minimum_production_rule(instance, month, factory):
        return (
            instance.production[month, factory]
            >= instance.min_prod[factory] * instance.running[month, factory]
        )

    model.minimum_production = pyo.Constraint(
        model.T, model.F, rule=minimum_production_rule
    )

    def maximum_production_rule(instance, month, factory):
        return (
            instance.production[month, factory]
            <= instance.max_capacity[factory] * instance.running[month, factory]
        )

    model.maximum_production = pyo.Constraint(
        model.T, model.F, rule=maximum_production_rule
    )

    def demand_satisfaction_rule(instance, month):
        return (
            sum(instance.production[month, factory] for factory in instance.F)
            >= instance.demand[month]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.T, rule=demand_satisfaction_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[factory] * model.running[month, factory]
            + model.var_cost[factory] * model.production[month, factory]
            for month in model.T
            for factory in model.F
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated errors; determine success by objective retrieval.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}