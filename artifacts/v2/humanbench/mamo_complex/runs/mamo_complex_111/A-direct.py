def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    foods = ["chicken", "cheese", "rice", "beans"]

    protein = {f: params[f"protein_{f}"] for f in foods}
    carbs = {f: params[f"carbs_{f}"] for f in foods}
    calories = {f: params[f"calories_{f}"] for f in foods}
    price = {f: params[f"price_{f}"] for f in foods}

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)
    model.qty = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.cost = pyo.Objective(
        expr=sum(price[f] * model.qty[f] for f in foods),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.qty[f] for f in foods) >= params["protein_req"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[f] * model.qty[f] for f in foods) >= params["carbs_req"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[f] * model.qty[f] for f in foods) >= params["calories_req"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}