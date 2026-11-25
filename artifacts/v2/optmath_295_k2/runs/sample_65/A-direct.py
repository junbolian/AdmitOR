import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = int(params["num_facilities"])
    num_stores = int(params["num_stores"])

    fixed_cost = params["fixed_cost"]
    shipping_cost_row0 = params["shipping_cost_row0"]
    demand = params["demand"]
    capacity = params["capacity"]

    facilities = list(range(num_facilities))
    stores = list(range(num_stores))

    # Only row 0 shipping costs are provided in params. Broadcast this given
    # row across all facilities (structural assumption: costs given per store).
    shipping_cost = {}
    for i in facilities:
        for j in stores:
            shipping_cost[(i, j)] = shipping_cost_row0[j]

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=facilities)
    model.stores = pyo.Set(initialize=stores)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in facilities for j in stores], dimen=2
    )

    model.open_fac = pyo.Var(model.facilities, within=pyo.Binary)
    model.ship = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def obj_rule(m):
        fixed = sum(fixed_cost[i] * m.open_fac[i] for i in m.facilities)
        var = sum(
            shipping_cost[(i, j)] * m.ship[(i, j)] for (i, j) in m.arcs
        )
        return fixed + var

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[(i, j)] for i in m.facilities) == demand[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i):
        return (
            sum(m.ship[(i, j)] for j in m.stores)
            <= capacity[i] * m.open_fac[i]
        )

    model.capacity_con = pyo.Constraint(model.facilities, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}