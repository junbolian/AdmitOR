# IR: {"sets":{"I":"0..5","J":"0..7"},"params":{"supply":"supply[I] from params","demand":"demand[J] from params","cost":"cost[I,J] from params","capacity":"capacity[I,J] from params"},"variables":{"shipment[I,J]":"NonNegativeReals"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for each i in I","sum(shipment[i,j] for i in I) == demand[j] for each j in J","shipment[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.I,
        initialize={i: supply[i] for i in model.I},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: demand[j] for j in model.J},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): cost[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): capacity[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )

    def supply_rule(network, i):
        return (
            sum(network.shipment[i, j] for j in network.J)
            == network.supply[i]
        )

    def demand_rule(network, j):
        return (
            sum(network.shipment[i, j] for i in network.I)
            == network.demand[j]
        )

    def capacity_rule(network, i, j):
        return network.shipment[i, j] <= network.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)
    model.route_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}