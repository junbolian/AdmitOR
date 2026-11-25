import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    costs = params["costs"]

    n_warehouses = len(supplies)
    n_stores = len(demands)

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, n_warehouses - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)

    model.x = pyo.Var(model.warehouses, model.stores, domain=pyo.NonNegativeReals)

    model.supply_con = pyo.Constraint(
        model.warehouses,
        rule=lambda m, i: sum(m.x[i, j] for j in m.stores) == supplies[i],
    )
    model.demand_con = pyo.Constraint(
        model.stores,
        rule=lambda m, j: sum(m.x[i, j] for i in m.warehouses) == demands[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(costs[i][j] * model.x[i, j]
                 for i in model.warehouses for j in model.stores),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}