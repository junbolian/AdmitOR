import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    resource_capacity = params["resource_capacity"]
    upper_limit = params["upper_limit"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Expression(
        expr=sum(profit[i] * model.x[i] for i in items)
    )

    def resource_rule(m):
        return sum(resource_coeff[i] * m.x[i] for i in items) <= resource_capacity

    model.resource_con = pyo.Constraint(rule=resource_rule)

    def upper_rule(m, i):
        return m.x[i] <= upper_limit[i]

    model.upper_con = pyo.Constraint(items, rule=upper_rule)

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}