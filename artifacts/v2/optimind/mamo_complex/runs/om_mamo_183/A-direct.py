import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    target_N = params["target_N"]
    target_P = params["target_P"]
    target_K = params["target_K"]
    tol = params["tol"]
    price = params["price"]
    nutrient_N = params["nutrient_N"]
    nutrient_P = params["nutrient_P"]
    nutrient_K = params["nutrient_K"]

    fertilizers = list(range(1, 6))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(fertilizers, bounds=(0, None))

    # Total percentage composition (percentages are linear, x in 100-lb units)
    model.nitrogen = pyo.Constraint(
        expr=sum(nutrient_N[i - 1] * model.x[i] for i in fertilizers)
        >= target_N * sum(model.x[i] for i in fertilizers)
    )
    model.nitrogen_ub = pyo.Constraint(
        expr=sum(nutrient_N[i - 1] * model.x[i] for i in fertilizers)
        <= (target_N + tol) * sum(model.x[i] for i in fertilizers)
    )
    model.phosphorus = pyo.Constraint(
        expr=sum(nutrient_P[i - 1] * model.x[i] for i in fertilizers)
        >= target_P * sum(model.x[i] for i in fertilizers)
    )
    model.phosphorus_ub = pyo.Constraint(
        expr=sum(nutrient_P[i - 1] * model.x[i] for i in fertilizers)
        <= (target_P + tol) * sum(model.x[i] for i in fertilizers)
    )
    model.potash = pyo.Constraint(
        expr=sum(nutrient_K[i - 1] * model.x[i] for i in fertilizers)
        >= target_K * sum(model.x[i] for i in fertilizers)
    )
    model.potash_ub = pyo.Constraint(
        expr=sum(nutrient_K[i - 1] * model.x[i] for i in fertilizers)
        <= (target_K + tol) * sum(model.x[i] for i in fertilizers)
    )

    # Total mass constraint: produce exactly 100 pounds of mix
    model.total_mass = pyo.Constraint(
        expr=sum(model.x[i] for i in fertilizers) == 1
    )

    model.cost = pyo.Objective(
        expr=sum(price[i - 1] * model.x[i] for i in fertilizers),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}