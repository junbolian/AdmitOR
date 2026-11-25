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

    model.warehouses = pyo.RangeSet(0, num_warehouses - 1)
    model.stores = pyo.RangeSet(0, num_stores - 1)

    model.ship = pyo.Var(model.warehouses, model.stores, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, w):
        return sum(mdl.ship[w, s] for s in mdl.stores) <= warehouse_supply[w]
    model.supply_con = pyo.Constraint(model.warehouses, rule=supply_rule)

    def demand_rule(mdl, s):
        return sum(mdl.ship[w, s] for w in mdl.warehouses) == store_demand[s]
    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def cap_rule(mdl, w, s):
        return mdl.ship[w, s] <= route_capacity[w][s]
    model.cap_con = pyo.Constraint(model.warehouses, model.stores, rule=cap_rule)

    def obj_rule(mdl):
        return sum(transport_cost[w][s] * mdl.ship[w, s]
                   for w in mdl.warehouses for s in mdl.stores)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}