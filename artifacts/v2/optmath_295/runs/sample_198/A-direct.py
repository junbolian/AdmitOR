import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    consumption = params["consumption"]
    capacity = params["capacity"]
    upper_limit = params["upper_limit"]

    n = len(profit)
    idx = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=idx)
    model.x = pyo.Var(model.item_set, bounds=lambda model, i: (0, upper_limit[i]))

    model.profit_expr = pyo.Expression(
        expr=sum(profit[i] * model.x[i] for i in model.item_set)
    )

    def resource_rule(model):
        return sum(consumption[i] * model.x[i] for i in model.item_set) <= capacity

    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}