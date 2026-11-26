import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    restaurants = ["A", "B", "C", "D"]

    revenue = params["revenue"]
    cost = params["cost"]
    budget = params["budget"]

    model = pyo.ConcreteModel()

    model.R = pyo.Set(initialize=restaurants)

    model.x = pyo.Var(model.R, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(revenue[i] * model.x[r] for i, r in enumerate(restaurants)),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(cost[i] * model.x[r] for i, r in enumerate(restaurants))
        <= budget
    )

    model.D_not_A = pyo.Constraint(expr=model.x["D"] + model.x["A"] <= 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}