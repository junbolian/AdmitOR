import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    items = [0, 1, 2]
    values = {
        0: params["value_item0"],
        1: params["value_item1"],
        2: params["value_item2"],
    }
    weights = {
        0: params["weight_item0"],
        1: params["weight_item1"],
        2: params["weight_item2"],
    }
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.Items = pyo.Set(initialize=items)
    model.x = pyo.Var(model.Items, domain=pyo.Binary)

    model.value_expr = pyo.Expression(
        expr=sum(values[i] * model.x[i] for i in model.Items)
    )
    model.weight_con = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in model.Items) <= capacity
    )
    model.obj = pyo.Objective(expr=model.value_expr, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}