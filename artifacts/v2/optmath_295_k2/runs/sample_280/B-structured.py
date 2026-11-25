# IR: {"sets":{"factories":[0,1,2,3],"months":[0,1,2,3]},"params":{"activation_cost":"indexed by factory","production_cost":"indexed by factory","min_production":"indexed by factory","max_production":"indexed by factory","demand":"indexed by month"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f]*run[f,t] for every factory and month","production[f,t] <= max_production[f]*run[f,t] for every factory and month","sum_f production[f,t] >= demand[t] for every month"],"objective":"minimize sum_f,t (activation_cost[f]*run[f,t] + production_cost[f]*production[f,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 3)
    model.months = pyo.RangeSet(0, 3)

    model.activation_cost = pyo.Param(
        model.factories,
        initialize={f: params["activation_cost"][f] for f in model.factories},
    )
    model.production_cost = pyo.Param(
        model.factories,
        initialize={f: params["production_cost"][f] for f in model.factories},
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={f: params["min_production"][f] for f in model.factories},
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: params["max_production"][f] for f in model.factories},
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
    )

    model.run = pyo.Var(model.factories, model.months, domain=pyo.Binary)
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_rule(model, f, t):
        return (
            model.production[f, t]
            >= model.min_production[f] * model.run[f, t]
        )

    def maximum_rule(model, f, t):
        return (
            model.production[f, t]
            <= model.max_production[f] * model.run[f, t]
        )

    def demand_rule(model, t):
        return (
            sum(model.production[f, t] for f in model.factories)
            >= model.demand[t]
        )

    model.minimum_output = pyo.Constraint(
        model.factories, model.months, rule=minimum_rule
    )
    model.maximum_output = pyo.Constraint(
        model.factories, model.months, rule=maximum_rule
    )
    model.demand_satisfaction = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[f] * model.run[f, t]
            + model.production_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}