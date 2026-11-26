# IR: {"sets":{},"params":["a_proc1_hours","a_proc2_hours","b_proc1_hours","b_proc2_hours","proc1_capacity","proc2_capacity","byproduct_per_b","c_sales_limit","c_disposal_cost","a_profit","b_profit","c_sell_profit"],"variables":{"a":"NonNegativeReals","b":"NonNegativeReals","c_sold":"NonNegativeReals","c_disposed":"NonNegativeReals"},"constraints":["a_proc1_hours*a + b_proc1_hours*b <= proc1_capacity","a_proc2_hours*a + b_proc2_hours*b <= proc2_capacity","c_sold + c_disposed == byproduct_per_b*b","c_sold <= c_sales_limit"],"objective":{"sense":"maximize","expression":"a_profit*a + b_profit*b + c_sell_profit*c_sold - c_disposal_cost*c_disposed"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coefficients = {
        "a_proc1_hours": params["a_proc1_hours"],
        "a_proc2_hours": params["a_proc2_hours"],
        "b_proc1_hours": params["b_proc1_hours"],
        "b_proc2_hours": params["b_proc2_hours"],
        "proc1_capacity": params["proc1_capacity"],
        "proc2_capacity": params["proc2_capacity"],
        "byproduct_per_b": params["byproduct_per_b"],
        "c_sales_limit": params["c_sales_limit"],
        "c_disposal_cost": params["c_disposal_cost"],
        "a_profit": params["a_profit"],
        "b_profit": params["b_profit"],
        "c_sell_profit": params["c_sell_profit"],
    }

    model = pyo.ConcreteModel()
    model.coefficients = pyo.Param(
        tuple(coefficients),
        initialize=coefficients,
        within=pyo.Reals,
    )

    model.a = pyo.Var(domain=pyo.NonNegativeReals)
    model.b = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_sold = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_disposed = pyo.Var(domain=pyo.NonNegativeReals)

    model.process_one_capacity = pyo.Constraint(
        expr=(
            model.coefficients["a_proc1_hours"] * model.a
            + model.coefficients["b_proc1_hours"] * model.b
            <= model.coefficients["proc1_capacity"]
        )
    )

    model.process_two_capacity = pyo.Constraint(
        expr=(
            model.coefficients["a_proc2_hours"] * model.a
            + model.coefficients["b_proc2_hours"] * model.b
            <= model.coefficients["proc2_capacity"]
        )
    )

    model.byproduct_balance = pyo.Constraint(
        expr=(
            model.c_sold + model.c_disposed
            == model.coefficients["byproduct_per_b"] * model.b
        )
    )

    model.byproduct_sales_limit = pyo.Constraint(
        expr=model.c_sold <= model.coefficients["c_sales_limit"]
    )

    model.total_profit = pyo.Objective(
        expr=(
            model.coefficients["a_profit"] * model.a
            + model.coefficients["b_profit"] * model.b
            + model.coefficients["c_sell_profit"] * model.c_sold
            - model.coefficients["c_disposal_cost"] * model.c_disposed
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}