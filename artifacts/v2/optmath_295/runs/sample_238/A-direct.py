import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    nutrient_min = params["nutrient_min"]
    nutrient_max = params["nutrient_max"]
    nutrient_coeff = params["nutrient_coeff"]

    num_foods = len(cost)
    num_nutrients = len(nutrient_min)

    foods = list(range(num_foods))
    nutrients = list(range(num_nutrients))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(foods, initialize=0.0, bounds=(0, None))

    model.obj = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in foods),
        sense=pyo.minimize,
    )

    def nutrient_rule(m, n):
        return sum(nutrient_coeff[n][i] * m.x[i] for i in foods)

    model.nutrient_expr = pyo.Expression(nutrients, rule=nutrient_rule)

    model.nut_min = pyo.Constraint(
        nutrients, rule=lambda m, n: m.nutrient_expr[n] >= nutrient_min[n]
    )
    model.nut_max = pyo.Constraint(
        nutrients, rule=lambda m, n: m.nutrient_expr[n] <= nutrient_max[n]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}