import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    num_warehouses = len(warehouse_supply)
    num_stores = len(store_demand)

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, num_warehouses - 1)
    model.S = pyo.RangeSet(0, num_stores - 1)

    def x_bounds(m, w, s):
        return (0, route_capacity[w][s])

    model.x = pyo.Var(model.W, model.S, bounds=x_bounds, domain=pyo.NonNegativeReals)

    def warehouse_rule(m, w):
        return sum(m.x[w, s] for s in m.S) <= warehouse_supply[w]

    def store_rule(m, s):
        return sum(m.x[w, s] for w in m.W) == store_demand[s]

    model.warehouse_limit = pyo.Constraint(model.W, rule=warehouse_rule)
    model.store_requirement = pyo.Constraint(model.S, rule=store_rule)

    def objective_rule(m):
        return sum(transport_cost[w][s] * m.x[w, s] for w in m.W for s in m.S)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}