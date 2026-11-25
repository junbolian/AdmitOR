# IR: {"sets":{"I":"0..24"},"params":{"profit":"params['profit'][i] for i in I","resource_coeff":"params['resource_coeff'][i] for i in I","resource_capacity":"params['resource_capacity']","upper_limit":"params['upper_limit'][i] for i in I"},"variables":{"production[i]":"nonnegative continuous for i in I"},"constraints":["sum(resource_coeff[i]*production[i] for i in I) <= resource_capacity","production[i] <= upper_limit[i] for each i in I"],"objective":"maximize sum(profit[i]*production[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 24)

    model.profit = pyo.Param(
        model.I,
        initialize={i: params["profit"][i] for i in model.I},
    )
    model.resource_coeff = pyo.Param(
        model.I,
        initialize={i: params["resource_coeff"][i] for i in model.I},
    )
    model.resource_capacity = pyo.Param(
        initialize=params["resource_capacity"],
    )
    model.upper_limit = pyo.Param(
        model.I,
        initialize={i: params["upper_limit"][i] for i in model.I},
    )

    model.production = pyo.Var(model.I, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_coeff[i] * model.production[i]
            for i in model.I
        ) <= model.resource_capacity
    )

    def production_limit_rule(instance, i):
        return instance.production[i] <= instance.upper_limit[i]

    model.production_limits = pyo.Constraint(
        model.I, rule=production_limit_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.production[i]
            for i in model.I
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}