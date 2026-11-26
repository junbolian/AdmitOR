# IR: {
#   "sets": [],
#   "params": ["profit_A", "profit_B", "mango_per_A", "pineapple_per_A", "strawberry_per_A", "mango_per_B", "pineapple_per_B", "strawberry_per_B", "mango_stock", "pineapple_stock", "strawberry_stock", "slack_tolerance"],
#   "variables": {"x1": "NonNegativeIntegers", "x2": "NonNegativeIntegers"},
#   "constraints": [
#     "mango_stock - slack_tolerance <= mango_per_A*x1 + mango_per_B*x2 <= mango_stock + slack_tolerance",
#     "pineapple_stock - slack_tolerance <= pineapple_per_A*x1 + pineapple_per_B*x2 <= pineapple_stock + slack_tolerance",
#     "strawberry_stock - slack_tolerance <= strawberry_per_A*x1 + strawberry_per_B*x2 <= strawberry_stock + slack_tolerance"
#   ],
#   "objective": "maximize profit_A*x1 + profit_B*x2"
# }

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

    model.x1 = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x2 = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.mango_usage = pyo.Constraint(
        expr=(
            mango_stock - slack_tolerance,
            mango_per_A * model.x1 + mango_per_B * model.x2,
            mango_stock + slack_tolerance,
        )
    )
    model.pineapple_usage = pyo.Constraint(
        expr=(
            pineapple_stock - slack_tolerance,
            pineapple_per_A * model.x1 + pineapple_per_B * model.x2,
            pineapple_stock + slack_tolerance,
        )
    )
    model.strawberry_usage = pyo.Constraint(
        expr=(
            strawberry_stock - slack_tolerance,
            strawberry_per_A * model.x1 + strawberry_per_B * model.x2,
            strawberry_stock + slack_tolerance,
        )
    )

    model.total_profit = pyo.Objective(
        expr=profit_A * model.x1 + profit_B * model.x2,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}