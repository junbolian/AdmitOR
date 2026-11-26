import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    items = ["A", "B", "C", "D"]

    income = {
        "A": params["income_A"],
        "B": params["income_B"],
        "C": params["income_C"],
        "D": params["income_D"],
    }
    cost = {
        "A": params["cost_A"],
        "B": params["cost_B"],
        "C": params["cost_C"],
        "D": params["cost_D"],
    }
    budget = params["budget"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(cost[i] * model.x[i] for i in items) <= budget
    )

    model.conflict_constraint = pyo.Constraint(
        expr=model.x["D"] + model.x["A"] <= 1
    )

    model.obj = pyo.Objective(
        expr=sum(income[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}