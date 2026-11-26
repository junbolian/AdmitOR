# IR: {"sets":{"P":["salmon","beef","pork"],"V":["okra","carrots","celery","cabbage"],"F":"P union V"},"params":["fiber_okra","fiber_carrots","fiber_celery","fiber_cabbage","price_salmon","price_beef","price_pork","price_okra","price_carrots","price_celery","price_cabbage","budget","total_food","min_vegetables"],"variables":{"grams[f in F]":"continuous nonnegative","selected[f in F]":"binary"},"constraints":["sum(grams[f] for f in F) = total_food","sum(price[f]*grams[f]/100 for f in F) <= budget","grams[f] <= total_food*selected[f] for f in F","sum(selected[f] for f in P) = 1","sum(selected[f] for f in V) >= min_vegetables"],"objective":"maximize sum(fiber[v]*grams[v]/100 for v in V)","selection_semantics":"Selection permits zero grams; no positive minimum serving size was supplied. Thus this models selection indicators, not a requirement that every selected food be purchased in a strictly positive quantity."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proteins = ("salmon", "beef", "pork")
    vegetables = ("okra", "carrots", "celery", "cabbage")
    foods = proteins + vegetables

    fiber_data = {
        "okra": params["fiber_okra"],
        "carrots": params["fiber_carrots"],
        "celery": params["fiber_celery"],
        "cabbage": params["fiber_cabbage"],
    }
    price_data = {
        "salmon": params["price_salmon"],
        "beef": params["price_beef"],
        "pork": params["price_pork"],
        "okra": params["price_okra"],
        "carrots": params["price_carrots"],
        "celery": params["price_celery"],
        "cabbage": params["price_cabbage"],
    }

    model = pyo.ConcreteModel()
    model.proteins = pyo.Set(initialize=proteins, ordered=True)
    model.vegetables = pyo.Set(initialize=vegetables, ordered=True)
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.fiber = pyo.Param(model.vegetables, initialize=fiber_data)
    model.price = pyo.Param(model.foods, initialize=price_data)
    model.budget = pyo.Param(initialize=params["budget"])
    model.total_food = pyo.Param(initialize=params["total_food"])
    model.min_vegetables = pyo.Param(initialize=params["min_vegetables"])

    model.grams = pyo.Var(model.foods, domain=pyo.NonNegativeReals)
    model.selected = pyo.Var(model.foods, domain=pyo.Binary)

    model.total_intake = pyo.Constraint(
        expr=sum(model.grams[food] for food in model.foods)
        == model.total_food
    )

    # Prices and fiber contents are specified per 100 grams.
    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.price[food] * model.grams[food] / 100
            for food in model.foods
        )
        <= model.budget
    )

    def selection_link_rule(instance, food):
        return (
            instance.grams[food]
            <= instance.total_food * instance.selected[food]
        )

    model.selection_link = pyo.Constraint(
        model.foods, rule=selection_link_rule
    )

    model.protein_selection = pyo.Constraint(
        expr=sum(model.selected[food] for food in model.proteins) == 1
    )

    model.vegetable_selection = pyo.Constraint(
        expr=sum(model.selected[food] for food in model.vegetables)
        >= model.min_vegetables
    )

    model.total_fiber = pyo.Objective(
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
        # Unexpected runtime errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_fiber))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}