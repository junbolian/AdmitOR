# IR: {"sets":{"R":["A","B","C","D"]},"params":{"revenue":"params['revenue']: mapping keyed by R or sequence in R order; dollars/year","cost":"params['cost']: mapping keyed by R or sequence in R order; millions of dollars","budget":"params['budget']; millions of dollars"},"variables":{"buy[r]":"Binary for r in R"},"constraints":["sum(cost[r]*buy[r] for r in R) <= budget","buy['D'] + buy['A'] <= 1"],"objective":"maximize sum(revenue[r]*buy[r] for r in R)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    restaurants = ("A", "B", "C", "D")

    def restaurant_values(values):
        if isinstance(values, Mapping) and all(
            restaurant in values for restaurant in restaurants
        ):
            return {
                restaurant: values[restaurant]
                for restaurant in restaurants
            }
        return {
            restaurant: values[position]
            for position, restaurant in enumerate(restaurants)
        }

    revenue = restaurant_values(params["revenue"])
    cost = restaurant_values(params["cost"])
    budget = params["budget"]

    model = pyo.ConcreteModel()
    model.restaurants = pyo.Set(initialize=restaurants, ordered=True)

    model.annual_revenue = pyo.Param(
        model.restaurants,
        initialize=revenue,
        within=pyo.Reals,
    )
    model.purchase_cost = pyo.Param(
        model.restaurants,
        initialize=cost,
        within=pyo.Reals,
    )
    model.investment_budget = pyo.Param(
        initialize=budget,
        within=pyo.Reals,
    )

    model.buy = pyo.Var(model.restaurants, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.purchase_cost[restaurant] * model.buy[restaurant]
            for restaurant in model.restaurants
        ) <= model.investment_budget
    )

    model.restaurant_exclusion = pyo.Constraint(
        expr=model.buy["D"] + model.buy["A"] <= 1
    )

    model.total_annual_income = pyo.Objective(
        expr=sum(
            model.annual_revenue[restaurant] * model.buy[restaurant]
            for restaurant in model.restaurants
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_annual_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}