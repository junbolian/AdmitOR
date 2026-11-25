import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    shipping_cost = params["shipping_cost"]
    route_capacity = params["route_capacity"]

    num_warehouses = 5
    num_stores = 6
    warehouses = list(range(num_warehouses))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses)
    model.S = pyo.Set(initialize=stores)
    model.WS = pyo.Set(initialize=warehouses, dimen=2) if False else None
    del model.WS

    routes = [(w, s) for w in warehouses for s in stores]

    model.x = pyo.Var(routes, domain=pyo.NonNegativeReals)

    model.supply_con = pyo.Constraint(
        warehouses,
        rule=lambda m, w: sum(m.x[w, s] for s in stores) == warehouse_supply[w],
    )
    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda m, s: sum(m.x[w, s] for w in warehouses) == store_demand[s],
    )
    model.cap_con = pyo.Constraint(
        routes,
        rule=lambda m, w, s: m.x[w, s] <= route_capacity[w][s],
    )

    model.obj = pyo.Objective(
        expr=sum(shipping_cost[w][s] * model.x[w, s] for (w, s) in routes),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}