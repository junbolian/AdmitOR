import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carbs_req = params["carbs_req"]
    calories_req = params["calories_req"]

    foods = list(range(len(cost)))

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.foods, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i] * m.x[i] for i in m.foods)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in model.foods) >= protein_req
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(carbs[i] * model.x[i] for i in model.foods) >= carbs_req
    )
    model.calories_con = pyo.Constraint(
        expr=sum(calories[i] * model.x[i] for i in model.foods) >= calories_req
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}