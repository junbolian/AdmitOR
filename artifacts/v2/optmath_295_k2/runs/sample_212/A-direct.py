import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margins = params["profit_margins"]
    resource_consumption = params["resource_consumption"]
    resource_budget = params["resource_budget"]
    production_capacities = params["production_capacities"]

    num_items = len(profit_margins)
    idx = range(num_items)

    model = pyo.ConcreteModel()
    model.item_idx = pyo.Set(initialize=idx)

    model.produce = pyo.Var(model.item_idx, domain=pyo.NonNegativeReals)

    model.profit = pyo.Objective(
        expr=sum(profit_margins[i] * model.produce[i] for i in model.item_idx),
        sense=pyo.maximize,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(resource_consumption[i] * model.produce[i] for i in model.item_idx)
        <= resource_budget
    )

    model.capacity = pyo.Constraint(
        model.item_idx,
        rule=lambda blk, i: blk.produce[i] <= production_capacities[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))

    return {"objective": obj_val, "status": "optimal"}