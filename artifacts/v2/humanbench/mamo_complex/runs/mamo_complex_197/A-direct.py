import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    mango_per_A = params["mango_per_A"]
    pineapple_per_A = params["pineapple_per_A"]
    strawberry_per_A = params["strawberry_per_A"]
    profit_A = params["profit_A"]
    mango_per_B = params["mango_per_B"]
    pineapple_per_B = params["pineapple_per_B"]
    strawberry_per_B = params["strawberry_per_B"]
    profit_B = params["profit_B"]
    mango_stock = params["mango_stock"]
    pineapple_stock = params["pineapple_stock"]
    strawberry_stock = params["strawberry_stock"]
    tol = params["completeness_tolerance"]

    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.profit = pyo.Objective(
        expr=profit_A * model.xA + profit_B * model.xB, sense=pyo.maximize
    )

    model.mango_usage = pyo.Constraint(
        expr=pyo.inequality(
            mango_stock - tol,
            mango_per_A * model.xA + mango_per_B * model.xB,
            mango_stock + tol,
        )
    )
    model.pineapple_usage = pyo.Constraint(
        expr=pyo.inequality(
            pineapple_stock - tol,
            pineapple_per_A * model.xA + pineapple_per_B * model.xB,
            pineapple_stock + tol,
        )
    )
    model.strawberry_usage = pyo.Constraint(
        expr=pyo.inequality(
            strawberry_stock - tol,
            strawberry_per_A * model.xA + strawberry_per_B * model.xB,
            strawberry_stock + tol,
        )
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}