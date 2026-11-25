import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    educational_value = params["educational_value"]
    cost = params["cost"]
    budget = params["budget"]

    n = len(educational_value)
    items = range(n)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(educational_value[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(cost[i] * model.x[i] for i in items) <= budget
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}