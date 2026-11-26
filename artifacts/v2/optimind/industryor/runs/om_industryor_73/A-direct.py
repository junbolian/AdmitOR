import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)  # units of A produced
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)  # units of B produced
    model.xC_sold = pyo.Var(domain=pyo.NonNegativeReals)   # units of C sold
    model.xC_disposed = pyo.Var(domain=pyo.NonNegativeReals)  # units of C disposed

    # Process capacity constraints
    model.proc1 = pyo.Constraint(
        expr=params["a_proc1_hours"] * model.xA
        + params["b_proc1_hours"] * model.xB
        <= params["proc1_capacity"]
    )
    model.proc2 = pyo.Constraint(
        expr=params["a_proc2_hours"] * model.xA
        + params["b_proc2_hours"] * model.xB
        <= params["proc2_capacity"]
    )

    # By-product balance: C generated = C sold + C disposed
    model.c_balance = pyo.Constraint(
        expr=model.xC_sold + model.xC_disposed
        == params["byproduct_per_b"] * model.xB
    )

    # Sales limit for C
    model.c_limit = pyo.Constraint(
        expr=model.xC_sold <= params["c_sales_limit"]
    )

    # Objective: maximize total profit
    model.obj = pyo.Objective(
        expr=params["a_profit"] * model.xA
        + params["b_profit"] * model.xB
        + params["c_sell_profit"] * model.xC_sold
        - params["c_disposal_cost"] * model.xC_disposed,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}