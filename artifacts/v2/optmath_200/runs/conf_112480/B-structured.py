# IR: {"sets":{"factories":[0,1,2,3],"months":[0,1,2,3]},"params":{"fixed_cost":"factory-indexed","variable_cost":"factory-indexed","min_production":"factory-indexed","max_production":"factory-indexed","demand":"month-indexed"},"variables":{"run[month,factory]":"binary","production[month,factory]":"nonnegative continuous"},"constraints":["production[t,f] >= min_production[f]*run[t,f] for all t,f","production[t,f] <= max_production[f]*run[t,f] for all t,f","sum_f production[t,f] >= demand[t] for all t"],"objective":"minimize sum_t,f (fixed_cost[f]*run[t,f] + variable_cost[f]*production[t,f])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 3)
    model.months = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: params["fixed_cost"][f] for f in model.factories},
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={f: params["variable_cost"][f] for f in model.factories},
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

    model.run = pyo.Var(model.months, model.factories, domain=pyo.Binary)
    model.production = pyo.Var(
        model.months, model.factories, domain=pyo.NonNegativeReals
    )

    def minimum_rule(md, t, f):
        return md.production[t, f] >= md.min_production[f] * md.run[t, f]

    def maximum_rule(md, t, f):
        return md.production[t, f] <= md.max_production[f] * md.run[t, f]

    def demand_rule(md, t):
        return sum(md.production[t, f] for f in md.factories) >= md.demand[t]

    model.minimum_constraints = pyo.Constraint(
        model.months, model.factories, rule=minimum_rule
    )
    model.maximum_constraints = pyo.Constraint(
        model.months, model.factories, rule=maximum_rule
    )
    model.demand_constraints = pyo.Constraint(model.months, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[t, f]
            + model.variable_cost[f] * model.production[t, f]
            for t in model.months
            for f in model.factories
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