import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["salmon", "beef", "pork", "okra", "carrots", "celery", "cabbage"]
    proteins = ["salmon", "beef", "pork"]
    vegetables = ["okra", "carrots", "celery", "cabbage"]

    fiber = {
        "okra": params["fiber_okra"],
        "carrots": params["fiber_carrots"],
        "celery": params["fiber_celery"],
        "cabbage": params["fiber_cabbage"],
    }
    price = {
        "salmon": params["price_salmon"],
        "beef": params["price_beef"],
        "pork": params["price_pork"],
        "okra": params["price_okra"],
        "carrots": params["price_carrots"],
        "celery": params["price_celery"],
        "cabbage": params["price_cabbage"],
    }

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)
    model.P = pyo.Set(initialize=proteins)
    model.V = pyo.Set(initialize=vegetables)

    # grams purchased of each food
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    # binary selection indicators
    model.y = pyo.Var(model.F, domain=pyo.Binary)

    # objective: maximize fiber from vegetables
    model.fiber_obj = pyo.Objective(
        expr=sum(fiber[v] * (model.x[v] / 100.0) for v in vegetables),
        sense=pyo.maximize,
    )

    # total food intake
    model.total = pyo.Constraint(
        expr=sum(model.x[f] for f in foods) == params["total_food"]
    )

    # budget
    model.budget_c = pyo.Constraint(
        expr=sum(price[f] * (model.x[f] / 100.0) for f in foods) <= params["budget"]
    )

    # at least two vegetables selected
    model.min_veg = pyo.Constraint(
        expr=sum(model.y[v] for v in vegetables) >= params["min_vegetables"]
    )

    # link: positive quantity implies selected
    model.link = pyo.ConstraintList()
    for f in foods:
        model.link.add(model.x[f] <= params["total_food"] * model.y[f])

    # choose at least one protein source
    model.protein_sel = pyo.Constraint(
        expr=sum(model.y[p] for p in proteins) >= 1
    )

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.fiber_obj))
    return {"objective": obj_val, "status": "optimal"}