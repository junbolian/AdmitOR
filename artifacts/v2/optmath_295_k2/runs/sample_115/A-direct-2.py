import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = 6
    model = pyo.ConcreteModel()
    model.warehouses = pyo.RangeSet(0, n - 1)
    model.stores = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.warehouses, model.stores, within=pyo.NonNegativeReals)

    model.supply_rule = pyo.Constraint(
        model.warehouses,
        rule=lambda m, i: sum(m.x[i, j] for j in m.stores) == supply[i],
    )
    model.demand_rule = pyo.Constraint(
        model.stores,
        rule=lambda m, j: sum(m.x[i, j] for i in m.warehouses) == demand[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.warehouses for j in model.stores),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}