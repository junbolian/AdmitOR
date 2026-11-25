# IR: {"sets":{"W":"0..6","D":"0..4"},"params":{"supply":"supply[W]","demand":"demand[D]","cost":"cost[W,D]","capacity":"capacity[W,D]"},"variables":{"shipment[W,D]":"continuous, nonnegative"},"constraints":["sum(shipment[i,j] for j in D) == supply[i] for i in W","sum(shipment[i,j] for i in W) == demand[j] for j in D","shipment[i,j] <= capacity[i,j] for i in W, j in D"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in W, j in D)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed supply/demand and row-indexed cost/capacity arrays."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.W = pyo.RangeSet(0, 6)
    model.D = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.W, initialize=lambda mdl, i: supply[i]
    )
    model.demand = pyo.Param(
        model.D, initialize=lambda mdl, j: demand[j]
    )
    model.cost = pyo.Param(
        model.W, model.D, initialize=lambda mdl, i, j: cost[i][j]
    )
    model.capacity = pyo.Param(
        model.W, model.D, initialize=lambda mdl, i, j: capacity[i][j]
    )

    model.shipment = pyo.Var(
        model.W, model.D, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, i):
        return sum(mdl.shipment[i, j] for j in mdl.D) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.W) == mdl.demand[j]

    def capacity_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.D, rule=demand_rule)
    model.route_capacity = pyo.Constraint(
        model.W, model.D, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.W
            for j in model.D
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}