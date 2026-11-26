# IR: {"sets":{"salads":["A","B"],"fruits":["mango","pineapple","strawberry"]},"params":["mango_per_A","pineapple_per_A","strawberry_per_A","profit_A","mango_per_B","pineapple_per_B","strawberry_per_B","profit_B","mango_stock","pineapple_stock","strawberry_stock","completeness_tolerance"],"variables":{"x[s]":"nonnegative integer, s in salads"},"constraints":["mango_stock-completeness_tolerance <= mango_per_A*x[A]+mango_per_B*x[B] <= mango_stock+completeness_tolerance","pineapple_stock-completeness_tolerance <= pineapple_per_A*x[A]+pineapple_per_B*x[B] <= pineapple_stock+completeness_tolerance","strawberry_stock-completeness_tolerance <= strawberry_per_A*x[A]+strawberry_per_B*x[B] <= strawberry_stock+completeness_tolerance"],"objective":"maximize profit_A*x[A]+profit_B*x[B]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fruit_usage = {
        ("mango", "A"): params["mango_per_A"],
        ("pineapple", "A"): params["pineapple_per_A"],
        ("strawberry", "A"): params["strawberry_per_A"],
        ("mango", "B"): params["mango_per_B"],
        ("pineapple", "B"): params["pineapple_per_B"],
        ("strawberry", "B"): params["strawberry_per_B"],
    }
    profits = {
        "A": params["profit_A"],
        "B": params["profit_B"],
    }
    stocks = {
        "mango": params["mango_stock"],
        "pineapple": params["pineapple_stock"],
        "strawberry": params["strawberry_stock"],
    }
    tolerance = params["completeness_tolerance"]

    model = pyo.ConcreteModel()
    model.salads = pyo.Set(initialize=["A", "B"], ordered=True)
    model.fruits = pyo.Set(
        initialize=["mango", "pineapple", "strawberry"], ordered=True
    )

    model.fruit_usage = pyo.Param(
        model.fruits, model.salads, initialize=fruit_usage
    )
    model.profit = pyo.Param(model.salads, initialize=profits)
    model.stock = pyo.Param(model.fruits, initialize=stocks)
    model.tolerance = pyo.Param(initialize=tolerance)

    model.x = pyo.Var(model.salads, domain=pyo.NonNegativeIntegers)

    def completeness_rule(instance, fruit):
        consumption = sum(
            instance.fruit_usage[fruit, salad] * instance.x[salad]
            for salad in instance.salads
        )
        return pyo.inequality(
            instance.stock[fruit] - instance.tolerance,
            consumption,
            instance.stock[fruit] + instance.tolerance,
        )

    model.completeness = pyo.Constraint(
        model.fruits, rule=completeness_rule
    )
    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[salad] * model.x[salad]
            for salad in model.salads
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when no feasible solution can be loaded.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}