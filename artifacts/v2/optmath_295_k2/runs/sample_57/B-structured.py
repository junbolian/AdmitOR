# IR: {"sets":{"I":"0..43"},"params":{"profit":"real[I], params['profit']","resource_rate":"real[I], params['resource_rate']","resource_capacity":"real, params['resource_capacity']","production_limit":"real[I], params['production_limit']"},"variables":{"quantity":"nonnegative continuous[I]"},"constraints":["sum(resource_rate[i]*quantity[i] for i in I) <= resource_capacity","quantity[i] <= production_limit[i] for i in I"],"objective":"maximize sum(profit[i]*quantity[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, 43)

    model.profit = pyo.Param(
        model.item_set,
        initialize={i: params["profit"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_rate = pyo.Param(
        model.item_set,
        initialize={i: params["resource_rate"][i] for i in model.item_set},
        within=pyo.Reals,
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
        within=pyo.Reals,
    )
    model.production_limit = pyo.Param(
        model.item_set,
        initialize={i: params["production_limit"][i] for i in model.item_set},
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.item_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_rate[i] * model.quantity[i]
            for i in model.item_set
        ) <= model.resource_capacity
    )

    def production_limit_rule(mdl, i):
        return mdl.quantity[i] <= mdl.production_limit[i]

    model.production_constraints = pyo.Constraint(
        model.item_set,
        rule=production_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.item_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}