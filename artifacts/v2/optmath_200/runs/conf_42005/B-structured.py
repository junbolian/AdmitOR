# IR: {"sets":{"C":"range(num_cities)","A":"[(i,j) for i in C for j in C if i != j], ordered lexicographically"},"params":{"num_cities":"params['num_cities']","net_supply":"params['net_supply'][i] for i in C","cost":"params['cost'][k] for the kth arc in A","capacity":"params['capacity'][k] for the kth arc in A"},"variables":{"shipment[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["For each i in C: sum(shipment[i,j] for j != i) - sum(shipment[j,i] for j != i) = net_supply[i]","For each (i,j) in A: shipment[i,j] <= capacity[i,j]"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    net_supply = params["net_supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    cities = list(range(num_cities))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_supply = pyo.Param(
        model.cities,
        initialize={i: net_supply[i] for i in cities},
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={arc: cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(block, i):
        outgoing = pyo.quicksum(
            block.shipment[i, j] for j in block.cities if j != i
        )
        incoming = pyo.quicksum(
            block.shipment[j, i] for j in block.cities if j != i
        )
        return outgoing - incoming == block.net_supply[i]

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(block, i, j):
        return block.shipment[i, j] <= block.route_capacity[i, j]

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.route_cost[i, j] * model.shipment[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}