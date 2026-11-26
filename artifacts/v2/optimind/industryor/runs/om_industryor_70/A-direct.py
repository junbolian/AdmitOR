import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    income = params["income"]
    cost = params["cost"]
    budget = params["budget"]

    n = len(income)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(n), domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(income[i] * model.x[i] for i in range(n)),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(cost[i] * model.x[i] for i in range(n)) <= budget
    )

    # If Property 4 is purchased, Property 3 cannot be purchased.
    model.conflict_con = pyo.Constraint(
        expr=model.x[3] + model.x[2] <= 1
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}