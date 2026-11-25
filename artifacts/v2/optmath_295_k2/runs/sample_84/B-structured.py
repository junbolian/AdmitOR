# IR: {
#   "sets": {"products": "0..9"},
#   "params": {"profit": "real[products]", "time_per_unit": "real[products]", "total_time": "real", "min_production": "real[products]", "max_production": "real[products]"},
#   "variables": {"production": "nonnegative continuous[products]"},
#   "constraints": [
#     "sum(time_per_unit[i] * production[i] for i in products) <= total_time",
#     "production[i] >= min_production[i] for each i in products",
#     "production[i] <= max_production[i] for each i in products"
#   ],
#   "objective": "maximize sum(profit[i] * production[i] for i in products)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 9)

    model.profit = pyo.Param(
        model.products,
        initialize={i: params["profit"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.total_time = pyo.Param(
        initialize=params["total_time"],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={i: params["min_production"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.products,
        initialize={i: params["max_production"][i] for i in model.products},
        within=pyo.Reals,
    )

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    model.time_limit = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.production[i]
            for i in model.products
        ) <= model.total_time
    )

    def minimum_rule(instance, i):
        return instance.production[i] >= instance.min_production[i]

    def maximum_rule(instance, i):
        return instance.production[i] <= instance.max_production[i]

    model.minimum_requirement = pyo.Constraint(
        model.products, rule=minimum_rule
    )
    model.maximum_requirement = pyo.Constraint(
        model.products, rule=maximum_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.production[i]
            for i in model.products
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