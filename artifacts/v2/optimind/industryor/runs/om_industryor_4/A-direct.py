import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fiber_okra = params["fiber_okra"]
    fiber_carrots = params["fiber_carrots"]
    fiber_celery = params["fiber_celery"]
    fiber_cabbage = params["fiber_cabbage"]
    price_salmon = params["price_salmon"]
    price_beef = params["price_beef"]
    price_pork = params["price_pork"]
    price_okra = params["price_okra"]
    price_carrots = params["price_carrots"]
    price_celery = params["price_celery"]
    price_cabbage = params["price_cabbage"]
    budget = params["budget"]
    total_intake = params["total_intake"]
    min_protein_grams = params["min_protein_grams"]
    min_vegetable_grams = params["min_vegetable_grams"]

    proteins = ["salmon", "beef", "pork"]
    veggies = ["okra", "carrots", "celery", "cabbage"]

    fiber = {
        "okra": fiber_okra,
        "carrots": fiber_carrots,
        "celery": fiber_celery,
        "cabbage": fiber_cabbage,
    }
    price = {
        "salmon": price_salmon,
        "beef": price_beef,
        "pork": price_pork,
        "okra": price_okra,
        "carrots": price_carrots,
        "celery": price_celery,
        "cabbage": price_cabbage,
    }

    model = pyo.ConcreteModel()

    model.AMT = pyo.Var(proteins + veggies, domain=pyo.NonNegativeReals)
    model.yP = pyo.Var(proteins, domain=pyo.Binary)
    model.yV = pyo.Var(veggies, domain=pyo.Binary)

    model.fiber_obj = pyo.Objective(
        expr=sum(fiber[k] * model.AMT[k] for k in veggies) / 100.0,
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(price[k] * model.AMT[k] for k in proteins + veggies) / 100.0
        <= budget
    )
    model.intake_con = pyo.Constraint(
        expr=sum(model.AMT[k] for k in proteins + veggies) == total_intake
    )
    model.one_protein = pyo.Constraint(
        expr=sum(model.yP[p] for p in proteins) == 1
    )
    model.protein_link = pyo.Constraint(
        proteins,
        rule=lambda m, p: m.AMT[p] >= min_protein_grams * m.yP[p],
    )
    model.protein_link_ub = pyo.Constraint(
        proteins,
        rule=lambda m, p: m.AMT[p] <= total_intake * m.yP[p],
    )
    model.min_veg = pyo.Constraint(
        veggies,
        rule=lambda m, v: m.AMT[v] >= min_vegetable_grams * m.yV[v],
    )
    model.veg_ub = pyo.Constraint(
        veggies,
        rule=lambda m, v: m.AMT[v] <= total_intake * m.yV[v],
    )
    model.min_two_veg = pyo.Constraint(
        expr=sum(model.yV[v] for v in veggies) >= 2
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.fiber_obj))
    return {"objective": obj_val, "status": "optimal"}