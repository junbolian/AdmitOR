import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fertilizers = list(range(5))

    target = {
        "Ni": params["target_Ni"],
        "Ph": params["target_Ph"],
        "Po": params["target_Po"],
    }
    tol = {
        "Ni": params["tol_Ni"],
        "Ph": params["tol_Ph"],
        "Po": params["tol_Po"],
    }
    nutrient = {
        "Ni": params["nutrient_Ni"],
        "Ph": params["nutrient_Ph"],
        "Po": params["nutrient_Po"],
    }
    price = params["price"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(fertilizers, bounds=(0, None))

    # Total weight of the blend
    model.total = pyo.Expression(expr=sum(model.x[i] for i in fertilizers))

    def nutrient_rule(model, idx):
        return sum(nutrient[idx][i] * model.x[i] for i in fertilizers)

    model.nut = pyo.Expression(["Ni", "Ph", "Po"], rule=nutrient_rule)

    # Constraints: target <= nutrient percent <= target + tol, expressed in weight terms
    def lower_rule(model, idx):
        return model.nut[idx] >= target[idx] * model.total

    def upper_rule(model, idx):
        return model.nut[idx] <= (target[idx] + tol[idx]) * model.total

    model.lower_con = pyo.Constraint(["Ni", "Ph", "Po"], rule=lower_rule)
    model.upper_con = pyo.Constraint(["Ni", "Ph", "Po"], rule=upper_rule)

    model.obj = pyo.Objective(
        expr=sum(price[i] * model.x[i] for i in fertilizers)
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}