import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    mango_per_A = params["mango_per_A"]
    pineapple_per_A = params["pineapple_per_A"]
    strawberry_per_A = params["strawberry_per_A"]
    mango_per_B = params["mango_per_B"]
    pineapple_per_B = params["pineapple_per_B"]
    strawberry_per_B = params["strawberry_per_B"]
    mango_stock = params["mango_stock"]
    pineapple_stock = params["pineapple_stock"]
    strawberry_stock = params["strawberry_stock"]
    slack_tolerance = params["slack_tolerance"]

    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Fruit usage balances: each fruit usage within +/- slack_tolerance of stock
    model.mango_lo = pyo.Constraint(
        expr=mango_per_A * model.xA + mango_per_B * model.xB >= mango_stock - slack_tolerance
    )
    model.mango_hi = pyo.Constraint(
        expr=mango_per_A * model.xA + mango_per_B * model.xB <= mango_stock + slack_tolerance
    )
    model.pineapple_lo = pyo.Constraint(
        expr=pineapple_per_A * model.xA + pineapple_per_B * model.xB >= pineapple_stock - slack_tolerance
    )
    model.pineapple_hi = pyo.Constraint(
        expr=pineapple_per_A * model.xA + pineapple_per_B * model.xB <= pineapple_stock + slack_tolerance
    )
    model.strawberry_lo = pyo.Constraint(
        expr=strawberry_per_A * model.xA + strawberry_per_B * model.xB >= strawberry_stock - slack_tolerance
    )
    model.strawberry_hi = pyo.Constraint(
        expr=strawberry_per_A * model.xA + strawberry_per_B * model.xB <= strawberry_stock + slack_tolerance
    )

    model.obj = pyo.Objective(
        expr=profit_A * model.xA + profit_B * model.xB, sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}