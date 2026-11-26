# IR: {"sets":{},"params":["a_front_hours","b_front_hours","a_back_hours","b_back_hours","front_capacity","back_capacity","c_per_b","c_sellable_max","c_disposal_cost","profit_a","profit_b","profit_c"],"variables":{"a_units":"continuous >= 0","b_units":"continuous >= 0","c_sold":"continuous >= 0","c_disposed":"continuous >= 0"},"constraints":["a_front_hours*a_units + b_front_hours*b_units <= front_capacity","a_back_hours*a_units + b_back_hours*b_units <= back_capacity","c_sold + c_disposed == c_per_b*b_units","c_sold <= c_sellable_max"],"objective":{"sense":"maximize","expression":"profit_a*a_units + profit_b*b_units + profit_c*c_sold - c_disposal_cost*c_disposed"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coefficients = {
        "a_front_hours": params["a_front_hours"],
        "b_front_hours": params["b_front_hours"],
        "a_back_hours": params["a_back_hours"],
        "b_back_hours": params["b_back_hours"],
        "front_capacity": params["front_capacity"],
        "back_capacity": params["back_capacity"],
        "c_per_b": params["c_per_b"],
        "c_sellable_max": params["c_sellable_max"],
        "c_disposal_cost": params["c_disposal_cost"],
        "profit_a": params["profit_a"],
        "profit_b": params["profit_b"],
        "profit_c": params["profit_c"],
    }

    model = pyo.ConcreteModel()
    model.coefficients = pyo.Param(
        tuple(coefficients),
        initialize=coefficients,
        within=pyo.Reals,
    )

    model.a_units = pyo.Var(domain=pyo.NonNegativeReals)
    model.b_units = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_disposed = pyo.Var(domain=pyo.NonNegativeReals)

    model.front_limit = pyo.Constraint(
        expr=(
            model.coefficients["a_front_hours"] * model.a_units
            + model.coefficients["b_front_hours"] * model.b_units
            <= model.coefficients["front_capacity"]
        )
    )

    model.back_limit = pyo.Constraint(
        expr=(
            model.coefficients["a_back_hours"] * model.a_units
            + model.coefficients["b_back_hours"] * model.b_units
            <= model.coefficients["back_capacity"]
        )
    )

    model.byproduct_balance = pyo.Constraint(
        expr=(
            model.c_sold + model.c_disposed
            == model.coefficients["c_per_b"] * model.b_units
        )
    )

    model.byproduct_sales_limit = pyo.Constraint(
        expr=model.c_sold <= model.coefficients["c_sellable_max"]
    )

    model.total_profit = pyo.Objective(
        expr=(
            model.coefficients["profit_a"] * model.a_units
            + model.coefficients["profit_b"] * model.b_units
            + model.coefficients["profit_c"] * model.c_sold
            - model.coefficients["c_disposal_cost"] * model.c_disposed
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