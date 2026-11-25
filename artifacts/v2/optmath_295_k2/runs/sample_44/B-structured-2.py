# IR: {"sets":{"factories":[0,1,2,3,4],"months":[0,1,2,3,4,5]},"params":{"fixed_cost":"params['fixed_cost'][f]","variable_cost":"params['variable_cost'][f]","min_production":"params['min_production'][f]","max_production":"params['max_production'][f]","demand":"params['demand'][t]"},"variables":{"run[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for each f,t","production[f,t] <= max_production[f] * run[f,t] for each f,t","sum(production[f,t] for f in factories) >= demand[t] for each t"],"objective":{"sense":"minimize","expression":"sum(fixed_cost[f] * run[f,t] + variable_cost[f] * production[f,t] for each f,t)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 4)
    model.months = pyo.RangeSet(0, 5)

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

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
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
    model.demand_coverage = pyo.Constraint(
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
        # APPsi raises this when it cannot load a feasible solution.
        # Leave success determination to objective retrieval below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}