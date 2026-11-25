# IR: {"sets":{"products":"0..10"},"params":{"profit_per_unit":"indexed by products","time_per_unit":"indexed by products","time_capacity":"scalar","min_production":"indexed by products","max_production":"indexed by products"},"variables":{"quantity":{"index":"products","type":"nonnegative continuous"}},"constraints":["sum(time_per_unit[i]*quantity[i] for i in products) <= time_capacity","quantity[i] >= min_production[i] for each i in products","quantity[i] <= max_production[i] for each i in products"],"objective":{"sense":"maximize","expression":"sum(profit_per_unit[i]*quantity[i] for i in products)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the production LP; indexed inputs use product indices 0 through 10."""
    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 10)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={i: params["profit_per_unit"][i] for i in model.products},
    )
    model.time_per_unit = pyo.Param(
        model.products,
        initialize={i: params["time_per_unit"][i] for i in model.products},
    )
    model.time_capacity = pyo.Param(initialize=params["time_capacity"])
    model.min_production = pyo.Param(
        model.products,
        initialize={i: params["min_production"][i] for i in model.products},
    )
    model.max_production = pyo.Param(
        model.products,
        initialize={i: params["max_production"][i] for i in model.products},
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    model.time_limit = pyo.Constraint(
        expr=sum(
            model.time_per_unit[i] * model.quantity[i]
            for i in model.products
        )
        <= model.time_capacity
    )
    model.production_minimum = pyo.Constraint(
        model.products,
        rule=lambda model, i: model.quantity[i] >= model.min_production[i],
    )
    model.production_maximum = pyo.Constraint(
        model.products,
        rule=lambda model, i: model.quantity[i] <= model.max_production[i],
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[i] * model.quantity[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    # Success depends solely on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        reason = "solver_failed" if solve_failed else "no_objective_value"
        return {"objective": None, "status": reason}

    return {"objective": obj_val, "status": "optimal"}