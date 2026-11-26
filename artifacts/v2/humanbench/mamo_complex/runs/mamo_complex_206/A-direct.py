import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    grains = [1, 2, 3]
    nutrients = ['A', 'B', 'C', 'D']

    def nutr(g, n):
        return params[f"nutrient_{n}_grain{g}"]

    def cost(g):
        return params[f"cost_grain{g}"]

    def req(n):
        return params[f"req_nutrient_{n}"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(grains, within=pyo.NonNegativeReals)

    model.cost_expr = pyo.Objective(
        expr=sum(cost(g) * model.x[g] for g in grains),
        sense=pyo.minimize,
    )

    model.nutrient_cons = pyo.Constraint(
        nutrients,
        rule=lambda model_, n: sum(nutr(g, n) * model_.x[g] for g in grains) >= req(n),
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost_expr))
    except Exception:
        return {"objective": None, "status": "infeasible or solve failed"}

    if obj_val is None:
        return {"objective": None, "status": "no objective value"}

    return {"objective": obj_val, "status": "optimal"}