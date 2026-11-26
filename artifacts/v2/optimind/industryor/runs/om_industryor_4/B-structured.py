# IR: {"sets":{"P":["salmon","beef","pork"],"V":["okra","carrots","celery","cabbage"],"F":"P union V"},"params":{"fiber[v]":"params['fiber_'+v], grams per 100 g","price[f]":"params['price_'+f], dollars per 100 g","budget":"params['budget']","total_intake":"params['total_intake']","min_protein_grams":"params['min_protein_grams']","min_vegetable_grams":"params['min_vegetable_grams']"},"variables":{"grams[f]":"NonNegativeReals","selected[f]":"Binary"},"constraints":["sum(selected[p] for p in P) == 1","sum(selected[v] for v in V) >= 2","grams[f] <= total_intake * selected[f] for f in F","grams[p] >= min_protein_grams * selected[p] for p in P","grams[v] >= min_vegetable_grams * selected[v] for v in V","sum(grams[f] for f in F) == total_intake","sum(price[f] * grams[f] / 100 for f in F) <= budget"],"objective":"maximize sum(fiber[v] * grams[v] / 100 for v in V)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.proteins = pyo.Set(
        initialize=["salmon", "beef", "pork"], ordered=True
    )
    model.vegetables = pyo.Set(
        initialize=["okra", "carrots", "celery", "cabbage"], ordered=True
    )
    model.foods = pyo.Set(
        initialize=[
            "salmon", "beef", "pork",
            "okra", "carrots", "celery", "cabbage",
        ],
        ordered=True,
    )

    model.fiber = pyo.Param(
        model.vegetables,
        initialize={
            vegetable: params["fiber_" + vegetable]
            for vegetable in model.vegetables
        },
        within=pyo.NonNegativeReals,
    )
    model.price = pyo.Param(
        model.foods,
        initialize={
            food: params["price_" + food]
            for food in model.foods
        },
        within=pyo.NonNegativeReals,
    )
    model.budget = pyo.Param(
        initialize=params["budget"], within=pyo.NonNegativeReals
    )
    model.total_intake = pyo.Param(
        initialize=params["total_intake"], within=pyo.NonNegativeReals
    )
    model.min_protein_grams = pyo.Param(
        initialize=params["min_protein_grams"],
        within=pyo.NonNegativeReals,
    )
    model.min_vegetable_grams = pyo.Param(
        initialize=params["min_vegetable_grams"],
        within=pyo.NonNegativeReals,
    )

    model.grams = pyo.Var(model.foods, domain=pyo.NonNegativeReals)
    model.selected = pyo.Var(model.foods, domain=pyo.Binary)

    model.one_protein = pyo.Constraint(
        expr=sum(model.selected[protein] for protein in model.proteins) == 1
    )
    model.at_least_two_vegetables = pyo.Constraint(
        expr=sum(
            model.selected[vegetable] for vegetable in model.vegetables
        ) >= 2
    )

    def selection_upper_rule(instance, food):
        return (
            instance.grams[food]
            <= instance.total_intake * instance.selected[food]
        )

    model.selection_upper = pyo.Constraint(
        model.foods, rule=selection_upper_rule
    )

    def protein_minimum_rule(instance, protein):
        return (
            instance.grams[protein]
            >= instance.min_protein_grams * instance.selected[protein]
        )

    model.protein_minimum = pyo.Constraint(
        model.proteins, rule=protein_minimum_rule
    )

    def vegetable_minimum_rule(instance, vegetable):
        return (
            instance.grams[vegetable]
            >= instance.min_vegetable_grams * instance.selected[vegetable]
        )

    model.vegetable_minimum = pyo.Constraint(
        model.vegetables, rule=vegetable_minimum_rule
    )
    model.required_intake = pyo.Constraint(
        expr=sum(model.grams[food] for food in model.foods)
        == model.total_intake
    )
    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.price[food] * model.grams[food] / 100
            for food in model.foods
        ) <= model.budget
    )
    model.fiber_objective = pyo.Objective(
        expr=sum(
            model.fiber[vegetable] * model.grams[vegetable] / 100
            for vegetable in model.vegetables
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.fiber_objective))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}