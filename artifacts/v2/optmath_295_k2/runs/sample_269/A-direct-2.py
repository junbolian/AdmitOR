import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    total_resource = params["total_resource"]
    capacity = params["capacity"]

    n = len(profit)
    idx = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=idx, ordered=True)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, capacity[i]))

    model.total_profit = pyo.Objective(
        rule=lambda m: sum(profit[i] * m.x[i] for i in m.item_set),
        sense=pyo.maximize,
    )

    model.resource_limit = pyo.Constraint(
        rule=lambda m: sum(resource_consumption[i] * m.x[i] for i in m.item_set)
        <= total_resource
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}