import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_capacity = params["production_capacity"]

    n = len(profit)
    item_list = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_list)

    model.qty = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_consumption[i] * model.qty[i] for i in model.item_set)
        <= resource_capacity
    )

    model.capacity_constraint = pyo.Constraint(
        model.item_set,
        rule=lambda m, i: m.qty[i] <= production_capacity[i],
    )

    model.profit_expr = pyo.Objective(
        expr=sum(profit[i] * model.qty[i] for i in model.item_set),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_expr))
    return {"objective": obj_val, "status": "optimal"}