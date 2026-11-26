import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["Food_1", "Food_2", "Food_3", "Food_4"]

    cost = params["cost"]
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]

    def cost_of(f, idx):
        try:
            return cost[f]
        except (KeyError, TypeError, IndexError):
            return cost[idx]

    def prot(f, idx):
        try:
            return protein_content[f]
        except (KeyError, TypeError, IndexError):
            return protein_content[idx]

    def carb(f, idx):
        try:
            return carb_content[f]
        except (KeyError, TypeError, IndexError):
            return carb_content[idx]

    def cal(f, idx):
        try:
            return calorie_content[f]
        except (KeyError, TypeError, IndexError):
            return calorie_content[idx]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.cost_obj = pyo.Objective(
        expr=sum(cost_of(f, i) * model.x[f] for i, f in enumerate(foods)),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(prot(f, i) * model.x[f] for i, f in enumerate(foods))
        >= params["protein_requirement"]
    )

    model.carb_con = pyo.Constraint(
        expr=sum(carb(f, i) * model.x[f] for i, f in enumerate(foods))
        >= params["carb_requirement"]
    )

    model.calorie_con = pyo.Constraint(
        expr=sum(cal(f, i) * model.x[f] for i, f in enumerate(foods))
        >= params["calorie_requirement"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}