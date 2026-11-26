import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_capacities = params["resource_capacities"]
    resource_budget = params["resource_budget"]
    production_limits = params["production_limits"]

    n = len(profit_margins)
    items = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, bounds=lambda m, i: (0, production_limits[i]))

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_capacities[i] * model.x[i] for i in items)
        <= resource_budget
    )

    model.profit = pyo.Objective(
        expr=sum(profit_margins[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}