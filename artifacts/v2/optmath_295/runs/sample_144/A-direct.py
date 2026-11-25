import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    num_warehouses = len(supply)
    num_stores = len(demand)

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, num_warehouses - 1)
    model.stores = pyo.RangeSet(0, num_stores - 1)

    model.x = pyo.Var(model.warehouses, model.stores, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            transport_cost[i][j] * m.x[i, j]
            for i in m.warehouses
            for j in m.stores
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.stores) == supply[i]

    model.supply_constraint = pyo.Constraint(model.warehouses, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.warehouses) == demand[j]

    model.demand_constraint = pyo.Constraint(model.stores, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}