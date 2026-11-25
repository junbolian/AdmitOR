# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3,4]},"params":{"fixed_cost":"F -> real","variable_cost":"F -> real","min_production":"F -> nonnegative real","max_production":"F -> nonnegative real","demand":"T -> nonnegative real"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for f in F, t in T","production[f,t] <= max_production[f]*run[f,t] for f in F, t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.Set(initialize=range(4), ordered=True)
    model.months = pyo.Set(initialize=range(5), ordered=True)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: params["fixed_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={f: params["variable_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={f: params["min_production"][f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: params["max_production"][f] for f in model.factories},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
        within=pyo.NonNegativeReals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(instance, f, t):
        return (
            instance.production[f, t]
            >= instance.min_production[f] * instance.run[f, t]
        )

    def maximum_production_rule(instance, f, t):
        return (
            instance.production[f, t]
            <= instance.max_production[f] * instance.run[f, t]
        )

    def demand_rule(instance, t):
        return (
            sum(instance.production[f, t] for f in instance.factories)
            >= instance.demand[t]
        )

    model.minimum_output = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )
    model.maximum_output = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )
    model.demand_satisfaction = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}