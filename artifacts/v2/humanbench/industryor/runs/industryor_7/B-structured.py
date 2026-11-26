# IR: {"sets":{"restaurants":["A","B","C","D"]},"params":["income_A","income_B","income_C","income_D","cost_A","cost_B","cost_C","cost_D","budget"],"variables":{"purchase[r]":"Binary for r in restaurants"},"constraints":["sum(cost[r]*purchase[r] for r in restaurants) <= budget","purchase[D] + purchase[A] <= 1"],"objective":"maximize sum(income[r]*purchase[r] for r in restaurants)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.restaurants = pyo.Set(initialize=["A", "B", "C", "D"])

    model.income = pyo.Param(
        model.restaurants,
        initialize={
            "A": params["income_A"],
            "B": params["income_B"],
            "C": params["income_C"],
            "D": params["income_D"],
        },
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.restaurants,
        initialize={
            "A": params["cost_A"],
            "B": params["cost_B"],
            "C": params["cost_C"],
            "D": params["cost_D"],
        },
        within=pyo.Reals,
    )
    model.budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.Reals,
    )

    model.purchase = pyo.Var(model.restaurants, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.cost[restaurant] * model.purchase[restaurant]
            for restaurant in model.restaurants
        )
        <= model.budget
    )
    model.purchase_exclusion = pyo.Constraint(
        expr=model.purchase["D"] + model.purchase["A"] <= 1
    )

    model.total_income = pyo.Objective(
        expr=sum(
            model.income[restaurant] * model.purchase[restaurant]
            for restaurant in model.restaurants
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}