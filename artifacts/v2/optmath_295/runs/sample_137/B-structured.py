# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"products","stage_time_available":"stages","time_per_unit":"stages x products","lower_bound":"products","upper_bound":"products"},"variables":{"production":{"index":"products","type":"nonnegative continuous"}},"constraints":["production[j] >= lower_bound[j] for each product j","production[j] <= upper_bound[j] for each product j","sum(time_per_unit[s,j] * production[j] for j in products) <= stage_time_available[s] for each stage s"],"objective":{"sense":"maximize","expression":"sum(profit[j] * production[j] for j in products)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize=lambda mdl, j: params["profit"][j],
    )
    model.stage_time_available = pyo.Param(
        model.stages,
        initialize=lambda mdl, s: params["stage_time_available"][s],
    )
    model.time_per_unit = pyo.Param(
        model.stages,
        model.products,
        initialize=lambda mdl, s, j: params["time_per_unit"][s][j],
    )
    model.lower_bound = pyo.Param(
        model.products,
        initialize=lambda mdl, j: params["lower_bound"][j],
    )
    model.upper_bound = pyo.Param(
        model.products,
        initialize=lambda mdl, j: params["upper_bound"][j],
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    model.minimum_production = pyo.Constraint(
        model.products,
        rule=lambda mdl, j: mdl.production[j] >= mdl.lower_bound[j],
    )
    model.maximum_production = pyo.Constraint(
        model.products,
        rule=lambda mdl, j: mdl.production[j] <= mdl.upper_bound[j],
    )
    model.stage_capacity = pyo.Constraint(
        model.stages,
        rule=lambda mdl, s: sum(
            mdl.time_per_unit[s, j] * mdl.production[j]
            for j in mdl.products
        ) <= mdl.stage_time_available[s],
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[j] * model.production[j]
            for j in model.products
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