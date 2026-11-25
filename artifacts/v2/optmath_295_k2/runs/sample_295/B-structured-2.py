# IR: {"sets":{"F":[0,1,2,3,4,5],"T":[0,1,2,3,4,5]},"params":{"min_production":"F-indexed","max_production":"F-indexed","demand":"T-indexed","fixed_cost":"F-indexed","variable_cost":"F-indexed"},"variables":{"run[f,t]":"binary","production[f,t]":"nonnegative continuous"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for all f,t","production[f,t] <= max_production[f] * run[f,t] for all f,t","sum_f production[f,t] >= demand[t] for all t"],"objective":"minimize sum_f,t (fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()
    model.factories = pyo.RangeSet(0, 5)
    model.months = pyo.RangeSet(0, 5)

    model.minimum_output = pyo.Param(
        model.factories,
        initialize={f: min_production[f] for f in model.factories},
    )
    model.capacity = pyo.Param(
        model.factories,
        initialize={f: max_production[f] for f in model.factories},
    )
    model.monthly_demand = pyo.Param(
        model.months,
        initialize={t: demand[t] for t in model.months},
    )
    model.operating_cost = pyo.Param(
        model.factories,
        initialize={f: fixed_cost[f] for f in model.factories},
    )
    model.unit_cost = pyo.Param(
        model.factories,
        initialize={f: variable_cost[f] for f in model.factories},
    )

    model.run = pyo.Var(model.factories, model.months, domain=pyo.Binary)
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_rule(mod, f, t):
        return mod.production[f, t] >= mod.minimum_output[f] * mod.run[f, t]

    def capacity_rule(mod, f, t):
        return mod.production[f, t] <= mod.capacity[f] * mod.run[f, t]

    def demand_rule(mod, t):
        return (
            sum(mod.production[f, t] for f in mod.factories)
            >= mod.monthly_demand[t]
        )

    model.minimum_constraints = pyo.Constraint(
        model.factories, model.months, rule=minimum_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.factories, model.months, rule=capacity_rule
    )
    model.demand_constraints = pyo.Constraint(model.months, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[f] * model.run[f, t]
            + model.unit_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}