import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "veg", "bread", "almonds", "salmon"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, domain=pyo.NonNegativeIntegers)

    model.protein = pyo.Constraint(
        expr=sum(params["protein_" + f] * model.x[f] for f in foods)
        >= params["protein_target"]
    )
    model.carb = pyo.Constraint(
        expr=sum(params["carb_" + f] * model.x[f] for f in foods)
        >= params["carb_target"]
    )
    model.cal = pyo.Constraint(
        expr=sum(params["cal_" + f] * model.x[f] for f in foods)
        >= params["cal_target"]
    )

    model.cost = pyo.Objective(
        expr=sum(params["cost_" + f] * model.x[f] for f in foods),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}