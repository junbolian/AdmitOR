import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n = len(profit)
    item_ids = list(range(n))

    model = pyo.ConcreteModel()

    model.item_set = pyo.Set(initialize=item_ids, ordered=True)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_rate[i] * model.x[i] for i in model.item_set)
        <= resource_capacity
    )

    def limit_rule(m, i):
        return m.x[i] <= production_limit[i]

    model.limit_constraint = pyo.Constraint(model.item_set, rule=limit_rule)

    model.total_profit = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in model.item_set),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}