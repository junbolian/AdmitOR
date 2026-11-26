import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    shirts_available = params["shirts_available"]
    pants_available = params["pants_available"]
    shirts_per_A = params["shirts_per_A"]
    pants_per_A = params["pants_per_A"]
    price_A = params["price_A"]
    shirts_per_B = params["shirts_per_B"]
    pants_per_B = params["pants_per_B"]
    price_B = params["price_B"]
    min_A = params["min_A"]
    min_B = params["min_B"]

    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.shirts_con = pyo.Constraint(
        expr=shirts_per_A * model.xA + shirts_per_B * model.xB <= shirts_available
    )
    model.pants_con = pyo.Constraint(
        expr=pants_per_A * model.xA + pants_per_B * model.xB <= pants_available
    )
    model.min_A_con = pyo.Constraint(expr=model.xA >= min_A)
    model.min_B_con = pyo.Constraint(expr=model.xB >= min_B)

    model.revenue = pyo.Objective(
        expr=price_A * model.xA + price_B * model.xB, sense=pyo.maximize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.revenue))
    return {"objective": obj_val, "status": "optimal"}