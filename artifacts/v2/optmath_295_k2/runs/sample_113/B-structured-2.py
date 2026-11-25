# IR: {"sets":{"I":"0..46"},"params":{"profit":"params['profit'][i], i in I","resource_usage":"params['resource_usage'][i], i in I","capacity":"params['capacity'][i], i in I","resource_budget":"params['resource_budget']"},"variables":{"quantity[i]":"NonNegativeReals, i in I"},"constraints":["sum(resource_usage[i]*quantity[i] for i in I) <= resource_budget","quantity[i] <= capacity[i] for i in I"],"objective":"maximize sum(profit[i]*quantity[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.items_set = pyo.RangeSet(0, 46)

    model.profit = pyo.Param(
        model.items_set,
        initialize={i: params["profit"][i] for i in model.items_set},
        within=pyo.Reals,
    )
    model.resource_usage = pyo.Param(
        model.items_set,
        initialize={i: params["resource_usage"][i] for i in model.items_set},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.items_set,
        initialize={i: params["capacity"][i] for i in model.items_set},
        within=pyo.Reals,
    )
    model.resource_budget = pyo.Param(
        initialize=params["resource_budget"],
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.items_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_usage[i] * model.quantity[i]
            for i in model.items_set
        )
        <= model.resource_budget
    )

    def capacity_rule(instance, i):
        return instance.quantity[i] <= instance.capacity[i]

    model.capacity_constraints = pyo.Constraint(
        model.items_set,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.quantity[i]
            for i in model.items_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}