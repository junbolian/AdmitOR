# {
#   "sets": {"I": "0,...,42"},
#   "params": {"profit": "real[I]", "resource_coeff": "real[I]", "resource_limit": "real", "capacity": "real[I]"},
#   "variables": {"production": "nonnegative continuous[I]"},
#   "constraints": [
#     "sum(resource_coeff[i] * production[i] for i in I) <= resource_limit",
#     "production[i] <= capacity[i] for each i in I"
#   ],
#   "objective": "maximize sum(profit[i] * production[i] for i in I)"
# }

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 42)

    model.profit = pyo.Param(
        model.I,
        initialize={i: params["profit"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.resource_coeff = pyo.Param(
        model.I,
        initialize={i: params["resource_coeff"][i] for i in model.I},
        within=pyo.Reals,
    )
    model.resource_limit = pyo.Param(
        initialize=params["resource_limit"],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        initialize={i: params["capacity"][i] for i in model.I},
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.I,
        domain=pyo.NonNegativeReals,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.resource_coeff[i] * model.production[i]
            for i in model.I
        ) <= model.resource_limit
    )

    def capacity_rule(instance, i):
        return instance.production[i] <= instance.capacity[i]

    model.capacity_constraints = pyo.Constraint(
        model.I,
        rule=capacity_rule,
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}